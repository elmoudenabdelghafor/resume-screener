# ── Latest Amazon Linux 2023 AMI ─────────────────────────────────────────────
data "aws_ami" "al2023" {
  most_recent = true
  owners      = ["amazon"]
  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }
  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# ── EC2 Instance ──────────────────────────────────────────────────────────────
resource "aws_instance" "app" {
  ami                    = data.aws_ami.al2023.id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.ec2.id]
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name

  root_block_device {
    volume_size = 30
    volume_type = "gp3"
  }

  user_data = templatefile("${path.module}/userdata/bootstrap.sh", {
    github_repo    = var.github_repo
    groq_api_key   = var.groq_api_key
    hf_api_token   = var.hf_api_token
    db_host        = aws_db_instance.postgres.address
    db_password    = var.db_password
    s3_bucket_name = aws_s3_bucket.resumes.bucket
    aws_region     = var.aws_region
  })

  tags = { Name = "${var.project_name}-app" }

  # Wait for RDS to be ready before booting EC2
  depends_on = [aws_db_instance.postgres]
}

# ── Elastic IP (static public IP) ────────────────────────────────────────────
resource "aws_eip" "app" {
  instance = aws_instance.app.id
  domain   = "vpc"
  tags     = { Name = "${var.project_name}-eip" }
}
