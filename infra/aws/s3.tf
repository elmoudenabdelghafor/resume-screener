# ── S3 Bucket for Resumes ─────────────────────────────────────────────────────
resource "aws_s3_bucket" "resumes" {
  bucket        = "${var.project_name}-resumes-${random_id.suffix.hex}"
  force_destroy = true
  tags          = { Name = "${var.project_name}-resumes" }
}

resource "random_id" "suffix" {
  byte_length = 4
}

# Block all public-access at the account level for safety
resource "aws_s3_bucket_public_access_block" "resumes" {
  bucket                  = aws_s3_bucket.resumes.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ── IAM Role for EC2 to access S3 ────────────────────────────────────────────
resource "aws_iam_role" "ec2_s3_role" {
  name = "${var.project_name}-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "ec2_s3_policy" {
  name = "${var.project_name}-s3-access"
  role = aws_iam_role.ec2_s3_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:PutObject", "s3:GetObject", "s3:DeleteObject", "s3:ListBucket"]
      Resource = [
        aws_s3_bucket.resumes.arn,
        "${aws_s3_bucket.resumes.arn}/*"
      ]
    }]
  })
}

resource "aws_iam_instance_profile" "ec2_profile" {
  name = "${var.project_name}-instance-profile"
  role = aws_iam_role.ec2_s3_role.name
}
