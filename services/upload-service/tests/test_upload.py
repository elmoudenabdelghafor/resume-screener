"""Unit tests for upload-service."""
import io
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


# ── /healthz ─────────────────────────────────────────────────────────────────

def test_health():
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# ── /upload — happy path ──────────────────────────────────────────────────────

@patch("main.get_rq_queue")
@patch("main.get_s3_client")
def test_upload_pdf_success(mock_s3_cls, mock_queue_cls):
    mock_s3 = MagicMock()
    mock_s3_cls.return_value = mock_s3

    mock_queue = MagicMock()
    mock_queue_cls.return_value = mock_queue

    pdf_bytes = b"%PDF-1.4 fake pdf content"
    response = client.post(
        "/upload",
        data={"job_description": "Python developer with FastAPI experience"},
        files={"file": ("resume.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )

    assert response.status_code == 200
    body = response.json()
    assert "job_id" in body
    assert body["filename"] == "resume.pdf"
    assert body["message"] == "Resume uploaded and queued for parsing."

    # MinIO put_object was called
    mock_s3.put_object.assert_called_once()
    # RQ enqueue was called
    mock_queue.enqueue.assert_called_once()


# ── /upload — invalid file type ───────────────────────────────────────────────

def test_upload_invalid_content_type():
    response = client.post(
        "/upload",
        data={"job_description": "Python developer"},
        files={"file": ("resume.txt", io.BytesIO(b"plain text"), "text/plain")},
    )
    assert response.status_code == 422
    assert "Unsupported file type" in response.json()["detail"]


# ── /upload — MinIO failure ───────────────────────────────────────────────────

@patch("main.get_s3_client")
def test_upload_minio_failure(mock_s3_cls):
    mock_s3 = MagicMock()
    mock_s3.put_object.side_effect = Exception("MinIO unreachable")
    mock_s3_cls.return_value = mock_s3

    response = client.post(
        "/upload",
        data={"job_description": "Python developer"},
        files={"file": ("resume.pdf", io.BytesIO(b"%PDF fake"), "application/pdf")},
    )
    assert response.status_code == 502
    assert "Object storage error" in response.json()["detail"]
