# Weekly digest scheduler
resource "aws_scheduler_schedule" "weekly_digest" {
  name = "${var.project}-weekly-digest"

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression = "cron(0 0 ? * MON *)"

  target {
    arn      = aws_lambda_function.digest.arn
    role_arn = aws_iam_role.scheduler.arn
  }
}

# IAM Role for EventBridge Scheduler
resource "aws_iam_role" "scheduler" {
  name = "${var.project}-scheduler"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "scheduler.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Project = var.project
  }
}

resource "aws_iam_role_policy" "scheduler" {
  name = "${var.project}-scheduler"
  role = aws_iam_role.scheduler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "lambda:InvokeFunction"
        Resource = aws_lambda_function.digest.arn
      }
    ]
  })
}

# ── S3 Upload → Step Functions trigger ──

resource "aws_cloudwatch_event_rule" "receipt_uploaded" {
  name = "${var.project}-receipt-uploaded"

  event_pattern = jsonencode({
    source      = ["aws.s3"]
    detail-type = ["Object Created"]
    detail = {
      bucket = { name = [aws_s3_bucket.receipts.id] }
      object = { key = [{ prefix = "uploads/" }] }
    }
  })

  tags = {
    Project = var.project
  }
}

resource "aws_cloudwatch_event_target" "receipt_sfn" {
  rule     = aws_cloudwatch_event_rule.receipt_uploaded.name
  arn      = aws_sfn_state_machine.receipt_pipeline.arn
  role_arn = aws_iam_role.eventbridge_sfn.arn

  input_transformer {
    input_paths = {
      bucket = "$.detail.bucket.name"
      key    = "$.detail.object.key"
    }
    input_template = <<-EOF
      {
        "bucket": <bucket>,
        "key": <key>
      }
    EOF
  }
}

resource "aws_iam_role" "eventbridge_sfn" {
  name = "${var.project}-eventbridge-sfn"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "events.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Project = var.project
  }
}

resource "aws_iam_role_policy" "eventbridge_sfn" {
  name = "${var.project}-eventbridge-sfn"
  role = aws_iam_role.eventbridge_sfn.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "states:StartExecution"
        Resource = aws_sfn_state_machine.receipt_pipeline.arn
      }
    ]
  })
}

# Lambda permission for EventBridge Scheduler
resource "aws_lambda_permission" "scheduler" {
  statement_id  = "AllowSchedulerInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.digest.function_name
  principal     = "scheduler.amazonaws.com"
  source_arn    = aws_scheduler_schedule.weekly_digest.arn
}
