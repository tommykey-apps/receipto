output "cognito_user_pool_id" {
  value = aws_cognito_user_pool.main.id
}

output "cognito_client_id" {
  value = aws_cognito_user_pool_client.web.id
}

output "api_gateway_url" {
  value = aws_apigatewayv2_stage.default.invoke_url
}

output "cloudfront_domain" {
  value = aws_cloudfront_distribution.main.domain_name
}

output "dynamodb_table_name" {
  value = aws_dynamodb_table.main.name
}

output "receipts_bucket" {
  value = aws_s3_bucket.receipts.id
}

output "sns_topic_arn" {
  value = aws_sns_topic.alerts.arn
}
