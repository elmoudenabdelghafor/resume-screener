"""
ai-screener-service  –  FastAPI + RQ consumer
Scores a resume against a job description via Groq (Llama 3 70B),
extracts named entities via HuggingFace NER, and persists results to PostgreSQL.
"""
import json
import logging
import os
import time

import httpx
import psycopg2
import redis as redis_lib
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from huggingface_hub import InferenceClient
from prometheus_fastapi_instrumentator import Instrumentator
from rq import Queue

from schemas import NEREntities, ScreeningResult, ScoreBreakdown, ScreenRequest

logger = logging.getLogger("ai-screener")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="AI Screener Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

Instrumentator().instrument(app).expose(app)


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


def get_db_conn():
    return psycopg2.connect(
        host=_env("POSTGRES_HOST", "postgres"),
        port=int(_env("POSTGRES_PORT", "5432")),
        dbname=_env("POSTGRES_DB", "resume_screener"),
        user=_env("POSTGRES_USER", "screener"),
        password=_env("POSTGRES_PASSWORD", "changeme"),
    )


# ── Groq scoring ─────────────────────────────────────────────────────────────

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = (
    "You are an expert technical recruiter. "
    "When given a resume and a job description you respond ONLY with a JSON object "
    "containing exactly these keys: skills, experience, education, overall (each a number 0-100) "
    "and summary (one sentence). No markdown, no explanation, just the JSON."
)


def _sanitize(text: str, max_chars: int = 6000) -> str:
    """Remove null bytes and non-printable control chars that cause Groq 400s."""
    cleaned = text.replace("\x00", "").replace("\r", "\n")
    # Keep tab and newline; strip other ASCII control chars
    cleaned = "".join(ch for ch in cleaned if ch == "\n" or ch == "\t" or ord(ch) >= 32)
    return cleaned[:max_chars]


def score_with_groq(resume_text: str, job_description: str) -> tuple[dict, str]:
    """Call Groq API and parse the structured score JSON."""
    api_key = _env("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY environment variable not set")

    user_content = (
        f"=== JOB DESCRIPTION ===\n{_sanitize(job_description, 1000)}\n\n"
        f"=== RESUME ===\n{_sanitize(resume_text, 5000)}"
    )

    t0 = time.monotonic()
    with httpx.Client(timeout=60) as client:
        resp = client.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                "temperature": 0.1,
            },
        )
    latency = time.monotonic() - t0
    logger.info("Groq responded in %.2fs  status=%s", latency, resp.status_code)

    if not resp.is_success:
        logger.error("Groq error body: %s", resp.text)
        resp.raise_for_status()

    content = resp.json()["choices"][0]["message"]["content"]
    # Strip potential markdown code fences
    content = content.strip()
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
    content = content.strip()

    try:
        return json.loads(content), content
    except json.JSONDecodeError:
        logger.error("Failed to parse Groq JSON: %s", content)
        # Return safe defaults rather than crashing the job
        return {"skills": 0, "experience": 0, "education": 0, "overall": 0, "summary": "Parse error"}, content


# ── HuggingFace NER ──────────────────────────────────────────────────────────

NER_MODEL = "dslim/bert-base-NER"

# Map HF NER entity group labels → our schema fields
_NER_LABEL_MAP = {
    "ORG": "companies",
    "LOC": "locations",
    "PER": "misc",      # treat person names as misc
    "MISC": "misc",
}

# Degree keywords for simple heuristic extraction from MISC
_DEGREE_KEYWORDS = {"bachelor", "master", "phd", "msc", "bsc", "mba", "b.s", "m.s", "b.e", "m.e"}


