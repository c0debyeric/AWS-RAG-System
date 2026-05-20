output "sync_lambda_function_name" {
  description = "SharePoint sync Lambda function name"
  value       = aws_lambda_function.sharepoint_sync.function_name
}

output "sync_lambda_function_arn" {
  description = "SharePoint sync Lambda function ARN"
  value       = aws_lambda_function.sharepoint_sync.arn
}

output "sharepoint_secret_arn" {
  description = "Secrets Manager ARN for SharePoint credentials"
  value       = aws_secretsmanager_secret.sharepoint_creds.arn
}
