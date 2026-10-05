variable "aws_region" {
  description = "AWS deployment region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (e.g., production, staging)"
  type        = string
  default     = "production"
}

variable "project_name" {
  description = "Project name prefix for AWS resources"
  type        = string
  default     = "secure-agentic-rag"
}

variable "vpc_cidr" {
  description = "CIDR block for the dedicated VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "domain_name" {
  description = "Base domain name for the application (e.g., example.com)"
  type        = string
  default     = "example.com"
}

variable "db_instance_class" {
  description = "RDS instance class (use db.t3.micro for cost control in development/student setups)"
  type        = string
  default     = "db.t3.micro"
}

variable "db_name" {
  description = "PostgreSQL database name"
  type        = string
  default     = "secure_rag"
}

variable "db_username" {
  description = "PostgreSQL master username"
  type        = string
  default     = "rag_admin"
}

variable "multi_az_db" {
  description = "Enable Multi-AZ RDS deployment for high availability"
  type        = bool
  default     = false
}

variable "backend_cpu" {
  description = "Fargate CPU units for backend API task (1024 = 1 vCPU)"
  type        = number
  default     = 1024
}

variable "backend_memory" {
  description = "Fargate Memory (MB) for backend API task"
  type        = number
  default     = 2048
}

variable "worker_cpu" {
  description = "Fargate CPU units for worker task"
  type        = number
  default     = 1024
}

variable "worker_memory" {
  description = "Fargate Memory (MB) for worker task"
  type        = number
  default     = 2048
}

variable "backend_desired_count" {
  description = "Desired number of backend API tasks"
  type        = number
  default     = 2
}

variable "worker_desired_count" {
  description = "Desired number of background worker tasks"
  type        = number
  default     = 1
}

variable "github_repo" {
  description = "GitHub repository (owner/repo) for OIDC federation"
  type        = string
  default     = "Ishaan-Chaturved1/Secure-Agentic-RAG-Prompt-Injection-Defens"
}
