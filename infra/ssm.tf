resource "aws_ssm_parameter" "cloudfront_distribution_id" {
  name  = "/${var.project}/cloudfront-distribution-id"
  type  = "String"
  value = aws_cloudfront_distribution.main.id
}

resource "aws_ssm_parameter" "frontend_bucket" {
  name  = "/${var.project}/frontend-bucket"
  type  = "String"
  value = aws_s3_bucket.frontend.bucket
}

resource "aws_ssm_parameter" "cognito_user_pool_id" {
  name  = "/${var.project}/cognito-user-pool-id"
  type  = "String"
  value = aws_cognito_user_pool.main.id
}

resource "aws_ssm_parameter" "cognito_client_id" {
  name  = "/${var.project}/cognito-client-id"
  type  = "String"
  value = aws_cognito_user_pool_client.web.id
}
