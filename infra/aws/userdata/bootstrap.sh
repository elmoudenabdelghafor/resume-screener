#!/bin/bash
set -e

# ── 1. System bootstrap ────────────────────────────────────────────────────────
yum update -y
yum install -y docker git

systemctl enable docker
systemctl start docker

# Install Docker Compose v2
COMPOSE_VERSION="v2.27.0"
curl -SL "https://github.com/docker/compose/releases/download/$COMPOSE_VERSION/docker-compose-linux-x86_64" \
  -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# ── 2. Clone the application repo ─────────────────────────────────────────────
cd /opt
git clone "https://github.com/${github_repo}.git" app
cd app

# ── 3. Write production .env file ─────────────────────────────────────────────
cat > .env <<EOF
# ── AI APIs ──────────────────────────────
GROQ_API_KEY=${groq_api_key}
HF_API_TOKEN=${hf_api_token}

# ── PostgreSQL (AWS RDS) ──────────────────
POSTGRES_HOST=${db_host}
POSTGRES_PORT=5432
POSTGRES_DB=resume_screener
POSTGRES_USER=screener
POSTGRES_PASSWORD=${db_password}

# ── Redis (local container) ───────────────
REDIS_HOST=redis
REDIS_PORT=6379

# ── AWS S3 (replaces MinIO) ───────────────
# Leave MINIO_ENDPOINT empty to use real AWS S3
MINIO_ENDPOINT=
AWS_REGION=${aws_region}
MINIO_BUCKET=${s3_bucket_name}
# No keys needed - EC2 IAM role provides access automatically
EOF

# ── 4. Run the init SQL against RDS ───────────────────────────────────────────
echo "Waiting 90s for RDS to accept connections..."
sleep 90

yum install -y postgresql15
PGPASSWORD="${db_password}" psql \
  -h "${db_host}" \
  -U screener \
  -d resume_screener \
  -f /opt/app/db/init.sql || true

# ── 5. Launch the production stack ───────────────────────────────────────────
docker-compose -f docker-compose.prod.yml up -d

echo "Bootstrap complete. App is starting on port 3000."
