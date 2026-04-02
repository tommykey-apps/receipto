# Receipts bucket
resource "aws_s3_bucket" "receipts" {
  bucket = "${var.project}-receipts-${data.aws_caller_identity.current.account_id}"

  tags = {
    Project = var.project
  }
}

resource "aws_s3_bucket_public_access_block" "receipts" {
  bucket = aws_s3_bucket.receipts.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "receipts" {
  bucket = aws_s3_bucket.receipts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_cors_configuration" "receipts" {
  bucket = aws_s3_bucket.receipts.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["PUT"]
    allowed_origins = ["*"]
    max_age_seconds = 3600
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "receipts" {
  bucket = aws_s3_bucket.receipts.id

  rule {
    id     = "transition-to-intelligent-tiering"
    status = "Enabled"

    filter {}

    transition {
      days          = 365
      storage_class = "INTELLIGENT_TIERING"
    }
  }
}

# S3 → EventBridge notifications (for Step Functions trigger)
resource "aws_s3_bucket_notification" "receipts" {
  bucket      = aws_s3_bucket.receipts.id
  eventbridge = true
}

# ── Versioning (required for S3 Replication) ──

resource "aws_s3_bucket_versioning" "receipts" {
  bucket = aws_s3_bucket.receipts.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_versioning" "receipts_us" {
  provider = aws.us_east_1
  bucket   = aws_s3_bucket.receipts_us.id

  versioning_configuration {
    status = "Enabled"
  }
}

# ── us-east-1 Receipts bucket (for Textract AnalyzeExpense) ──

resource "aws_s3_bucket" "receipts_us" {
  provider = aws.us_east_1
  bucket   = "${var.project}-receipts-us-${data.aws_caller_identity.current.account_id}"

  tags = {
    Project = var.project
  }
}

resource "aws_s3_bucket_public_access_block" "receipts_us" {
  provider = aws.us_east_1
  bucket   = aws_s3_bucket.receipts_us.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ── S3 Cross-Region Replication: ap-northeast-1 → us-east-1 ──

resource "aws_iam_role" "s3_replication" {
  name = "${var.project}-s3-replication"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "s3.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Project = var.project
  }
}

resource "aws_iam_role_policy" "s3_replication" {
  name = "${var.project}-s3-replication"
  role = aws_iam_role.s3_replication.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetReplicationConfiguration",
          "s3:ListBucket",
        ]
        Resource = aws_s3_bucket.receipts.arn
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObjectVersionForReplication",
          "s3:GetObjectVersionAcl",
          "s3:GetObjectVersionTagging",
        ]
        Resource = "${aws_s3_bucket.receipts.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ReplicateObject",
          "s3:ReplicateDelete",
          "s3:ReplicateTags",
        ]
        Resource = "${aws_s3_bucket.receipts_us.arn}/*"
      }
    ]
  })
}

resource "aws_s3_bucket_replication_configuration" "receipts" {
  depends_on = [
    aws_s3_bucket_versioning.receipts,
    aws_s3_bucket_versioning.receipts_us,
  ]

  role   = aws_iam_role.s3_replication.arn
  bucket = aws_s3_bucket.receipts.id

  rule {
    id     = "replicate-uploads"
    status = "Enabled"

    filter {
      prefix = "uploads/"
    }

    destination {
      bucket        = aws_s3_bucket.receipts_us.arn
      storage_class = "STANDARD"
    }
  }
}

# Frontend bucket
resource "aws_s3_bucket" "frontend" {
  bucket        = "${var.project}-frontend-${data.aws_caller_identity.current.account_id}"
  force_destroy = true

  tags = {
    Project = var.project
  }
}

resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
