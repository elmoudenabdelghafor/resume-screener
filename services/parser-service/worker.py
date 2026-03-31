"""
parser-service  –  FastAPI (status endpoint) + RQ worker
Downloads files from MinIO, extracts plain text (PDF via PyMuPDF, DOCX via python-docx),
structures sections, persists to PostgreSQL, and enqueues a screening job.
"""
import io
import json
import logging
import os
import re

# Heavy deps are imported lazily inside their respective functions
# so this module can be loaded in tests without C-extensions installed.

logger = logging.getLogger("parser-worker")
logging.basicConfig(level=logging.INFO)

# ── Environment helpers ──────────────────────────────────────────────────────

def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


def get_s3_client():
    import boto3
    from botocore.client import Config
    endpoint = _env("MINIO_ENDPOINT", "minio:9000")
    secure = _env("MINIO_SECURE", "false").lower() == "true"
    return boto3.client(
        "s3",
        endpoint_url=f"{'https' if secure else 'http'}://{endpoint}",
        aws_access_key_id=_env("MINIO_ACCESS_KEY", "minioadmin"),
        aws_secret_access_key=_env("MINIO_SECRET_KEY", "minioadmin"),
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )


def get_db_conn():
    import psycopg2
    return psycopg2.connect(
        host=_env("POSTGRES_HOST", "postgres"),
        port=int(_env("POSTGRES_PORT", "5432")),
        dbname=_env("POSTGRES_DB", "resume_screener"),
        user=_env("POSTGRES_USER", "screener"),
        password=_env("POSTGRES_PASSWORD", "changeme"),
    )


def get_redis_conn():
    import redis as redis_lib
    return redis_lib.Redis(
        host=_env("REDIS_HOST", "redis"),
        port=int(_env("REDIS_PORT", "6379")),
    )


# ── Text extraction ──────────────────────────────────────────────────────────

def extract_text_pdf(data: bytes) -> str:
    """Extract plain text from PDF bytes using PyMuPDF."""
    import fitz  # lazy import — keeps worker.py loadable without PyMuPDF installed
    text_parts = []
    with fitz.open(stream=data, filetype="pdf") as doc:
        for page in doc:
            text_parts.append(page.get_text())
    return "\n".join(text_parts)


def extract_text_docx(data: bytes) -> str:
    """Extract plain text from DOCX bytes using python-docx."""
    from docx import Document
    doc = Document(io.BytesIO(data))
    return "\n".join(para.text for para in doc.paragraphs)


# ── Section structuring ──────────────────────────────────────────────────────

_SECTION_HEADERS = {
    "education": re.compile(r"\b(education|academic|qualification)\b", re.I),
    "experience": re.compile(r"\b(experience|employment|work history|career)\b", re.I),
    "skills": re.compile(r"\b(skills|technologies|tech stack|competencies|tools)\b", re.I),
    "summary": re.compile(r"\b(summary|objective|profile|about)\b", re.I),
    "projects": re.compile(r"\b(projects|portfolio|open.?source)\b", re.I),
    "certifications": re.compile(r"\b(certifications?|licenses?|courses?)\b", re.I),
}


def structure_sections(text: str) -> dict:
    """
    Naively split raw resume text into labelled sections by detecting
    common section header keywords. Falls back to 'other' for unmatched content.
    """
    sections: dict[str, list[str]] = {k: [] for k in _SECTION_HEADERS}
    sections["other"] = []
    current = "other"
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        matched = False
        for section, pattern in _SECTION_HEADERS.items():
            if pattern.search(stripped) and len(stripped) < 60:
                current = section
                matched = True
                break
        if not matched:
            sections[current].append(stripped)
    # Collapse each section's lines into a single string
    return {k: "\n".join(v) for k, v in sections.items() if v}


# ── RQ job ───────────────────────────────────────────────────────────────────

def parse_resume(
    job_id: str,
    storage_key: str,
    filename: str,
    job_description: str,
) -> None:
    """
    Main RQ worker function.
    1. Download file from MinIO
    2. Extract text
    3. Structure sections
    4. Insert job + resume records into PostgreSQL
    5. Enqueue ai-screener job
    """
    logger.info("[%s] Starting parse for %s", job_id, filename)

    # ── Download from MinIO ──────────────────────────────────────────────────
    bucket = _env("MINIO_BUCKET", "resumes")
    s3 = get_s3_client()
    response = s3.get_object(Bucket=bucket, Key=storage_key)
    file_bytes = response["Body"].read()

    # ── Extract text ─────────────────────────────────────────────────────────
    if filename.lower().endswith(".pdf"):
        raw_text = extract_text_pdf(file_bytes)
    else:
        raw_text = extract_text_docx(file_bytes)

    sections = structure_sections(raw_text)
    logger.info("[%s] Extracted %d chars, %d sections", job_id, len(raw_text), len(sections))

    # ── Persist to PostgreSQL ─────────────────────────────────────────────────
    conn = get_db_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                # Upsert job record
                cur.execute(
                    """
                    INSERT INTO jobs (id, status, job_description)
                    VALUES (%s, 'parsing', %s)
                    ON CONFLICT (id) DO UPDATE SET status = 'parsing', updated_at = NOW()
                    """,
                    (job_id, job_description),
                )
                # Insert resume record and get its id
                cur.execute(
                    """
                    INSERT INTO resumes (job_id, filename, storage_key, raw_text, sections)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (job_id, filename, storage_key, raw_text, json.dumps(sections)),
                )
                resume_id = cur.fetchone()[0]

                # Update job status
                cur.execute(
                    "UPDATE jobs SET status = 'screening', updated_at = NOW() WHERE id = %s",
                    (job_id,),
                )
    finally:
        conn.close()

    logger.info("[%s] Persisted resume_id=%s", job_id, resume_id)

    # ── Enqueue screener job ──────────────────────────────────────────────────
    redis_conn = get_redis_conn()
    from rq import Queue
    screen_queue = Queue("screen_queue", connection=redis_conn)
    screen_queue.enqueue(
        "main.screen_resume",   # resolved inside ai-screener-service
        kwargs={
            "job_id": job_id,
            "resume_id": str(resume_id),
            "raw_text": raw_text,
            "job_description": job_description,
        },
        job_id=job_id,          # RQ job id = app job id for traceability
    )
    logger.info("[%s] Enqueued screen job for resume_id=%s", job_id, resume_id)
