"""
parser-service  –  FastAPI (status + health endpoints)
The parsing work is done by worker.py; this module provides HTTP endpoints
for job status queries and launches the RQ worker process.
"""
import logging
import os

import psycopg2
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

logger = logging.getLogger("parser-service")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Parser Service", version="1.0.0")

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


# ── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/healthz", tags=["ops"])
def health():
    return {"status": "ok"}


@app.get("/jobs/{job_id}", tags=["status"])
def get_job_status(job_id: str):
    """Return the current status of a parsing / screening job."""
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, status, created_at, updated_at FROM jobs WHERE id = %s",
                (job_id,),
            )
            row = cur.fetchone()
    finally:
        conn.close()

    if not row:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    return {
        "job_id": str(row[0]),
        "status": row[1],
        "created_at": row[2].isoformat(),
        "updated_at": row[3].isoformat(),
    }


@app.get("/jobs/{job_id}/resumes", tags=["status"])
def get_job_resumes(job_id: str):
    """Return all parsed resumes for a given job."""
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT r.id, r.filename, r.created_at,
                       s.overall_score, s.breakdown, s.entities, s.summary
                FROM resumes r
                LEFT JOIN scores s ON s.resume_id = r.id
                WHERE r.job_id = %s
                ORDER BY s.overall_score DESC NULLS LAST
                """,
                (job_id,),
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    return [
        {
            "resume_id": str(r[0]),
            "filename": r[1],
            "created_at": r[2].isoformat(),
            "overall_score": float(r[3]) if r[3] is not None else None,
            "breakdown": r[4],
            "entities": r[5],
            "summary": r[6],
        }
        for r in rows
    ]
