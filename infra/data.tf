data "aws_vpc" "existing" {
  filter {
    name   = "tag:Name"
    values = ["url-shortener-vpc"]
  }
}

data "aws_subnets" "private" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.existing.id]
  }

  tags = {
    "kubernetes.io/role/internal-elb" = "1"
  }
}

data "aws_subnets" "public" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.existing.id]
  }

  tags = {
    "kubernetes.io/role/elb" = "1"
  }
}

data "aws_acm_certificate" "wildcard" {
  provider = aws.us_east_1
  domain   = "*.tommykeyapp.com"
  statuses = ["ISSUED"]
}

data "aws_route53_zone" "main" {
  name = "tommykeyapp.com"
}

data "aws_caller_identity" "current" {}
