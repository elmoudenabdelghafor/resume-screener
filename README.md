# AI Resume Screener

An AI-powered resume screening system built with a microservices architecture. Upload resumes against a job description and receive AI-generated scores, ranked candidates, and extracted entities.

## Features

- Multi-resume upload (PDF and DOCX)
- AI scoring via Groq LLaMA 3.3 70B across Skills, Experience, and Education
- Named entity extraction using HuggingFace BERT-NER (companies, degrees, tools, locations)
- Async processing with Redis background workers
- Visual dashboard with radar charts and ranked candidate list
- Live metrics via Prometheus and Grafana Cloud

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React, Vite, TypeScript, Nginx |
| Backend | FastAPI (Python 3.11) |
| AI Scoring | Groq LLaMA 3.3 70B |
| NER | HuggingFace `dslim/bert-base-NER` |
| Queue | Redis + RQ |
| Database | PostgreSQL 16 |
| File Storage | MinIO (dev) / AWS S3 (prod) |
| Containers | Docker + Docker Compose |
| IaC | Terraform (AWS EC2, RDS, S3) |
| CI/CD | GitHub Actions |
| Monitoring | Grafana Alloy + Grafana Cloud |

## Architecture

```
Browser → Dashboard (React/Nginx)
              |
        Upload Service (FastAPI) → S3/MinIO + Redis
              |
        Parser Service (RQ Worker) → PostgreSQL
              |
        AI Screener Service → Groq API + HuggingFace
              |
        Grafana Alloy → Grafana Cloud
```

## Local Setup

**Prerequisites:** Docker Desktop, Groq API key, HuggingFace token.

```bash
git clone https://github.com/elmoudenabdelghafor/resume-screener.git
cd resume-screener
cp .env.example .env   # fill in GROQ_API_KEY and HF_API_TOKEN
docker compose up --build -d
```

Open **http://localhost:3000**.

## AWS Deployment

**Prerequisites:** Terraform CLI, AWS CLI configured.

```bash
cd infra/aws
cp terraform.tfvars.example terraform.tfvars   # fill in your values
terraform init
terraform apply
```

Terraform provisions a VPC, EC2 t3.micro, RDS PostgreSQL (free tier), and an S3 bucket. The app URL is printed when complete.

## Project Structure

```
services/
  upload-service/       FastAPI — file ingestion and job queuing
  parser-service/       RQ worker — text extraction and database write
  ai-screener-service/  RQ worker — Groq scoring and NER
  dashboard-service/    React frontend served by Nginx
db/init.sql             PostgreSQL schema
helm/                   Kubernetes Helm charts
infra/aws/              Terraform scripts for AWS
monitoring/             Grafana Alloy config
.github/workflows/      GitHub Actions CI/CD pipelines
docker-compose.yml      Local development
docker-compose.prod.yml Production (uses AWS RDS + S3)
```

## CI/CD

On every push to `main`, GitHub Actions runs lint, tests, builds a Docker image, pushes it to the GitHub Container Registry, and updates the Helm chart version tag.

## License

MIT
