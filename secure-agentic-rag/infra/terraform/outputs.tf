output "alb_dns_name" {
  description = "Public DNS name of the Application Load Balancer"
  value       = aws_lb.main.dns_name
}

output "ecr_repository_url" {
  description = "URL of the Amazon ECR repository"
  value       = aws_ecr_repository.app.repository_url
}

output "s3_document_bucket" {
  description = "Name of the private S3 document storage bucket"
  value       = aws_s3_bucket.documents.id
}

output "s3_frontend_bucket" {
  description = "Name of the S3 frontend static assets bucket"
  value       = aws_s3_bucket.frontend.id
}

output "rds_endpoint" {
  description = "Private endpoint of the Amazon RDS PostgreSQL instance"
  value       = aws_db_instance.postgres.endpoint
}

output "redis_endpoint" {
  description = "Private endpoint of the ElastiCache Redis cluster"
  value       = aws_elasticache_cluster.redis.cache_nodes[0].address
}

output "sqs_doc_ingestion_url" {
  description = "URL of the SQS document ingestion queue"
  value       = aws_sqs_queue.doc_ingestion.url
}

output "sqs_redteam_url" {
  description = "URL of the SQS red-team evaluation queue"
  value       = aws_sqs_queue.redteam.url
}

output "sqs_dlq_url" {
  description = "URL of the SQS Dead-Letter Queue"
  value       = aws_sqs_queue.dlq.url
}

output "github_actions_role_arn" {
  description = "IAM Role ARN for GitHub Actions OIDC deployment"
  value       = aws_iam_role.github_actions_deploy.arn
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID for frontend CDN"
  value       = aws_cloudfront_distribution.frontend.id
}

output "cloudfront_domain_name" {
  description = "CloudFront domain name for accessing the frontend"
  value       = aws_cloudfront_distribution.frontend.domain_name
}

output "frontend_url" {
  description = "Full HTTPS URL for the frontend application"
  value       = "https://${aws_cloudfront_distribution.frontend.domain_name}"
}
