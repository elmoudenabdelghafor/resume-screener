# 🤖 AI Resume Screener

An end-to-end, production-grade **AI-powered Resume Screening System** built with a microservices architecture. Upload multiple resumes against a job description and get AI-generated scores, ranked candidates, and named entity extraction — all in real time.

![Dashboard Preview](services/dashboard-service/src/assets/hero.png)

---

## ✨ Features

- 📄 **Multi-resume upload** — PDF and DOCX support
- 🧠 **AI Scoring** — Groq LLaMA 3.3 70B evaluates each resume across Skills, Experience, and Education
- 🔍 **Named Entity Extraction** — HuggingFace BERT-NER extracts companies, degrees, tools, and locations
- 📊 **Visual Dashboard** — Radar charts, score bars, and ranked candidate cards
- ⚡ **Async Processing** — Redis + RQ background workers so uploads never block
- 🔒 **Secure Storage** — Files stored in MinIO (local) or AWS S3 (production)
- 📈 **Live Monitoring** — Prometheus metrics + Grafana Cloud dashboards
- 🚀 **Cloud-Ready** — Fully automated deployment to AWS with Terraform

---

## 🏗️ Architecture

```
Browser
  │
  └─► Dashboard Service (React + Nginx) :3000
          │
          ├─► Upload Service (FastAPI) :8001
          │       │
          │       ├─► AWS S3 / MinIO (file storage)
          │       └─► Redis (job queue)
          │                 │
          │           Parser Service (RQ Worker) :8002
          │                 │
          │                 ├─► PostgreSQL (structured data)
          │                 └─► Redis (screen queue)
          │                           │
          │                     AI Screener Service :8003
          │                           │
          │                     ┌─────┴─────┐
          │                  Groq API    HuggingFace
          │               (LLaMA 3 70B)  (BERT NER)
          │
          └─► Grafana Alloy → Grafana Cloud (monitoring)
```

---

## 🛠️ Tech Stack

### Backend
| Technology | Role |
|---|---|
| **FastAPI** (Python 3.11) | All 3 backend microservices |
| **RQ** (Redis Queue) | Async background job processing |
| **psycopg2** | PostgreSQL database driver |
| **boto3** | S3 / MinIO file storage |
| **PyMuPDF (fitz)** | PDF text extraction |
| **python-docx** | DOCX text extraction |
| **httpx** | Async HTTP client for Groq API |

### AI & Machine Learning
| Technology | Role |
|---|---|
| **Groq LLaMA 3.3 70B** | Resume scoring and summary generation |
| **HuggingFace `dslim/bert-base-NER`** | Named entity recognition (companies, degrees, tools) |
| **prometheus_fastapi_instrumentator** | Automatic `/metrics` endpoint on all services |

### Frontend
| Technology | Role |
|---|---|
| **React 18** | UI framework |
| **Vite + TypeScript** | Build tooling and type safety |
| **Recharts** | Radar charts and score visualizations |
| **React Router v6** | Client-side navigation |
| **Axios** | API calls to backend services |
| **Nginx** | Serves the built React app and proxies API calls |

### Infrastructure & DevOps
| Technology | Role |
|---|---|
| **Docker + Docker Compose** | Local development environment |
| **PostgreSQL 16** | Relational database (jobs, resumes, scores) |
| **Redis 7** | Message broker and job queue |
| **MinIO** | S3-compatible object storage for local dev |
| **AWS S3** | Production file storage |
| **AWS RDS** (db.t3.micro) | Managed PostgreSQL in production |
| **AWS EC2** (t3.micro) | App server (free tier) |
| **Terraform** | Infrastructure as Code for AWS |
| **Helm** | Kubernetes deployment charts |
| **GitHub Actions** | CI/CD pipelines (lint → test → build → deploy) |
| **Grafana Alloy** | Metrics scraping agent |
| **Grafana Cloud** | Prometheus + Grafana dashboards (hosted, free) |

---

## 🚀 Getting Started (Local)

### Prerequisites
- Docker Desktop installed and running
- A [Groq API key](https://console.groq.com) (free)
- A [HuggingFace token](https://huggingface.co/settings/tokens) (free)

### 1. Clone the repository
```bash
git clone https://github.com/elmoudenabdelghafor/resume-screener.git
cd resume-screener
```

### 2. Configure environment variables
```bash
cp .env.example .env
# Edit .env and fill in your GROQ_API_KEY and HF_API_TOKEN
```

### 3. Start the full stack
```bash
docker compose up --build -d
```

### 4. Open the dashboard
Navigate to **http://localhost:3000**

> First run may take 2-3 minutes while Docker builds all images and the database initializes.

---

## 📁 Project Structure

```
resume-screener/
├── services/
│   ├── upload-service/        # FastAPI — file ingestion + job queuing
│   ├── parser-service/        # FastAPI + RQ worker — text extraction + DB write
│   ├── ai-screener-service/   # FastAPI + RQ worker — Groq scoring + NER
│   └── dashboard-service/     # React + Vite frontend + Nginx
├── db/
│   └── init.sql               # PostgreSQL schema (auto-run on first boot)
├── helm/                      # Kubernetes Helm charts for all 4 services
├── infra/
│   └── aws/                   # Terraform scripts for EC2 + RDS + S3 + VPC
├── monitoring/
│   └── alloy.config           # Grafana Alloy scrape + remote_write config
├── .github/
│   └── workflows/             # GitHub Actions CI/CD pipelines
├── docker-compose.yml         # Local development environment
└── docker-compose.prod.yml    # Production environment (uses AWS RDS + S3)
```

---

## ☁️ Cloud Deployment (AWS Free Tier)

The entire infrastructure is provisioned automatically with Terraform.

### Prerequisites
- [Terraform CLI](https://developer.hashicorp.com/terraform/install)
- [AWS CLI](https://aws.amazon.com/cli/) configured with your credentials (`aws configure`)

### Deploy
```bash
cd infra/aws
cp terraform.tfvars.example terraform.tfvars
# Fill in terraform.tfvars with your values

terraform init
terraform apply
```

Terraform will provision:
- ✅ VPC, Subnets, Security Groups
- ✅ RDS PostgreSQL (db.t3.micro — free tier)
- ✅ S3 Bucket with IAM role
- ✅ EC2 t3.micro with auto-bootstrap script

After ~10 minutes, Terraform prints your live URL:
```
dashboard_url = "http://X.X.X.X:3000"
```

---

## 🔄 CI/CD Pipeline

Every `git push` to `main` automatically:

1. **Lints** the code (flake8 / eslint)
2. **Tests** the code (pytest)
3. **Builds** a Docker image
4. **Pushes** to GitHub Container Registry (`ghcr.io`)
5. **Updates** the Helm chart version tag (GitOps)

```
git push → GitHub Actions → Tests pass → Docker Image → Helm Updated
```

---

## 📊 Monitoring

All FastAPI services expose a `/metrics` endpoint in Prometheus format.
Grafana Alloy scrapes these every 15 seconds and forwards to Grafana Cloud.

Key metrics available:
- `http_requests_total` — request counts per service
- `http_request_duration_seconds` — API latency
- `http_requests_in_progress` — concurrent requests

Import Grafana dashboard **ID 14056** for a pre-built FastAPI overview.

---

## 🗄️ Database Schema

```sql
jobs     — one row per upload session (status: pending → parsing → screening → done)
resumes  — one row per uploaded file (raw_text, sections as JSONB)
scores   — AI results per resume (overall_score, breakdown, entities, summary)
```

---

## 📝 License

MIT License — free to use, modify, and distribute.
