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

# Lambda permission for EventBridge Scheduler
resource "aws_lambda_permission" "scheduler" {
  statement_id  = "AllowSchedulerInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.digest.function_name
  principal     = "scheduler.amazonaws.com"
  source_arn    = aws_scheduler_schedule.weekly_digest.arn
}
