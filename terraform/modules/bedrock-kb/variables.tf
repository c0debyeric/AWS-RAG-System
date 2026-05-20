variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment (dev, prod)"
  type        = string
}

variable "embedding_model_id" {
  description = "Bedrock embedding model ID"
  type        = string
  default     = "amazon.titan-embed-text-v2:0"
}

variable "foundation_model_id" {
  description = "Bedrock foundation model for RetrieveAndGenerate"
  type        = string
  default     = "amazon.nova-pro-v1:0"
}

# --- Networking ---
variable "vpc_id" {
  description = "VPC ID for Aurora cluster"
  type        = string
}

variable "vpc_cidr" {
  description = "VPC CIDR block for security group ingress"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for Aurora DB subnet group"
  type        = list(string)
}

# --- Aurora ---
variable "db_master_username" {
  description = "Master username for Aurora PostgreSQL"
  type        = string
  default     = "bedrock_admin"
}

variable "db_master_password" {
  description = "Master password for Aurora PostgreSQL"
  type        = string
  sensitive   = true
}

# --- Chunking ---
variable "max_tokens" {
  description = "Maximum tokens per chunk"
  type        = number
  default     = 512
}

variable "overlap_percentage" {
  description = "Overlap between chunks as percentage"
  type        = number
  default     = 20
}
