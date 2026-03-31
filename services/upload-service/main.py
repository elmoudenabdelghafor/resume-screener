"""
upload-service  –  FastAPI
Accepts PDF / DOCX uploads, stores to MinIO, and enqueues a parse job in Redis.
"""
import uuid
import logging
import os
from functools import lru_cache

import boto3
import psycopg2
from botocore.client import Config
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel
from pydantic_settings import BaseSettings
import redis as redis_lib
from rq import Queue

# ── Settings ────────────────────────────────────────────────────────────────

class Settings(BaseSettings):
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "resumes"
    minio_secure: bool = False

    redis_host: str = "redis"
    redis_port: int = 6379

    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "resume_screener"
    postgres_user: str = "screener"
    postgres_password: str = "changeme"

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()


# ── Application ──────────────────────────────────────────────────────────────

app = FastAPI(title="Upload Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

Instrumentator().instrument(app).expose(app)

logger = logging.getLogger("upload-service")
logging.basicConfig(level=logging.INFO)

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


# ── Dependencies ─────────────────────────────────────────────────────────────

def get_s3_client(settings: Settings):
    return boto3.client(
        "s3",
        endpoint_url=f"{'https' if settings.minio_secure else 'http'}://{settings.minio_endpoint}",
        aws_access_key_id=settings.minio_access_key,
        aws_secret_access_key=settings.minio_secret_key,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )


def get_rq_queue(settings: Settings) -> Queue:
    conn = redis_lib.Redis(host=settings.redis_host, port=settings.redis_port)
    return Queue("parse_queue", connection=conn)


# ── Response schemas ─────────────────────────────────────────────────────────

class UploadResponse(BaseModel):
    job_id: str
    filename: str
    storage_key: str
    message: str


# ── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/healthz", tags=["ops"])
def health():
    return {"status": "ok"}


@app.get("/jobs/{job_id}", tags=["status"])
def get_job_status(job_id: str):
    """Return current processing status of a job from the database."""
    settings = get_settings()
    try:
        conn = psycopg2.connect(
            host=settings.postgres_host,
            port=settings.postgres_port,
            dbname=settings.postgres_db,
            user=settings.postgres_user,
            password=settings.postgres_password,
        )
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, status, created_at, updated_at FROM jobs WHERE id = %s",
                    (job_id,),
                )
                row = cur.fetchone()
        finally:
            conn.close()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {exc}") from exc

    if not row:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    return {
        "job_id": str(row[0]),
        "status": row[1],
        "created_at": row[2].isoformat(),
        "updated_at": row[3].isoformat(),
    }


@app.post("/upload", response_model=UploadResponse, tags=["upload"])
async def upload_resume(
    file: UploadFile = File(...),
    job_description: str = Form(...),
):
    """
    Upload a PDF or DOCX resume and a job description.
    The file is stored in MinIO and a parsing job is enqueued.
    """
    settings = get_settings()

    # ── Validate file type ───────────────────────────────────────────────────
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported file type '{file.content_type}'. Only PDF and DOCX are accepted.",
        )

    job_id = str(uuid.uuid4())
    ext = "pdf" if file.content_type == "application/pdf" else "docx"
    storage_key = f"{job_id}/{file.filename or f'resume.{ext}'}"

    # ── Upload to MinIO ──────────────────────────────────────────────────────
    try:
        s3 = get_s3_client(settings)
        file_bytes = await file.read()
        s3.put_object(
            Bucket=settings.minio_bucket,
            Key=storage_key,
            Body=file_bytes,
            ContentType=file.content_type,
        )
        logger.info("Stored %s → s3://%s/%s", file.filename, settings.minio_bucket, storage_key)
    except Exception as exc:
        logger.exception("MinIO upload failed")
        raise HTTPException(status_code=502, detail=f"Object storage error: {exc}") from exc

    # ── Enqueue parse job ────────────────────────────────────────────────────
    try:
        q = get_rq_queue(settings)
        q.enqueue(
            "worker.parse_resume",   # resolved inside parser-service
            kwargs={
                "job_id": job_id,
                "storage_key": storage_key,
                "filename": file.filename,
                "job_description": job_description,
            },
            job_id=job_id,           # RQ job id = our app job id for traceability
        )
        logger.info("Enqueued parse job %s", job_id)
    except Exception as exc:
        logger.exception("Redis enqueue failed")
        raise HTTPException(status_code=502, detail=f"Queue error: {exc}") from exc

    return UploadResponse(
        job_id=job_id,
        filename=file.filename or f"resume.{ext}",
        storage_key=storage_key,
        message="Resume uploaded and queued for parsing.",
    )
# test actions
# test push race condition loop
