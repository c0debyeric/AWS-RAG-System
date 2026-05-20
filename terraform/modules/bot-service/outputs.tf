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
