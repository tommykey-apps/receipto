# Step Functions for receipt processing pipeline
resource "aws_sfn_state_machine" "receipt_pipeline" {
  name     = "${var.project}-receipt-pipeline"
  role_arn = aws_iam_role.stepfunctions.arn
  type     = "STANDARD"

  definition = jsonencode({
    Comment = "Receipt OCR pipeline: validate → OCR → categorize → save OCR result to receipt"
    StartAt = "ParseS3Key"
    States = {
      ParseS3Key = {
        Type = "Pass"
        Parameters = {
          "bucket.$"     = "$.bucket"
          "s3_key.$"     = "$.key"
          "user_id.$"    = "States.ArrayGetItem(States.StringSplit($.key, '/'), 1)"
          "receipt_id.$" = "States.ArrayGetItem(States.StringSplit($.key, '/'), 2)"
        }
        Next = "ValidateReceipt"
      }
      ValidateReceipt = {
        Type     = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          "FunctionName" = aws_lambda_function.pipeline["receipt-validator"].arn
          "Payload.$"    = "$"
        }
        ResultPath  = "$"
        ResultSelector = { "result.$" = "$.Payload" }
        OutputPath  = "$.result"
        Next        = "CheckValid"
      }
      CheckValid = {
        Type = "Choice"
        Choices = [
          {
            Variable     = "$.valid"
            BooleanEquals = false
            Next         = "MarkFailed"
          }
        ]
        Default = "ProcessOCR"
      }
      ProcessOCR = {
        Type     = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          "FunctionName" = aws_lambda_function.pipeline["ocr-processor"].arn
          "Payload.$"    = "$"
        }
        ResultPath  = "$"
        ResultSelector = { "result.$" = "$.Payload" }
        OutputPath  = "$.result"
        Next        = "CheckOCR"
      }
      CheckOCR = {
        Type = "Choice"
        Choices = [
          {
            Variable      = "$.ocr_success"
            BooleanEquals = false
            Next          = "MarkFailed"
          }
        ]
        Default = "Categorize"
      }
      Categorize = {
        Type     = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          "FunctionName" = aws_lambda_function.pipeline["categorizer"].arn
          "Payload.$"    = "$"
        }
        ResultPath  = "$"
        ResultSelector = { "result.$" = "$.Payload" }
        OutputPath  = "$.result"
        Next        = "SaveExpense"
      }
      SaveExpense = {
        Type     = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          "FunctionName" = aws_lambda_function.pipeline["expense-saver"].arn
          "Payload.$"    = "$"
        }
        ResultPath  = "$"
        ResultSelector = { "result.$" = "$.Payload" }
        OutputPath  = "$.result"
        End         = true
      }
      MarkFailed = {
        Type     = "Task"
        Resource = "arn:aws:states:::dynamodb:updateItem"
        Parameters = {
          "TableName"  = aws_dynamodb_table.main.name
          "Key" = {
            "pk" = { "S.$" = "States.Format('USER#{}', $.user_id)" }
            "sk" = { "S.$" = "States.Format('RCV#{}', $.receipt_id)" }
          }
          "UpdateExpression"          = "SET #s = :failed"
          "ExpressionAttributeNames"  = { "#s" = "status" }
          "ExpressionAttributeValues" = { ":failed" = { "S" = "failed" } }
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
        Effect   = "Allow"
        Action   = "lambda:InvokeFunction"
        Resource = [for fn in aws_lambda_function.pipeline : fn.arn]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:UpdateItem",
        ]
        Resource = aws_dynamodb_table.main.arn
      }
    ]
  })
}
