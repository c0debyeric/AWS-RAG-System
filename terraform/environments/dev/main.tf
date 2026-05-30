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
    key          = "enterprise-rag-chatbot/dev/terraform.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "teams-rag-chatbot"
      Environment = var.environment
      ManagedBy   = "terraform"
      Owner       = "your-team"
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
  db_name            = var.db_name
}

# --- Bot Service (API Gateway + Lambda) ---
module "bot_service" {
  source = "../../modules/bot-service"

  project_name          = var.project_name
  environment           = var.environment
  aws_region            = var.aws_region
  generation_model_id   = var.generation_model_id
  embedding_model_id    = var.embedding_model_id
  db_secret_arn         = module.bedrock_kb.aurora_credentials_secret_arn
  documents_bucket_name = module.bedrock_kb.documents_bucket_name
  documents_bucket_arn  = module.bedrock_kb.documents_bucket_arn
  private_subnet_ids    = var.private_subnet_ids
  vpc_id                = var.vpc_id
  powertools_layer_arn  = var.powertools_layer_arn
}

# --- SharePoint-to-S3 Sync ---
module "sharepoint_sync" {
  source = "../../modules/sharepoint-sync"

  project_name = var.project_name
  environment  = var.environment

  sharepoint_site_url      = var.sharepoint_site_url
  sharepoint_tenant_id     = var.sharepoint_tenant_id
  sharepoint_client_id     = var.sharepoint_client_id
  sharepoint_client_secret = var.sharepoint_client_secret

  documents_bucket_name = module.bedrock_kb.documents_bucket_name
  documents_bucket_arn  = module.bedrock_kb.documents_bucket_arn
}

resource "terraform_data" "pgvector_setup" {
  triggers_replace = [module.bedrock_kb.aurora_cluster_endpoint]

  provisioner "local-exec" {
    interpreter = ["PowerShell", "-Command"]
    command     = "aws lambda invoke --function-name \"${module.bot_service.pgvector_setup_lambda_function_name}\" --payload '{\"action\":\"setup\"}' --cli-binary-format raw-in-base64-out \"${path.root}/pgvector-setup-response.json\""
  }

  depends_on = [module.bot_service]
}

# --- Cross-Project Integration ---

data "aws_caller_identity" "current" {}

# Only ONE SSM lookup needed — the Vending Lambda ARN from the account-setup repo
data "aws_ssm_parameter" "vending_lambda_arn" {
  name = "/teams-platform/${var.environment}/vending-lambda-arn"
}

# --- Centralized Secrets ---

# Azure Bot credentials — used by the Router Lambda to authenticate with Microsoft
resource "aws_secretsmanager_secret" "bot_credentials" {
  name                    = "teams-platform/${var.environment}/bot-credentials"
  description             = "Azure Bot Service app_id and app_password for Teams bot"
  recovery_window_in_days = 7

  tags = {
    Purpose = "Teams Bot authentication with Microsoft Bot Framework"
  }
}

# NOTE: Secret value must be set manually after first apply:
#   aws secretsmanager put-secret-value \
#     --secret-id "teams-platform/dev/bot-credentials" \
#     --secret-string '{"MicrosoftAppId":"YOUR_APP_ID","MicrosoftAppPassword":"YOUR_PASSWORD","MicrosoftAppTenantId":"YOUR_TENANT_ID"}'

# --- Router (front door for Teams — routes to RAG or Vending) ---
module "router" {
  source = "../../modules/router"

  project_name       = var.project_name
  environment        = var.environment
  rag_lambda_arn     = module.bot_service.lambda_function_arn
  vending_lambda_arn = data.aws_ssm_parameter.vending_lambda_arn.value
  bot_secret_arn     = aws_secretsmanager_secret.bot_credentials.arn
}

# --- Outputs ---
output "documents_bucket" {
  value = module.bedrock_kb.documents_bucket_name
}

output "aurora_endpoint" {
  value = module.bedrock_kb.aurora_cluster_endpoint
}

output "aurora_secret_arn" {
  value = module.bedrock_kb.aurora_credentials_secret_arn
}

output "rag_api_gateway_url" {
  description = "Original RAG API Gateway (direct access, bypasses router)"
  value       = module.bot_service.api_gateway_url
}

output "router_api_gateway_url" {
  description = "Router API Gateway — set this in Azure Bot Service configuration"
  value       = module.router.api_gateway_url
}

output "ingest_lambda" {
  value = module.bot_service.ingest_lambda_function_name
}

output "sharepoint_sync_lambda" {
  value = module.sharepoint_sync.sync_lambda_function_name
}

output "rag_lambda_arn" {
  value = module.bot_service.lambda_function_arn
}

output "router_lambda_arn" {
  value = module.router.lambda_function_arn
}

output "bot_secret_arn" {
  description = "Populate with: aws secretsmanager put-secret-value --secret-id <arn> --secret-string '{...}'"
  value       = aws_secretsmanager_secret.bot_credentials.arn
}

output "sessions_table" {
  value = module.router.sessions_table_name
}
