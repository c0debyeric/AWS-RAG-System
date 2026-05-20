variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment (dev, prod)"
  type        = string
}

variable "knowledge_base_id" {
  description = "Bedrock Knowledge Base ID to query"
  type        = string
}

variable "foundation_model_id" {
  description = "Bedrock model ID for generation"
  type        = string
  default     = "amazon.nova-pro-v1:0"
}

variable "bot_app_id" {
  description = "Azure Bot App ID (from Azure AD app registration)"
  type        = string
  sensitive   = true
}

variable "bot_app_password" {
  description = "Azure Bot App Password"
  type        = string
  sensitive   = true
}
