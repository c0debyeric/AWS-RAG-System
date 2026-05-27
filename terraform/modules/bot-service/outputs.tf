output "api_gateway_url" {
  description = "API Gateway endpoint URL (set as Bot messaging endpoint in Azure)"
  value       = "${aws_apigatewayv2_api.bot.api_endpoint}/api/messages"
}

output "lambda_function_name" {
  description = "Bot handler Lambda function name"
  value       = aws_lambda_function.bot_handler.function_name
}

output "lambda_function_arn" {
  description = "Bot handler Lambda function ARN"
  value       = aws_lambda_function.bot_handler.arn
}

output "ingest_lambda_function_name" {
  description = "Ingestion Lambda function name"
  value       = aws_lambda_function.ingest_handler.function_name
}

output "ingest_lambda_function_arn" {
  description = "Ingestion Lambda function ARN"
  value       = aws_lambda_function.ingest_handler.arn
}

output "pgvector_setup_lambda_function_name" {
  description = "One-time pgvector setup Lambda function name"
  value       = aws_lambda_function.pgvector_setup.function_name
}

output "pgvector_setup_lambda_function_arn" {
  description = "One-time pgvector setup Lambda function ARN"
  value       = aws_lambda_function.pgvector_setup.arn
}
