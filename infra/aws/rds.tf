# ── RDS PostgreSQL (Free Tier: db.t3.micro) ──────────────────────────────────
resource "aws_db_instance" "postgres" {
  identifier        = "${var.project_name}-db"
  engine            = "postgres"
  engine_version    = "16"
  instance_class    = "db.t3.micro"   # Free tier eligible
  allocated_storage = 20              # 20 GB free tier max

  db_name  = "resume_screener"
  username = "screener"
  password = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  # Free-tier settings
  multi_az               = false
  publicly_accessible    = false
  skip_final_snapshot    = true
  deletion_protection    = false
  backup_retention_period = 0  # Disable automated backups (saves cost)

  tags = { Name = "${var.project_name}-postgres" }
}
