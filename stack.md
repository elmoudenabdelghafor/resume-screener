# AI Resume Screener — Full Stack Reference

## Project overview

A cloud-native microservices application that ingests candidate resumes, parses them, scores them against a job description using an LLM, and surfaces results in a recruiter dashboard. Built to demonstrate a complete DevOps pipeline from code push to production observability.

---

## Application services

| Service | Language | Framework | Role |
|---|---|---|---|
| `upload-service` | Python 3.11 | FastAPI | Accepts PDF/DOCX uploads, stores to MinIO, enqueues parse job |
| `parser-service` | Python 3.11 | FastAPI + RQ | Extracts text from files, structures sections (education, skills, experience) |
| `ai-screener-service` | Python 3.11 | FastAPI | Scores resume vs job description via Groq; extracts entities via HuggingFace NER |
| `dashboard-service` | TypeScript | React + Vite | Recruiter UI — ranked candidates, score breakdown, extracted skills |

### Key libraries per service

**upload-service**
- `python-multipart` — multipart file handling
- `boto3` — MinIO / S3-compatible object storage
- `redis` — job queue producer

**parser-service**
- `PyMuPDF` (fitz) — PDF text extraction
- `python-docx` — DOCX text extraction
- `rq` (Redis Queue) — async job consumer

**ai-screener-service**
- `httpx` — async HTTP calls to Groq API
- `huggingface_hub` — NER model inference (dslim/bert-base-NER)
- `pydantic` — structured score schema validation

**dashboard-service**
- `Tailwind CSS` — utility-first styling
- `Recharts` — score visualization charts

---

## Shared infrastructure

| Component | Technology | Purpose |
|---|---|---|
| Job queue | Redis + RQ | Async job passing between upload → parser → screener |
| Database | PostgreSQL | Stores job records, resume scores, candidate metadata |
| Object storage | MinIO (S3-compatible) | Stores uploaded PDF/DOCX files |

---

## External AI APIs (free tier)

| API | Model | Used for |
|---|---|---|
| [Groq](https://console.groq.com) | `llama3-70b-8192` | Resume scoring vs job description |
| [HuggingFace](https://huggingface.co/inference-api) | `dslim/bert-base-NER` | Named entity extraction (companies, degrees, tools) |

---

## Cloud hosting

**Provider**: Oracle Cloud Free Tier (recommended)

| Resource | Spec | Cost |
|---|---|---|
| Compute | 4x ARM Ampere vCPUs | Free forever |
| Memory | 24 GB RAM | Free forever |
| Block storage | 200 GB | Free forever |
| Networking | 10 TB/month egress | Free forever |

Sufficient to run: K3s cluster + 4 service pods + Redis + PostgreSQL + MinIO + Prometheus + Grafana — all on a single VM.

**Alternative**: Render.com (simpler, no Kubernetes, services sleep after 15 min inactivity)

---

## DevOps pipeline

```
[GitHub monorepo]
      │  path-based trigger on /services/**
      ▼
[GitHub Actions]
      │  lint → unit tests → docker build → push image
      ▼
[ghcr.io registry]
      │  versioned tag: sha-<commit> per service
      │  also commits new tag into Helm values file
      ▼
[ArgoCD]
      │  watches Git repo, detects Helm values change
      │  auto-syncs cluster state
      ▼
[K3s on Oracle Cloud]
      │  4 service deployments + Helm charts
      │  rolling update, zero downtime
      ▼
[Prometheus + Grafana]
         metrics scraping + dashboards + alerting
```

### CI — GitHub Actions

Trigger: push to `main` or PR, scoped to the changed service path.

Steps per service:
1. Lint (flake8 / eslint)
2. Unit tests (pytest / vitest)
3. Docker build (multi-stage Dockerfile)
4. Push to `ghcr.io/<user>/<service>:sha-<commit>`
5. Update `helm/<service>/values.yaml` image tag and commit back

### CD — ArgoCD + Helm

- One Helm chart per service under `/helm/<service>/`
- ArgoCD Application per service, pointing to the chart
- Auto-sync enabled: any Git change triggers a cluster reconciliation
- Rollback = revert the commit in Git

### IaC — Terraform

Located in `/infra/` in the monorepo. Provisions:
- Oracle Cloud VM instance (ARM shape)
- VCN + subnet + security list
- K3s installation via remote-exec provisioner

---

## Observability

| Tool | Role | Deployment |
|---|---|---|
| Prometheus | Metrics scraping from all pods | `kube-prometheus-stack` Helm chart |
| Grafana | Dashboards + alerting | Bundled in kube-prometheus-stack |
| FastAPI metrics | `/metrics` endpoint | `prometheus-fastapi-instrumentator` lib |

### Key metrics to track

- `http_requests_total` — request count per service and status code
- `http_request_duration_seconds` — latency histogram
- `rq_jobs_queued` / `rq_jobs_failed` — queue health
- `groq_api_latency_seconds` — custom gauge for AI response time

---

## Repository structure

```
resume-screener/
├── services/
│   ├── upload-service/
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   └── requirements.txt
│   ├── parser-service/
│   ├── ai-screener-service/
│   └── dashboard-service/
├── helm/
│   ├── upload-service/
│   ├── parser-service/
│   ├── ai-screener-service/
│   └── dashboard-service/
├── infra/
│   └── main.tf
├── .github/
│   └── workflows/
│       ├── upload-service.yml
│       ├── parser-service.yml
│       ├── ai-screener-service.yml
│       └── dashboard-service.yml
└── docker-compose.yml   ← local dev
```

---

## Local development

```bash
# Start all services locally
docker compose up

# Services available at:
# upload-service    → http://localhost:8001
# parser-service    → http://localhost:8002
# ai-screener       → http://localhost:8003
# dashboard         → http://localhost:3000
# MinIO console     → http://localhost:9001
# Redis             → localhost:6379
# PostgreSQL        → localhost:5432
```

---

## CV skills covered by this project

**Cloud & DevOps**: Docker, Kubernetes (K3s), Helm, ArgoCD, GitHub Actions, Terraform, Oracle Cloud, Prometheus, Grafana

**Backend**: Python, FastAPI, Redis Queue, PostgreSQL, MinIO/S3

**AI/ML integration**: Groq API (Llama 3), HuggingFace Inference API, NER, LLM prompt engineering

**Frontend**: React, TypeScript, Vite, Tailwind CSS

**Architecture patterns**: Microservices, async job queue, GitOps, IaC