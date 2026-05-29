locals {
  name_prefix   = "${var.project_name}-${var.environment}"
  function_name = "${local.name_prefix}-query-handler"
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

resource "aws_security_group" "lambda" {
  name        = "${local.name_prefix}-lambda-sg"
  description = "Security group for query and ingest Lambdas"
  vpc_id      = var.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
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

  # Bedrock invocation for embeddings + generation
  statement {
    actions = [
      "bedrock:InvokeModel",
      "bedrock:InvokeModelWithResponseStream",
    ]
    resources = [
      "arn:aws:bedrock:${var.aws_region}::foundation-model/${var.generation_model_id}",
      "arn:aws:bedrock:${var.aws_region}::foundation-model/${var.embedding_model_id}",
    ]
  }

  # DB credentials
  statement {
    actions = [
      "secretsmanager:GetSecretValue",
    ]
    resources = [var.db_secret_arn]
  }

  # S3 access for ingestion Lambda and any document fetches
  statement {
    actions = [
      "s3:GetObject",
      "s3:ListBucket",
    ]
    resources = [
      var.documents_bucket_arn,
      "${var.documents_bucket_arn}/*",
    ]
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

resource "aws_iam_role_policy_attachment" "lambda_vpc" {
  role       = aws_iam_role.bot_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

# --- Lambda Function ---
resource "aws_lambda_function" "bot_handler" {
  function_name = local.function_name
  role          = aws_iam_role.bot_lambda.arn
  handler       = "app.handler"
  runtime       = "python3.13"
  timeout       = 30
  memory_size   = 256
  architectures = ["arm64"]

  layers = [var.powertools_layer_arn]

  # Placeholder — will be replaced by CI/CD pipeline
  filename = "${path.module}/placeholder.zip"

  logging_config {
    log_format = "JSON"
  }

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [aws_security_group.lambda.id]
  }

  environment {
    variables = {
      DB_SECRET_ARN       = var.db_secret_arn
      EMBEDDING_MODEL_ID  = var.embedding_model_id
      GENERATION_MODEL_ID = var.generation_model_id
      TOP_K               = "5"
      CHUNK_SIZE          = "512"
      CHUNK_OVERLAP       = "100"
      POWERTOOLS_SERVICE_NAME = "query-handler"
      POWERTOOLS_LOG_LEVEL    = "INFO"
    }
  }
}

resource "aws_lambda_function" "ingest_handler" {
  function_name = "${local.name_prefix}-ingest-handler"
  role          = aws_iam_role.bot_lambda.arn
  handler       = "ingest_handler.handler"
  runtime       = "python3.13"
  timeout       = 300
  memory_size   = 512
  architectures = ["arm64"]

  layers = [var.powertools_layer_arn]

  filename = "${path.module}/placeholder.zip"

  logging_config {
    log_format = "JSON"
  }

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [aws_security_group.lambda.id]
  }

  environment {
    variables = {
      DB_SECRET_ARN       = var.db_secret_arn
      EMBEDDING_MODEL_ID  = var.embedding_model_id
      GENERATION_MODEL_ID = var.generation_model_id
      TOP_K               = "5"
      CHUNK_SIZE          = "512"
      CHUNK_OVERLAP       = "100"
      POWERTOOLS_SERVICE_NAME = "ingest-handler"
      POWERTOOLS_LOG_LEVEL    = "INFO"
    }
  }
}

resource "aws_lambda_function" "pgvector_setup" {
  function_name = "${local.name_prefix}-pgvector-setup"
  role          = aws_iam_role.bot_lambda.arn
  handler       = "setup_handler.handler"
  runtime       = "python3.13"
  timeout       = 300
  memory_size   = 256
  architectures = ["arm64"]

  filename = "${path.module}/placeholder.zip"

  logging_config {
    log_format = "JSON"
  }

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [aws_security_group.lambda.id]
  }

  environment {
    variables = {
      DB_SECRET_ARN = var.db_secret_arn
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

resource "aws_lambda_permission" "s3_ingest" {
  statement_id  = "AllowS3InvokeIngest"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ingest_handler.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = var.documents_bucket_arn
}

resource "aws_s3_bucket_notification" "documents_ingest" {
  bucket = var.documents_bucket_name

  lambda_function {
    lambda_function_arn = aws_lambda_function.ingest_handler.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "documents/"
  }

  lambda_function {
    lambda_function_arn = aws_lambda_function.ingest_handler.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "sharepoint/"
  }

  depends_on = [aws_lambda_permission.s3_ingest]
}
