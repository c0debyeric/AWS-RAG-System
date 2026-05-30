variable "project_name" {
  description = "Project name prefix"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "rag_lambda_arn" {
  description = "ARN of the RAG query-handler Lambda (same state file)"
  type        = string
}

variable "vending_lambda_arn" {
  description = "ARN of the Vending agent Lambda (from SSM)"
  type        = string
}

variable "bot_secret_arn" {
  description = "ARN of the Secrets Manager secret containing Azure Bot credentials"
  type        = string
}
