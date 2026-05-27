variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment (dev, prod)"
  type        = string
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

variable "db_name" {
  description = "Database name for Aurora PostgreSQL"
  type        = string
  default     = "ragdb"
}
