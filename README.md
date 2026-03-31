# AI Resume Screener

A cloud-native microservices application that ingests candidate resumes, parses them, scores them against a job description using an LLM, and surfaces results in a recruiter dashboard.

## Services

| Service | Port | Description |
|---|---|---|
| `upload-service` | 8001 | Accepts PDF/DOCX uploads → MinIO + Redis job queue |
| `parser-service` | 8002 | RQ worker: extracts text, structures resume sections |
| `ai-screener-service` | 8003 | Scores resume vs JD via Groq LLM + HuggingFace NER |
| `dashboard-service` | 3000 | React recruiter UI — ranked candidates, score charts |

## Quick Start (Local)

```bash
# 1. Clone and configure environment
cp .env.example .env
# Edit .env and fill in GROQ_API_KEY and HF_API_TOKEN

# 2. Start all services
docker compose up --build

# 3. Open the dashboard
# http://localhost:3000

# 4. Smoke-test an upload
curl -X POST http://localhost:8001/upload \
  -F "file=@sample.pdf" \
  -F "job_description=Python developer with FastAPI experience"
```

## Local service URLs

| URL | Purpose |
|---|---|
| http://localhost:8001/docs | Upload service Swagger UI |
| http://localhost:8002/docs | Parser service Swagger UI |
| http://localhost:8003/docs | AI Screener Swagger UI |
| http://localhost:3000 | Recruiter Dashboard |
| http://localhost:9001 | MinIO console (minioadmin / minioadmin) |

## Repository structure

```
resume-screener/
├── services/
│   ├── upload-service/
│   ├── parser-service/
│   ├── ai-screener-service/
│   └── dashboard-service/
├── helm/                    # Kubernetes Helm charts (Phase 5)
├── infra/                   # Terraform IaC (Phase 7)
├── db/
│   └── init.sql             # PostgreSQL schema
├── .github/
│   └── workflows/           # GitHub Actions CI (Phase 6)
├── .env.example
└── docker-compose.yml
```

## Tech stack

- **Backend**: Python 3.11, FastAPI, Redis Queue, PostgreSQL, MinIO
- **AI/ML**: Groq API (Llama 3 70B), HuggingFace NER (`dslim/bert-base-NER`)
- **Frontend**: React, TypeScript, Vite, Tailwind CSS, Recharts
- **DevOps**: Docker, K3s, Helm, ArgoCD, GitHub Actions, Terraform, Oracle Cloud
- **Observability**: Prometheus, Grafana
