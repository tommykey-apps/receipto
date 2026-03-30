# Step Functions Express Workflow for receipt processing
resource "aws_sfn_state_machine" "receipt_pipeline" {
  name     = "${var.project}-receipt-pipeline"
  role_arn = aws_iam_role.stepfunctions.arn
  type     = "EXPRESS"

  definition = jsonencode({
    Comment = "Receipt processing pipeline"
    StartAt = "AnalyzeReceipt"
    States = {
      AnalyzeReceipt = {
        Type     = "Task"
        Resource = "arn:aws:states:::aws-sdk:textract:analyzeExpense"
        Parameters = {
          "Document" = {
            "S3Object" = {
              "Bucket.$" = "$.bucket"
              "Name.$"   = "$.key"
            }
          }
        }
        Next = "SaveExpense"
      }
      SaveExpense = {
        Type     = "Task"
        Resource = "arn:aws:states:::dynamodb:putItem"
        Parameters = {
          "TableName" = aws_dynamodb_table.main.name
          "Item" = {
            "pk" = { "S.$" = "$.userId" }
            "sk" = { "S.$" = "$.expenseId" }
          }
        }
        Next = "NotifyUser"
      }
      NotifyUser = {
        Type     = "Task"
        Resource = "arn:aws:states:::sns:publish"
        Parameters = {
          "TopicArn" = aws_sns_topic.alerts.arn
          "Message.$" = "$.message"
        }
        End = true
      }
    }
  })

  tags = {
    Project = var.project
  }
}

# IAM Role for Step Functions
resource "aws_iam_role" "stepfunctions" {
  name = "${var.project}-stepfunctions"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "states.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Project = var.project
  }
}

resource "aws_iam_role_policy" "stepfunctions" {
  name = "${var.project}-stepfunctions"
  role = aws_iam_role.stepfunctions.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "textract:AnalyzeExpense",
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
        ]
        Resource = aws_dynamodb_table.main.arn
      },
      {
        Effect   = "Allow"
        Action   = "sns:Publish"
        Resource = aws_sns_topic.alerts.arn
      },
      {
        Effect   = "Allow"
        Action   = "lambda:InvokeFunction"
        Resource = aws_lambda_function.api.arn
      },
      {
        Effect = "Allow"
        Action = "s3:GetObject"
        Resource = "${aws_s3_bucket.receipts.arn}/*"
      }
    ]
  })
}
