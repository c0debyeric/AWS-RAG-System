locals {
  name_prefix   = "${var.project_name}-${var.environment}"
  function_name = "${local.name_prefix}-sharepoint-sync"
}

# --- Secrets Manager for SharePoint credentials ---
resource "aws_secretsmanager_secret" "sharepoint_creds" {
  name        = "${local.name_prefix}/sharepoint-credentials"
  description = "Microsoft Entra ID credentials for SharePoint Graph API access"
}

resource "aws_secretsmanager_secret_version" "sharepoint_creds" {
  secret_id = aws_secretsmanager_secret.sharepoint_creds.id
  secret_string = jsonencode({
    tenantId     = var.sharepoint_tenant_id
    clientId     = var.sharepoint_client_id
    clientSecret = var.sharepoint_client_secret
  })
}

# --- IAM Role for SharePoint Sync Lambda ---
data "aws_iam_policy_document" "lambda_trust" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "sync_lambda" {
  name               = "${local.name_prefix}-sharepoint-sync-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_trust.json
}

data "aws_iam_policy_document" "sync_permissions" {
  # CloudWatch Logs
  statement {
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["arn:aws:logs:*:*:*"]
  }

  # S3 — read/write to documents bucket
  statement {
    actions = [
      "s3:PutObject",
      "s3:GetObject",
      "s3:HeadObject",
      "s3:ListBucket",
    ]
    resources = [
      var.documents_bucket_arn,
      "${var.documents_bucket_arn}/*",
    ]
  }

  # Secrets Manager — read SharePoint credentials
  statement {
    actions = [
      "secretsmanager:GetSecretValue",
    ]
    resources = [aws_secretsmanager_secret.sharepoint_creds.arn]
  }
}

resource "aws_iam_role_policy" "sync_lambda" {
  name   = "${local.name_prefix}-sharepoint-sync-policy"
  role   = aws_iam_role.sync_lambda.id
  policy = data.aws_iam_policy_document.sync_permissions.json
}

# --- Lambda Function ---
resource "aws_lambda_function" "sharepoint_sync" {
  function_name = local.function_name
  role          = aws_iam_role.sync_lambda.arn
  handler       = "sync.handler"
  runtime       = "python3.13"
  timeout       = 900 # 15 min max — large doc libraries need time
  memory_size   = 512
  architectures = ["arm64"]

  # Placeholder — replaced by deploy script
  filename = "${path.module}/placeholder.zip"

  # Prevent duplicate concurrent invocations
  reserved_concurrent_executions = 1

  logging_config {
    log_format = "JSON"
  }

  environment {
    variables = {
      DOCUMENTS_BUCKET     = var.documents_bucket_name
      SHAREPOINT_SECRET_ARN = aws_secretsmanager_secret.sharepoint_creds.arn
      SHAREPOINT_SITE_URL  = var.sharepoint_site_url
      POWERTOOLS_SERVICE_NAME = "sharepoint-sync"
      POWERTOOLS_LOG_LEVEL    = "INFO"
    }
  }
}

# --- EventBridge Schedule (every 6 hours) ---
resource "aws_cloudwatch_event_rule" "sync_schedule" {
  name                = "${local.name_prefix}-sharepoint-sync-schedule"
  description         = "Trigger SharePoint-to-S3 sync every 6 hours"
  schedule_expression = var.sync_schedule
}

resource "aws_cloudwatch_event_target" "sync_lambda" {
  rule = aws_cloudwatch_event_rule.sync_schedule.name
  arn  = aws_lambda_function.sharepoint_sync.arn
}

resource "aws_lambda_permission" "eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.sharepoint_sync.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.sync_schedule.arn
}
