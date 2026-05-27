variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment (dev, prod)"
  type        = string
}

variable "aws_region" {
  description = "AWS region for resource ARN construction"
  type        = string
}

variable "powertools_layer_arn" {
  description = "ARN for AWS Lambda Powertools Python layer"
  type        = string
}

variable "generation_model_id" {
  description = "Bedrock model ID for answer generation"
  type        = string
  default     = "amazon.nova-pro-v1:0"
}

variable "embedding_model_id" {
  description = "Bedrock model ID for embeddings"
  type        = string
  default     = "amazon.titan-embed-text-v2:0"
}

variable "db_secret_arn" {
  description = "Secrets Manager ARN with DB host/dbname/user/password"
  type        = string
}

variable "documents_bucket_name" {
  description = "S3 bucket name containing source documents"
  type        = string
}

variable "documents_bucket_arn" {
  description = "S3 bucket ARN containing source documents"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for Lambda VPC config"
  type        = list(string)
}

variable "vpc_id" {
  description = "VPC ID for Lambda security group"
  type        = string
}
