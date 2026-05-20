terraform {
  required_version = ">= 1.10"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket       = "terraform-state-sharedservices-east-044061434394"
    key          = "teams-rag-chatbot/dev/terraform.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true
    profile      = "shared"
  }
}

provider "aws" {
  region  = var.aws_region
  profile = "shared"

  default_tags {
    tags = {
      Project     = "teams-rag-chatbot"
      Environment = var.environment
      ManagedBy   = "terraform"
      Owner       = "cloud-infrastructure"
    }
  }
}

# --- Bedrock Knowledge Base (Aurora pgvector + S3 data source) ---
module "bedrock_kb" {
  source = "../../modules/bedrock-kb"

  project_name       = var.project_name
  environment        = var.environment
  vpc_id             = var.vpc_id
  vpc_cidr           = var.vpc_cidr
  private_subnet_ids = var.private_subnet_ids
  db_master_password = var.db_master_password
  foundation_model_id = var.foundation_model_id
}

# --- Bot Service (API Gateway + Lambda) ---
module "bot_service" {
  source = "../../modules/bot-service"

  project_name       = var.project_name
  environment        = var.environment
  knowledge_base_id  = module.bedrock_kb.knowledge_base_id
  foundation_model_id = var.foundation_model_id
  bot_app_id         = var.bot_app_id
  bot_app_password   = var.bot_app_password
}

# --- SharePoint-to-S3 Sync ---
module "sharepoint_sync" {
  source = "../../modules/sharepoint-sync"

  project_name = var.project_name
  environment  = var.environment

  sharepoint_site_url    = var.sharepoint_site_url
  sharepoint_tenant_id   = var.sharepoint_tenant_id
  sharepoint_client_id   = var.sharepoint_client_id
  sharepoint_client_secret = var.sharepoint_client_secret

  knowledge_base_id    = module.bedrock_kb.knowledge_base_id
  knowledge_base_arn   = module.bedrock_kb.knowledge_base_arn
  data_source_id       = module.bedrock_kb.data_source_id
  documents_bucket_name = module.bedrock_kb.documents_bucket_name
  documents_bucket_arn  = module.bedrock_kb.documents_bucket_arn
}

# --- Outputs ---
output "knowledge_base_id" {
  value = module.bedrock_kb.knowledge_base_id
}

output "documents_bucket" {
  value = module.bedrock_kb.documents_bucket_name
}

output "api_gateway_url" {
  value = module.bot_service.api_gateway_url
}

output "sharepoint_sync_lambda" {
  value = module.sharepoint_sync.sync_lambda_function_name
}
