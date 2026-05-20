variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

# --- SharePoint Configuration ---
variable "sharepoint_site_url" {
  description = "SharePoint Online site URL (e.g. https://rccl.sharepoint.com/sites/CloudInfrastructureServices)"
  type        = string
}

variable "sharepoint_tenant_id" {
  description = "Microsoft 365 tenant ID"
  type        = string
  sensitive   = true
}

variable "sharepoint_client_id" {
  description = "Entra ID application (client) ID"
  type        = string
  sensitive   = true
}

variable "sharepoint_client_secret" {
  description = "Entra ID application client secret"
  type        = string
  sensitive   = true
}

# --- Bedrock KB references ---
variable "knowledge_base_id" {
  description = "Bedrock Knowledge Base ID"
  type        = string
}

variable "knowledge_base_arn" {
  description = "Bedrock Knowledge Base ARN"
  type        = string
}

variable "data_source_id" {
  description = "Bedrock Data Source ID"
  type        = string
}

variable "documents_bucket_name" {
  description = "S3 bucket name for documents"
  type        = string
}

variable "documents_bucket_arn" {
  description = "S3 bucket ARN for documents"
  type        = string
}

# --- Schedule ---
variable "sync_schedule" {
  description = "EventBridge cron/rate expression for sync frequency"
  type        = string
  default     = "rate(6 hours)"
}
