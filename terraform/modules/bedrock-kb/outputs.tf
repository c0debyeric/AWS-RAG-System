output "knowledge_base_id" {
  description = "Bedrock Knowledge Base ID"
  value       = aws_bedrockagent_knowledge_base.main.id
}

output "knowledge_base_arn" {
  description = "Bedrock Knowledge Base ARN"
  value       = aws_bedrockagent_knowledge_base.main.arn
}

output "data_source_id" {
  description = "Bedrock Data Source ID (for triggering ingestion)"
  value       = aws_bedrockagent_data_source.s3_docs.data_source_id
}

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
