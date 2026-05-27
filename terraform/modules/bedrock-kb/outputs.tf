output "documents_bucket_name" {
  description = "S3 bucket for uploading documents"
  value       = aws_s3_bucket.documents.id
}

output "documents_bucket_arn" {
  description = "S3 bucket ARN for documents"
  value       = aws_s3_bucket.documents.arn
}

output "aurora_cluster_endpoint" {
  description = "Aurora PostgreSQL cluster endpoint"
  value       = aws_rds_cluster.vectors.endpoint
}

output "aurora_cluster_arn" {
  description = "Aurora PostgreSQL cluster ARN"
  value       = aws_rds_cluster.vectors.arn
}

output "aurora_credentials_secret_arn" {
  description = "Secrets Manager ARN containing Aurora connection credentials"
  value       = aws_secretsmanager_secret.aurora_creds.arn
}

output "aurora_security_group_id" {
  description = "Aurora security group ID"
  value       = aws_security_group.aurora.id
}
