locals {
  name_prefix   = "${var.project_name}-${var.environment}"
  function_name = "${local.name_prefix}-router"
}

# -----------------------------------------------------------------------------
# DynamoDB — Router Session Store
# -----------------------------------------------------------------------------
resource "aws_dynamodb_table" "sessions" {
  name         = "${local.name_prefix}-sessions"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "PK"

  attribute {
    name = "PK"
    type = "S"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  tags = {
    Purpose = "Teams bot routing session state"
  }
}

# -----------------------------------------------------------------------------
# IAM Role — Router Lambda
# -----------------------------------------------------------------------------
data "aws_iam_policy_document" "lambda_trust" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "router_lambda" {
  name               = "${local.name_prefix}-router-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_trust.json
}

data "aws_iam_policy_document" "router_lambda_permissions" {
  # CloudWatch Logs
  statement {
    sid = "CloudWatchLogs"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["arn:aws:logs:*:*:*"]
  }

  # DynamoDB — Session store
  statement {
    sid = "DynamoDBSessions"
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:DeleteItem",
    ]
    resources = [aws_dynamodb_table.sessions.arn]
  }

  # Lambda — Invoke RAG backend (same state, ARN passed in directly)
  # Lambda — Invoke Vending backend (ARN discovered via SSM)
  statement {
    sid = "InvokeBackendLambdas"
    actions = [
      "lambda:InvokeFunction",
    ]
    resources = [
      var.rag_lambda_arn,
      var.vending_lambda_arn,
    ]
  }

  # Secrets Manager — Read bot credentials
  statement {
    sid = "ReadBotSecret"
    actions = [
      "secretsmanager:GetSecretValue",
    ]
    resources = [var.bot_secret_arn]
  }
}

resource "aws_iam_role_policy" "router_lambda" {
  name   = "${local.name_prefix}-router-lambda-policy"
  role   = aws_iam_role.router_lambda.id
  policy = data.aws_iam_policy_document.router_lambda_permissions.json
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.router_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# -----------------------------------------------------------------------------
# Lambda Function — Router (NOT in VPC)
# Only calls other Lambdas (AWS API) + public Microsoft OAuth endpoints.
# Keeping it out of VPC avoids needing a NAT Gateway.
# -----------------------------------------------------------------------------
resource "aws_lambda_function" "router" {
  function_name = local.function_name
  role          = aws_iam_role.router_lambda.arn
  handler       = "app.handler"
  runtime       = "python3.13"
  timeout       = 30
  memory_size   = 256
  architectures = ["arm64"]

  # Placeholder — CI/CD pipeline deploys the actual code from src/router/
  filename = "${path.module}/placeholder.zip"

  logging_config {
    log_format = "JSON"
  }

  environment {
    variables = {
      BOT_SECRET_ARN          = var.bot_secret_arn
      RAG_LAMBDA_ARN          = var.rag_lambda_arn
      VENDING_LAMBDA_ARN      = var.vending_lambda_arn
      SESSION_TABLE_NAME      = aws_dynamodb_table.sessions.name
      POWERTOOLS_SERVICE_NAME = "teams-bot-router"
      POWERTOOLS_LOG_LEVEL    = "INFO"
    }
  }
}

# -----------------------------------------------------------------------------
# API Gateway (HTTP API) — Azure Bot messaging endpoint
# -----------------------------------------------------------------------------
resource "aws_apigatewayv2_api" "router" {
  name          = "${local.name_prefix}-router-api"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "router_lambda" {
  api_id                 = aws_apigatewayv2_api.router.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.router.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "messages" {
  api_id    = aws_apigatewayv2_api.router.id
  route_key = "POST /api/messages"
  target    = "integrations/${aws_apigatewayv2_integration.router_lambda.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.router.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.router.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.router.execution_arn}/*/*"
}
