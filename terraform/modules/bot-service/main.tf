locals {
  name_prefix  = "${var.project_name}-${var.environment}"
  function_name = "${local.name_prefix}-bot-handler"
}

# --- Lambda Function for Bot Handler ---
data "aws_iam_policy_document" "lambda_trust" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "bot_lambda" {
  name               = "${local.name_prefix}-bot-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_trust.json
}

data "aws_iam_policy_document" "bot_lambda_permissions" {
  # CloudWatch Logs
  statement {
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["arn:aws:logs:*:*:*"]
  }

  # Bedrock KB retrieval
  statement {
    actions = [
      "bedrock:RetrieveAndGenerate",
      "bedrock:Retrieve",
      "bedrock:InvokeModel",
    ]
    resources = ["*"]
  }

  # Secrets Manager (bot credentials)
  statement {
    actions = [
      "secretsmanager:GetSecretValue",
    ]
    resources = [aws_secretsmanager_secret.bot_creds.arn]
  }
}

resource "aws_iam_role_policy" "bot_lambda" {
  name   = "${local.name_prefix}-bot-lambda-policy"
  role   = aws_iam_role.bot_lambda.id
  policy = data.aws_iam_policy_document.bot_lambda_permissions.json
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.bot_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# --- Secrets for Bot Credentials ---
resource "aws_secretsmanager_secret" "bot_creds" {
  name        = "${local.name_prefix}/bot-credentials"
  description = "Azure Bot Service app credentials"
}

resource "aws_secretsmanager_secret_version" "bot_creds" {
  secret_id = aws_secretsmanager_secret.bot_creds.id
  secret_string = jsonencode({
    MicrosoftAppId       = var.bot_app_id
    MicrosoftAppPassword = var.bot_app_password
  })
}

# --- Lambda Function ---
resource "aws_lambda_function" "bot_handler" {
  function_name = local.function_name
  role          = aws_iam_role.bot_lambda.arn
  handler       = "app.handler"
  runtime       = "python3.11"
  timeout       = 30
  memory_size   = 256

  # Placeholder — will be replaced by CI/CD pipeline
  filename = "${path.module}/placeholder.zip"

  environment {
    variables = {
      KNOWLEDGE_BASE_ID   = var.knowledge_base_id
      FOUNDATION_MODEL_ID = var.foundation_model_id
      BOT_SECRET_ARN      = aws_secretsmanager_secret.bot_creds.arn
    }
  }
}

# --- API Gateway (HTTP API) ---
resource "aws_apigatewayv2_api" "bot" {
  name          = "${local.name_prefix}-bot-api"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "bot_lambda" {
  api_id                 = aws_apigatewayv2_api.bot.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.bot_handler.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "bot_messages" {
  api_id    = aws_apigatewayv2_api.bot.id
  route_key = "POST /api/messages"
  target    = "integrations/${aws_apigatewayv2_integration.bot_lambda.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.bot.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.bot_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.bot.execution_arn}/*/*"
}
