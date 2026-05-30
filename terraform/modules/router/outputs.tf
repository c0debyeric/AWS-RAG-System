output "api_gateway_url" {
  description = "Router API Gateway endpoint — set this in Azure Bot Service"
  value       = "${aws_apigatewayv2_api.router.api_endpoint}/api/messages"
}

output "lambda_function_name" {
  description = "Router Lambda function name"
  value       = aws_lambda_function.router.function_name
}

output "lambda_function_arn" {
  description = "Router Lambda function ARN"
  value       = aws_lambda_function.router.arn
}

output "sessions_table_name" {
  description = "DynamoDB sessions table name"
  value       = aws_dynamodb_table.sessions.name
}
