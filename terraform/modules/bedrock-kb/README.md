# Bedrock Knowledge Base Module

This module creates:
- Amazon Bedrock Knowledge Base
- SharePoint data source connector (via Microsoft Graph)
- Aurora PostgreSQL Serverless v2 with pgvector (vector store)
- IAM roles for Bedrock to access Aurora and invoke embedding model
- S3 bucket for ingestion metadata
- Secrets Manager entries for SharePoint and Aurora credentials

## Usage

```hcl
module "bedrock_kb" {
  source = "../../modules/bedrock-kb"

  project_name             = var.project_name
  environment              = var.environment
  sharepoint_tenant_id     = var.sharepoint_tenant_id
  sharepoint_client_id     = var.sharepoint_client_id
  sharepoint_client_secret = var.sharepoint_client_secret
  sharepoint_site_urls     = var.sharepoint_site_urls
  vpc_id                   = var.vpc_id
  vpc_cidr                 = var.vpc_cidr
  private_subnet_ids       = var.private_subnet_ids
  db_master_password       = var.db_master_password
}
```

## Cost

Aurora Serverless v2 (0.5–2 ACU): ~$50–70/month for dev workloads.
Upgrade path: swap `storage_configuration` to `OPENSEARCH_SERVERLESS` for production scale.