def extract_entities_ner(text: str) -> NEREntities:
    """Run HuggingFace NER and bucket entities into our schema."""
    hf_token = _env("HF_API_TOKEN")
    client = InferenceClient(token=hf_token or None)

    try:
        results = client.token_classification(text[:2000], model=NER_MODEL)
    except Exception as exc:
        logger.warning("HF NER failed, returning empty entities: %s", exc)
        return NEREntities()

    entities: dict[str, set] = {k: set() for k in ["companies", "degrees", "tools", "locations", "misc"]}
    for item in results:
        label = item.get("entity_group", item.get("entity", "")).upper()
        word = item.get("word", "").replace("##", "").strip()
        if not word:
            continue
        # Degrees heuristic
        if any(kw in word.lower() for kw in _DEGREE_KEYWORDS):
            entities["degrees"].add(word)
        else:
            bucket = _NER_LABEL_MAP.get(label, "misc")
            entities[bucket].add(word)

    return NEREntities(
        companies=list(entities["companies"]),
        degrees=list(entities["degrees"]),
        tools=list(entities["tools"]),
        locations=list(entities["locations"]),
        misc=list(entities["misc"]),
    )


# ── Core screening function (called by RQ and HTTP) ──────────────────────────

def screen_resume(
    job_id: str,
    resume_id: str,
    raw_text: str,
    job_description: str,
) -> ScreeningResult:
    """Score resume + extract entities + persist to PostgreSQL."""
    logger.info("[%s] Screening resume_id=%s", job_id, resume_id)

    # Groq scoring
    score_dict, raw_llm = score_with_groq(raw_text, job_description)
    breakdown = ScoreBreakdown(
        skills=float(score_dict.get("skills", 0)),
        experience=float(score_dict.get("experience", 0)),
        education=float(score_dict.get("education", 0)),
        overall=float(score_dict.get("overall", 0)),
    )

    # HuggingFace NER
    entities = extract_entities_ner(raw_text)

    result = ScreeningResult(
        resume_id=resume_id,
        job_id=job_id,
        overall_score=breakdown.overall,
        breakdown=breakdown,
        entities=entities,
        summary=score_dict.get("summary", ""),
        raw_llm_response=raw_llm,
    )

    # Persist to PostgreSQL
    conn = get_db_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO scores (resume_id, overall_score, breakdown, entities, summary)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (
                        resume_id,
                        result.overall_score,
                        json.dumps(breakdown.model_dump()),
                        json.dumps(entities.model_dump()),
                        result.summary,
                    ),
                )
                cur.execute(
                    "UPDATE jobs SET status = 'done', updated_at = NOW() WHERE id = %s",
                    (job_id,),
                )
    finally:
        conn.close()

    logger.info("[%s] Screening complete → overall=%.1f", job_id, result.overall_score)
    return result


# ── HTTP endpoints ────────────────────────────────────────────────────────────

@app.get("/healthz", tags=["ops"])
def health():
    return {"status": "ok"}


@app.post("/screen", response_model=ScreeningResult, tags=["screen"])
def screen_endpoint(req: ScreenRequest):
    """
    Synchronous screening endpoint for ad-hoc calls
    (the normal flow uses the RQ worker path via parser-service).
    """
    try:
        return screen_resume(
            job_id=req.job_id,
            resume_id=req.resume_id,
            raw_text=req.raw_text,
            job_description=req.job_description,
        )
    except Exception as exc:
        logger.exception("Screening failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/results/{job_id}", tags=["results"])
def get_results(job_id: str):
    """Return all scored resumes for a job, ranked by overall score."""
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT r.id, r.filename, s.overall_score, s.breakdown, s.entities, s.summary
                FROM resumes r
                JOIN scores s ON s.resume_id = r.id
                WHERE r.job_id = %s
                ORDER BY s.overall_score DESC
                """,
                (job_id,),
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    if not rows:
        raise HTTPException(status_code=404, detail="No results found for this job")

    return [
        {
            "resume_id": str(r[0]),
            "filename": r[1],
            "overall_score": float(r[2]),
            "breakdown": r[3],
            "entities": r[4],
            "summary": r[5],
        }
        for r in rows
    ]
# trigger ci
