output "ec2_public_ip" {
  description = "Public IP of the EC2 app server (your app's address)"
  value       = aws_eip.app.public_ip
}

output "dashboard_url" {
  description = "URL to open the dashboard in your browser"
  value       = "http://${aws_eip.app.public_ip}:3000"
}

output "rds_endpoint" {
  description = "PostgreSQL RDS endpoint (internal)"
  value       = aws_db_instance.postgres.address
}

output "s3_bucket_name" {
  description = "S3 bucket name for uploaded resumes"
  value       = aws_s3_bucket.resumes.bucket
}
