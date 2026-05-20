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

variable "foundation_model_id" {
  description = "Bedrock foundation model for generation"
  type        = string
  default     = "amazon.nova-pro-v1:0"
}

# --- Networking (existing VPC) ---
variable "vpc_id" {
  description = "VPC ID for Aurora cluster"
  type        = string
  default     = "vpc-04c3856083ffcad39"
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.73.2.0/24"
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for Aurora"
  type        = list(string)
  default     = ["subnet-04efa035b190ccc70", "subnet-029ec0f20609bfbec"]
}

# --- Aurora ---
variable "db_master_password" {
  description = "Aurora PostgreSQL master password"
  type        = string
  sensitive   = true
}

# --- SharePoint ---
variable "sharepoint_site_url" {
  description = "SharePoint Online site URL"
  type        = string
  default     = "https://rccl.sharepoint.com/sites/CloudInfrastructureServices"
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

# --- Bot (optional for Phase A testing) ---
variable "bot_app_id" {
  description = "Azure Bot App ID"
  type        = string
  default     = "placeholder"
  sensitive   = true
}

variable "bot_app_password" {
  description = "Azure Bot App Password"
  type        = string
  default     = "placeholder"
  sensitive   = true
}
