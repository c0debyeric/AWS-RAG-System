locals {
  name_prefix = "${var.project_name}-${var.environment}"
}

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
  database_name      = var.db_name
  master_username    = var.db_master_username
  master_password    = var.db_master_password

  storage_encrypted   = true
  deletion_protection = false # Set true for prod

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
  description = "Aurora PostgreSQL credentials for custom RAG pipeline"
}

resource "aws_secretsmanager_secret_version" "aurora_creds" {
  secret_id = aws_secretsmanager_secret.aurora_creds.id
  secret_string = jsonencode({
    host     = aws_rds_cluster.vectors.endpoint
    port     = 5432
    dbname   = var.db_name
    username = var.db_master_username
    password = var.db_master_password
  })
}
