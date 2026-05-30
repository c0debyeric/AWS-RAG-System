variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

# --- SharePoint Configuration ---
variable "sharepoint_site_url" {
  description = "SharePoint Online site URL (e.g. https://your-tenant.sharepoint.com/sites/YourSite)"
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
