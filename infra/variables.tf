variable "project" {
  description = "Project name"
  type        = string
  default     = "expense-tracker"
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "ap-northeast-1"
}

variable "alert_email" {
  description = "Email address for alert notifications"
  type        = string
  sensitive   = true
}
