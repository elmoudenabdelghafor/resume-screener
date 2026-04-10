variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Prefix for all resource names"
  type        = string
  default     = "resume-screener"
}

variable "instance_type" {
  description = "EC2 instance type (t3.micro is free-tier eligible)"
  type        = string
  default     = "t3.micro"
}

variable "db_password" {
  description = "Password for the RDS PostgreSQL instance"
  type        = string
  sensitive   = true
}

variable "my_ip" {
  description = "Your public IP in CIDR notation (e.g. 102.182.x.x/32). Find it at https://checkip.amazonaws.com"
  type        = string
}

variable "groq_api_key" {
  description = "Groq API key for the AI screener service"
  type        = string
  sensitive   = true
}

variable "hf_api_token" {
  description = "HuggingFace API token for the NER service"
  type        = string
  sensitive   = true
}

variable "github_repo" {
  description = "GitHub repo to clone on the EC2 instance (e.g. elmoudenabdelghafor/resume-screener)"
  type        = string
  default     = "elmoudenabdelghafor/resume-screener"
}
