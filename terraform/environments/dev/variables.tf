variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, prod)"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "teams-rag-chatbot"
}

variable "generation_model_id" {
  description = "Bedrock foundation model for generation"
  type        = string
  default     = "amazon.nova-pro-v1:0"
}

variable "embedding_model_id" {
  description = "Bedrock embedding model ID"
  type        = string
  default     = "amazon.titan-embed-text-v2:0"
}

variable "powertools_layer_arn" {
  description = "ARN for AWS Lambda Powertools Python layer"
  type        = string
  default     = "arn:aws:lambda:us-east-1:017000801446:layer:AWSLambdaPowertoolsPythonV3-python313-arm64:29"
}

# --- Networking (existing VPC) ---
variable "vpc_id" {
  description = "VPC ID for Aurora cluster"
  type        = string
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for Aurora"
  type        = list(string)
}

# --- Aurora ---
variable "db_master_password" {
  description = "Aurora PostgreSQL master password"
  type        = string
  sensitive   = true
}

variable "db_name" {
  description = "Aurora PostgreSQL database name"
  type        = string
  default     = "ragdb"
}

# --- SharePoint ---
variable "sharepoint_site_url" {
  description = "SharePoint Online site URL"
  type        = string
  default     = "https://your-tenant.sharepoint.com/sites/YourSite"
}

variable "sharepoint_tenant_id" {
  description = "Microsoft 365 tenant ID"
  type        = string
  default     = "placeholder"
  sensitive   = true
}

variable "sharepoint_client_id" {
  description = "Entra ID application (client) ID"
  type        = string
  default     = "placeholder"
  sensitive   = true
}

variable "sharepoint_client_secret" {
  description = "Entra ID application client secret"
  type        = string
  default     = "placeholder"
  sensitive   = true
}

