locals {
  name_prefix = "${var.project_name}-${var.environment}"
}

data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

# --- S3 Bucket for documents (data source) ---
resource "aws_s3_bucket" "documents" {
  bucket = "${local.name_prefix}-documents-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_server_side_encryption_configuration" "documents" {
  bucket = aws_s3_bucket.documents.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "documents" {
  bucket = aws_s3_bucket.documents.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# --- Aurora PostgreSQL + pgvector ---
resource "aws_rds_cluster" "vectors" {
  cluster_identifier = "${local.name_prefix}-pgvector"
  engine             = "aurora-postgresql"
  engine_mode        = "provisioned"
  engine_version     = "16.6"
  database_name      = "bedrockdb"
  master_username    = var.db_master_username
  master_password    = var.db_master_password

  storage_encrypted   = true
  deletion_protection = false # Set true for prod
  enable_http_endpoint = true # Required for Bedrock KB Data API access

  serverlessv2_scaling_configuration {
    min_capacity = 0.5
    max_capacity = 2.0
  }

  vpc_security_group_ids = [aws_security_group.aurora.id]
  db_subnet_group_name   = aws_db_subnet_group.aurora.name

  skip_final_snapshot = true # Set false for prod
}

resource "aws_rds_cluster_instance" "vectors" {
  identifier         = "${local.name_prefix}-pgvector-1"
  cluster_identifier = aws_rds_cluster.vectors.id
  instance_class     = "db.serverless"
  engine             = aws_rds_cluster.vectors.engine
  engine_version     = aws_rds_cluster.vectors.engine_version
}

# --- Networking for Aurora ---
resource "aws_security_group" "aurora" {
  name        = "${local.name_prefix}-aurora-sg"
  description = "Security group for Aurora pgvector cluster"
  vpc_id      = var.vpc_id

  ingress {
    description = "PostgreSQL from VPC (Bedrock and Lambda)"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_db_subnet_group" "aurora" {
  name       = "${local.name_prefix}-aurora-subnets"
  subnet_ids = var.private_subnet_ids
}

# --- Secrets Manager for Aurora credentials (used by Bedrock KB) ---
resource "aws_secretsmanager_secret" "aurora_creds" {
  name        = "${local.name_prefix}/aurora-credentials"
  description = "Aurora PostgreSQL credentials for Bedrock KB"
}

resource "aws_secretsmanager_secret_version" "aurora_creds" {
  secret_id = aws_secretsmanager_secret.aurora_creds.id
  secret_string = jsonencode({
    username = var.db_master_username
    password = var.db_master_password
  })
}

# --- IAM Role for Bedrock KB ---
data "aws_iam_policy_document" "bedrock_kb_trust" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["bedrock.amazonaws.com"]
    }
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}

resource "aws_iam_role" "bedrock_kb" {
  name               = "${local.name_prefix}-bedrock-kb-role"
  assume_role_policy = data.aws_iam_policy_document.bedrock_kb_trust.json
}

data "aws_iam_policy_document" "bedrock_kb_permissions" {
  # Access to Aurora via RDS Data API
  statement {
    actions = [
      "rds:DescribeDBClusters",
      "rds-data:ExecuteStatement",
      "rds-data:BatchExecuteStatement",
    ]
    resources = [aws_rds_cluster.vectors.arn]
  }

  # Access to Aurora credentials
  statement {
    actions = [
      "secretsmanager:GetSecretValue",
    ]
    resources = [aws_secretsmanager_secret.aurora_creds.arn]
  }

  # Access to embedding model
  statement {
    actions = [
      "bedrock:InvokeModel",
    ]
    resources = [
      "arn:aws:bedrock:${data.aws_region.current.name}::foundation-model/${var.embedding_model_id}",
    ]
  }

  # Access to S3 documents bucket (data source)
  statement {
    actions = [
      "s3:GetObject",
      "s3:ListBucket",
    ]
    resources = [
      aws_s3_bucket.documents.arn,
      "${aws_s3_bucket.documents.arn}/*",
    ]
  }
}

resource "aws_iam_role_policy" "bedrock_kb" {
  name   = "${local.name_prefix}-bedrock-kb-policy"
  role   = aws_iam_role.bedrock_kb.id
  policy = data.aws_iam_policy_document.bedrock_kb_permissions.json
}

# --- Bedrock Knowledge Base (Aurora pgvector) ---
resource "aws_bedrockagent_knowledge_base" "main" {
  name     = "${local.name_prefix}-kb"
  role_arn = aws_iam_role.bedrock_kb.arn

  knowledge_base_configuration {
    type = "VECTOR"

    vector_knowledge_base_configuration {
      embedding_model_arn = "arn:aws:bedrock:${data.aws_region.current.name}::foundation-model/${var.embedding_model_id}"
    }
  }

  storage_configuration {
    type = "RDS"

    rds_configuration {
      resource_arn           = aws_rds_cluster.vectors.arn
      credentials_secret_arn = aws_secretsmanager_secret.aurora_creds.arn
      database_name          = aws_rds_cluster.vectors.database_name
      table_name             = "bedrock_integration.bedrock_kb"

      field_mapping {
        primary_key_field = "id"
        vector_field      = "embedding"
        text_field        = "chunks"
        metadata_field    = "metadata"
      }
    }
  }

  depends_on = [
    aws_rds_cluster_instance.vectors,
    aws_iam_role_policy.bedrock_kb,
  ]
}

# --- Bedrock Data Source (S3) ---
resource "aws_bedrockagent_data_source" "s3_docs" {
  name                 = "${local.name_prefix}-s3-documents"
  knowledge_base_id    = aws_bedrockagent_knowledge_base.main.id
  data_deletion_policy = "RETAIN"

  data_source_configuration {
    type = "S3"

    s3_configuration {
      bucket_arn = aws_s3_bucket.documents.arn
    }
  }

  vector_ingestion_configuration {
    chunking_configuration {
      chunking_strategy = "FIXED_SIZE"

      fixed_size_chunking_configuration {
        max_tokens         = var.max_tokens
        overlap_percentage = var.overlap_percentage
      }
    }
  }
}
