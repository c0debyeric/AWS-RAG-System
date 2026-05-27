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
  db_name            = var.db_name
}

# --- Bot Service (API Gateway + Lambda) ---
module "bot_service" {
  source = "../../modules/bot-service"

  project_name          = var.project_name
  environment           = var.environment
  generation_model_id   = var.generation_model_id
  embedding_model_id    = var.embedding_model_id
  db_secret_arn         = module.bedrock_kb.aurora_credentials_secret_arn
  documents_bucket_name = module.bedrock_kb.documents_bucket_name
  documents_bucket_arn  = module.bedrock_kb.documents_bucket_arn
  private_subnet_ids    = var.private_subnet_ids
  vpc_id                = var.vpc_id
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

output "api_gateway_url" {
  value = module.bot_service.api_gateway_url
}

output "ingest_lambda" {
  value = module.bot_service.ingest_lambda_function_name
}

output "sharepoint_sync_lambda" {
  value = module.sharepoint_sync.sync_lambda_function_name
}
