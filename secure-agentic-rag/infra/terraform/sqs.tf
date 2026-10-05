# ---------------------------------------------------------------------------
# Amazon SQS Asynchronous Queues & Dead-Letter Queue (DLQ)
# ---------------------------------------------------------------------------

# 1. Dead-Letter Queue (DLQ)
resource "aws_sqs_queue" "dlq" {
  name                      = "${var.project_name}-${var.environment}-dlq"
  message_retention_seconds = 1209600 # 14 days
  sqs_managed_sse_enabled   = true

  tags = {
    Name = "${var.project_name}-${var.environment}-dlq"
  }
}

# 2. Document Ingestion Queue (maxReceiveCount = 3 before moving to DLQ)
resource "aws_sqs_queue" "doc_ingestion" {
  name                       = "${var.project_name}-${var.environment}-doc-ingestion"
  visibility_timeout_seconds = 180    # 3 minutes for parsing and vector embedding
  message_retention_seconds  = 345600 # 4 days
  sqs_managed_sse_enabled    = true

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 3
  })

  tags = {
    Name = "${var.project_name}-${var.environment}-doc-ingestion"
  }
}

# 3. Red-Team Benchmark Queue (visibility timeout 600s for full attack suite)
resource "aws_sqs_queue" "redteam" {
  name                       = "${var.project_name}-${var.environment}-redteam"
  visibility_timeout_seconds = 600    # 10 minutes for 50-attack suite
  message_retention_seconds  = 345600 # 4 days
  sqs_managed_sse_enabled    = true

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 3
  })

  tags = {
    Name = "${var.project_name}-${var.environment}-redteam"
  }
}
