# AI Resume Screener

An AI-powered resume screening system built with a microservices architecture. Upload resumes against a job description and receive AI-generated scores, ranked candidates, and extracted entities.

## Features

- Multi-resume upload (PDF and DOCX)
- AI scoring via Groq LLaMA 3.3 70B across Skills, Experience, and Education
- Named entity extraction using HuggingFace BERT-NER (companies, degrees, tools, locations)
- Async processing with Redis background workers
- Visual dashboard with radar charts and ranked candidate list
- Live metrics via Prometheus and Grafana Cloud

## Architecture

```
Browser
  |
Dashboard Service (React + Nginx) :3000
  |
  +-- Upload Service (FastAPI) :8001 --> AWS S3 + Redis Queue
                                               |
                                        Parser Service (RQ Worker) :8002
                                               |
                                        PostgreSQL (AWS RDS)
                                               |
                                        AI Screener Service (RQ Worker) :8003
                                               |
                                        +------+------+
                                     Groq API     HuggingFace
                                  (LLaMA 3 70B)  (BERT NER)

All services --> Grafana Alloy --> Grafana Cloud (monitoring)
```

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, TypeScript, Nginx |
| Backend | FastAPI (Python 3.11) |
| AI Scoring | Groq LLaMA 3.3 70B |
| NER | HuggingFace `dslim/bert-base-NER` |
| Queue | Redis 7 + RQ |
| Database | PostgreSQL 16 |
| File Storage | MinIO (local dev) / AWS S3 (production) |
| Containers | Docker + Docker Compose |
| Cloud | AWS (EC2 t3.micro, RDS, S3, VPC) |
| IaC | Terraform |
| CI/CD | GitHub Actions |
| Monitoring | Grafana Alloy + Grafana Cloud |

## Project Structure

```
resume-screener/
├── services/
│   ├── upload-service/         FastAPI — file ingestion and job queuing
│   ├── parser-service/         RQ worker — text extraction and DB persistence
│   ├── ai-screener-service/    RQ worker — Groq scoring and NER
│   └── dashboard-service/      React + Vite frontend served by Nginx
├── db/
│   └── init.sql                PostgreSQL schema (auto-run on first boot)
├── infra/
│   └── aws/                    Terraform scripts (EC2, RDS, S3, VPC)
├── monitoring/
│   └── alloy.config            Grafana Alloy scrape and remote_write config
├── .github/workflows/          GitHub Actions CI/CD pipelines
├── docker-compose.yml          Local development environment
└── docker-compose.prod.yml     Production environment (uses AWS RDS + S3)
```

## Local Setup

**Prerequisites:** Docker Desktop, Groq API key, HuggingFace token.

```bash
git clone https://github.com/elmoudenabdelghafor/resume-screener.git
cd resume-screener
cp .env.example .env        # fill in GROQ_API_KEY and HF_API_TOKEN
docker compose up --build -d
```

Open **http://localhost:3000**.

## AWS Deployment

**Prerequisites:** [Terraform CLI](https://developer.hashicorp.com/terraform/install), [AWS CLI](https://aws.amazon.com/cli/) configured.

```bash
cd infra/aws
cp terraform.tfvars.example terraform.tfvars   # fill in your values
terraform init
terraform apply
```

Terraform provisions a VPC, EC2 t3.micro app server, RDS PostgreSQL (free tier), and an S3 bucket for resume storage. The live dashboard URL is printed when the apply completes.

The EC2 server automatically clones this repository on first boot, writes the production `.env`, initializes the database, and starts all containers using `docker-compose.prod.yml`.

## CI/CD

Every push to `main` triggers four GitHub Actions pipelines — one per service. Each pipeline:

1. Lints the code (`flake8` for Python, `eslint` for React)
2. Runs unit tests (`pytest`)
3. Builds a Docker image
4. Pushes it to GitHub Container Registry (`ghcr.io`)

## Monitoring

All FastAPI services expose a `/metrics` endpoint in Prometheus format via `prometheus_fastapi_instrumentator`. Grafana Alloy scrapes these every 15 seconds and forwards the data to Grafana Cloud.

To activate monitoring, add the following to your `.env`:

```env
GRAFANA_PROM_URL=https://prometheus-prod-XX.grafana.net/api/prom/push
GRAFANA_PROM_USER=<your numeric user ID>
GRAFANA_PROM_PASSWORD=<your grafana cloud API key>
```

Import dashboard **ID 14056** on Grafana Cloud for a pre-built FastAPI overview.

## Database Schema

```
jobs     — one row per upload session (status: pending → parsing → screening → done)
resumes  — one row per uploaded file (raw_text, sections as JSONB)
scores   — AI results per resume (overall_score, breakdown, entities, summary)
```

## License

MIT
