"""Unit tests for ai-screener-service."""
import json
import pytest
from unittest.mock import MagicMock, patch

from schemas import ScoreBreakdown, NEREntities, ScreeningResult


# ── Schema validation ─────────────────────────────────────────────────────────

def test_score_breakdown_valid():
    bd = ScoreBreakdown(skills=85.0, experience=70.0, education=90.0, overall=82.0)
    assert bd.overall == 82.0


def test_score_breakdown_out_of_range():
    with pytest.raises(Exception):
        ScoreBreakdown(skills=110, experience=70, education=90, overall=82)


def test_ner_entities_defaults():
    ent = NEREntities()
    assert ent.companies == []
    assert ent.degrees == []


# ── screen_resume (mocked Groq + HF) ─────────────────────────────────────────

@patch("main.extract_entities_ner")
@patch("main.score_with_groq")
@patch("main.get_db_conn")
def test_screen_resume_success(mock_db, mock_groq, mock_ner):
    from main import screen_resume

    mock_groq.return_value = (
        {"skills": 80, "experience": 75, "education": 85, "overall": 80, "summary": "Strong Python fit"},
        '{"skills":80,"experience":75,"education":85,"overall":80,"summary":"Strong Python fit"}',
    )
    mock_ner.return_value = NEREntities(companies=["Acme Corp"], tools=["FastAPI"])

    # Mock DB connection
    mock_conn = MagicMock()
    mock_db.return_value = mock_conn
    mock_conn.__enter__ = lambda s: s
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.cursor.return_value.__enter__ = lambda s: s
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

    result = screen_resume(
        job_id="job-123",
        resume_id="resume-456",
        raw_text="Python FastAPI developer at Acme Corp",
        job_description="Python developer with FastAPI experience",
    )

    assert isinstance(result, ScreeningResult)
    assert result.overall_score == 80.0
    assert result.summary == "Strong Python fit"
    assert "Acme Corp" in result.entities.companies


# ── /healthz ───────────────────────────────────────────────────────────────────

def test_health():
    from fastapi.testclient import TestClient
    from main import app
    client = TestClient(app)
    resp = client.get("/healthz")
    assert resp.status_code == 200
