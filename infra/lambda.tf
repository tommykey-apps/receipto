# Placeholder zip for Lambda deployment
data "archive_file" "lambda_placeholder" {
  type        = "zip"
  output_path = "${path.module}/lambda-placeholder.zip"

  source {
    content  = "# placeholder"
    filename = "main.py"
  }
}

data "archive_file" "pipeline_placeholder" {
  type        = "zip"
  output_path = "${path.module}/lambda-pipeline-placeholder.zip"

  source {
    content  = "# placeholder"
    filename = "main.py"
  }
}

data "archive_file" "digest_placeholder" {
  type        = "zip"
  output_path = "${path.module}/lambda-digest-placeholder.zip"

  source {
    content  = "# placeholder"
    filename = "main.py"
  }
}

# API Lambda
resource "aws_lambda_function" "api" {
  function_name = "${var.project}-api"
  role          = aws_iam_role.lambda_api.arn
  handler       = "main.handler"
  runtime       = "python3.12"
  timeout       = 30
  memory_size   = 128

  filename         = data.archive_file.lambda_placeholder.output_path
  source_code_hash = data.archive_file.lambda_placeholder.output_base64sha256

  environment {
    variables = {
      DYNAMODB_TABLE       = aws_dynamodb_table.main.name
      RECEIPTS_BUCKET      = aws_s3_bucket.receipts.id
      COGNITO_USER_POOL_ID = aws_cognito_user_pool.main.id
      COGNITO_CLIENT_ID    = aws_cognito_user_pool_client.web.id
    }
  }

  tags = {
    Project = var.project
  }
}

# IAM Role for API Lambda
resource "aws_iam_role" "lambda_api" {
  name = "${var.project}-lambda-api"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Project = var.project
  }
}

resource "aws_iam_role_policy_attachment" "lambda_api_basic" {
  role       = aws_iam_role.lambda_api.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "lambda_api_dynamodb" {
  name = "${var.project}-lambda-api-dynamodb"
  role = aws_iam_role.lambda_api.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
        ]
        Resource = [
          aws_dynamodb_table.main.arn,
          "${aws_dynamodb_table.main.arn}/index/*",
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_api_s3" {
  name = "${var.project}-lambda-api-s3"
  role = aws_iam_role.lambda_api.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
        ]
        Resource = "${aws_s3_bucket.receipts.arn}/*"
      }
    ]
  })
}

# Permission for API Gateway to invoke Lambda
resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}

# Digest Lambda
resource "aws_lambda_function" "digest" {
  function_name = "${var.project}-digest"
  role          = aws_iam_role.lambda_digest.arn
  handler       = "main.handler"
  runtime       = "python3.12"
  timeout       = 60
  memory_size   = 128

  filename         = data.archive_file.digest_placeholder.output_path
  source_code_hash = data.archive_file.digest_placeholder.output_base64sha256

  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.main.name
      SNS_TOPIC_ARN  = aws_sns_topic.alerts.arn
      SES_FROM_EMAIL = "noreply@tommykeyapp.com"
    }
  }

  tags = {
    Project = var.project
  }
}

# IAM Role for Digest Lambda
resource "aws_iam_role" "lambda_digest" {
  name = "${var.project}-lambda-digest"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Project = var.project
  }
}

resource "aws_iam_role_policy_attachment" "lambda_digest_basic" {
  role       = aws_iam_role.lambda_digest.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "lambda_digest_dynamodb" {
  name = "${var.project}-lambda-digest-dynamodb"
  role = aws_iam_role.lambda_digest.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:Query",
        ]
        Resource = [
          aws_dynamodb_table.main.arn,
          "${aws_dynamodb_table.main.arn}/index/*",
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_digest_sns" {
  name = "${var.project}-lambda-digest-sns"
  role = aws_iam_role.lambda_digest.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "sns:Publish"
        Resource = aws_sns_topic.alerts.arn
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_digest_ses" {
  name = "${var.project}-lambda-digest-ses"
  role = aws_iam_role.lambda_digest.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "ses:SendEmail"
        Resource = "*"
      }
    ]
  })
}

# ── Receipt Pipeline Lambdas ──

locals {
  pipeline_functions = {
    receipt-validator = { handler = "receipt_validator.handler", timeout = 30 }
    ocr-processor     = { handler = "ocr_processor.handler", timeout = 60 }
    categorizer       = { handler = "categorizer.handler", timeout = 10 }
    expense-saver     = { handler = "expense_saver.handler", timeout = 30 }
    budget-checker    = { handler = "budget_checker.handler", timeout = 30 }
    notifier          = { handler = "notifier.handler", timeout = 30 }
  }
}

resource "aws_lambda_function" "pipeline" {
  for_each = local.pipeline_functions

  function_name = "${var.project}-${each.key}"
  role          = aws_iam_role.lambda_pipeline.arn
  handler       = each.value.handler
  runtime       = "python3.12"
  timeout       = each.value.timeout
  memory_size   = 128

  filename         = data.archive_file.pipeline_placeholder.output_path
  source_code_hash = data.archive_file.pipeline_placeholder.output_base64sha256

  environment {
    variables = {
      DYNAMODB_TABLE         = aws_dynamodb_table.main.name
      BUDGET_ALERT_TOPIC_ARN = aws_sns_topic.alerts.arn
      RECEIPTS_BUCKET_US     = aws_s3_bucket.receipts_us.id
      BEDROCK_MODEL_ID       = "apac.anthropic.claude-sonnet-4-20250514-v1:0"
    }
  }

  tags = {
    Project = var.project
  }
}

# IAM Role for Pipeline Lambdas (shared)
resource "aws_iam_role" "lambda_pipeline" {
  name = "${var.project}-lambda-pipeline"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Project = var.project
  }
}

resource "aws_iam_role_policy_attachment" "lambda_pipeline_basic" {
  role       = aws_iam_role.lambda_pipeline.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "lambda_pipeline" {
  name = "${var.project}-lambda-pipeline"
  role = aws_iam_role.lambda_pipeline.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:HeadObject",
        ]
        Resource = "${aws_s3_bucket.receipts.arn}/*"
      },
      {
        Effect = "Allow"
        Action = "bedrock:InvokeModel"
        Resource = [
          "arn:aws:bedrock:ap-northeast-1::foundation-model/anthropic.*",
          "arn:aws:bedrock:*::inference-profile/apac.anthropic.*",
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:Query",
        ]
        Resource = [
          aws_dynamodb_table.main.arn,
          "${aws_dynamodb_table.main.arn}/index/*",
        ]
      },
      {
        Effect   = "Allow"
        Action   = "sns:Publish"
        Resource = aws_sns_topic.alerts.arn
      }
    ]
  })
}

