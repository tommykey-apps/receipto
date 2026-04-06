data "aws_acm_certificate" "wildcard" {
  provider = aws.us_east_1
  domain   = "*.tommykeyapp.com"
  statuses = ["ISSUED"]
}

data "aws_route53_zone" "main" {
  name = "tommykeyapp.com"
}

data "aws_caller_identity" "current" {}
