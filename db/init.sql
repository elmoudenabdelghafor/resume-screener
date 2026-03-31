-- ─────────────────────────────────────────────────────────
-- AI Resume Screener — PostgreSQL Schema
-- Run automatically by the postgres container on first boot
-- ─────────────────────────────────────────────────────────

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ── jobs ─────────────────────────────────────────────────
-- One row per uploaded resume + job-description pairing
CREATE TABLE IF NOT EXISTS jobs (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status        TEXT NOT NULL DEFAULT 'pending',   -- pending | parsing | screening | done | failed
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    job_description TEXT NOT NULL
);

-- ── resumes ───────────────────────────────────────────────
-- Parsed resume data, linked to a job
CREATE TABLE IF NOT EXISTS resumes (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id        UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    filename      TEXT NOT NULL,
    storage_key   TEXT NOT NULL,          -- MinIO object key
    raw_text      TEXT,                   -- Extracted plain text
    sections      JSONB,                  -- { education, experience, skills, ... }
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── scores ────────────────────────────────────────────────
-- AI screening results per resume
CREATE TABLE IF NOT EXISTS scores (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resume_id       UUID NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,
    overall_score   NUMERIC(5, 2),        -- 0.00 – 100.00
    breakdown       JSONB,                -- { skills: 80, experience: 70, education: 90, ... }
    entities        JSONB,                -- NER output: companies, degrees, tools
    summary         TEXT,                 -- LLM-generated one-line summary
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Indexes ───────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_resumes_job_id  ON resumes(job_id);
CREATE INDEX IF NOT EXISTS idx_scores_resume_id ON scores(resume_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status      ON jobs(status);
