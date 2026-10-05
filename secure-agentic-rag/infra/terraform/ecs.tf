# ---------------------------------------------------------------------------
# Amazon ECR Repository & ECS Fargate Cluster / Services
# ---------------------------------------------------------------------------

# 1. ECR Repository for container images
resource "aws_ecr_repository" "app" {
  name                 = "${var.project_name}-app"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = {
    Name = "${var.project_name}-ecr"
  }
}

# Retain only last 10 images to control storage costs
resource "aws_ecr_lifecycle_policy" "app" {
  repository = aws_ecr_repository.app.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 10
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# 2. ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-${var.environment}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-cluster"
  }
}

# 3. ECS Task Definition: Backend API
resource "aws_ecs_task_definition" "backend" {
  family                   = "${var.project_name}-${var.environment}-backend"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.backend_cpu
  memory                   = var.backend_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_backend_task.arn

  container_definitions = jsonencode([
    {
      name      = "backend-api"
      image     = "${aws_ecr_repository.app.repository_url}:latest"
      command   = ["sh", "-c", "python -c 'p = \"/app/app/db/database.py\"; c = open(p).read().replace(\"self._conn.commit()\", \"getattr(self._raw_conn, \\\"commit\\\", lambda: None)(); self._conn.commit()\").replace(\"self._conn.rollback()\", \"getattr(self._raw_conn, \\\"rollback\\\", lambda: None)(); self._conn.rollback()\"); open(p, \"w\").write(c)'; pip install --user --no-cache-dir pypdf; exec gunicorn -c gunicorn_conf.py app.main:app"]
      essential = true


      portMappings = [
        {
          containerPort = 8000
          hostPort      = 8000
          protocol      = "tcp"
        }
      ]

      environment = [
        { name = "ENVIRONMENT", value = var.environment },
        { name = "HOST", value = "0.0.0.0" },
        { name = "PORT", value = "8000" },
        { name = "RAG_MODE", value = "hardened" },

        { name = "STORAGE_BACKEND", value = "s3" },
        { name = "S3_BUCKET", value = aws_s3_bucket.documents.id },
        { name = "S3_REGION", value = var.aws_region },

        { name = "VECTOR_BACKEND", value = "pgvector" },
        { name = "RAG_VECTOR_STORE", value = "pgvector" },

        { name = "QUEUE_BACKEND", value = "sqs" },
        { name = "SQS_DOCUMENT_QUEUE_URL", value = aws_sqs_queue.doc_ingestion.url },
        { name = "SQS_REDTEAM_QUEUE_URL", value = aws_sqs_queue.redteam.url },
        { name = "SQS_DLQ_URL", value = aws_sqs_queue.dlq.url },

        { name = "REDIS_URL", value = "redis://${aws_elasticache_cluster.redis.cache_nodes[0].address}:6379/0" },
        { name = "RATE_LIMIT_ENABLED", value = "true" },

        # Explicit CORS configuration for ALB and CloudFront origins (wildcard '*' is forbidden in production)
        { name = "CORS_ALLOWED_ORIGINS", value = "http://${aws_lb.main.dns_name},https://${aws_lb.main.dns_name},https://${aws_cloudfront_distribution.frontend.domain_name}" },

        { name = "LOG_FORMAT", value = "json" },
        { name = "LOG_LEVEL", value = "INFO" },

        { name = "LLM_PROVIDER", value = "bedrock" },
        { name = "BEDROCK_MODEL_ID", value = "anthropic.claude-3-haiku-20240307-v1:0" },
        { name = "BEDROCK_REGION", value = var.aws_region }
      ]

      secrets = [
        {
          name      = "DATABASE_URL"
          valueFrom = "${aws_secretsmanager_secret.app_secrets.arn}:DATABASE_URL::"
        },
        {
          name      = "JWT_SECRET"
          valueFrom = "${aws_secretsmanager_secret.app_secrets.arn}:JWT_SECRET::"
        }
      ]

      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 15
      }

      logConfiguration = {
        logDriver = "awslogs"

        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.backend.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "backend"
        }
      }
    }
  ])
}

# 4. ECS Service: Backend API
# Backend runs in private subnets behind the ALB
resource "aws_ecs_service" "backend" {
  name            = "${var.project_name}-${var.environment}-backend"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = var.backend_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.ecs_backend.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.backend.arn
    container_name   = "backend-api"
    container_port   = 8000
  }

  # HTTP ALB listener is currently used because no custom domain exists.
  depends_on = [
    aws_lb_listener.http,
    aws_iam_role_policy.backend_least_privilege
  ]
}

# 5. ECS Task Definition: Worker
resource "aws_ecs_task_definition" "worker" {
  family                   = "${var.project_name}-${var.environment}-worker"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.worker_cpu
  memory                   = var.worker_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_worker_task.arn

  container_definitions = jsonencode([
    {
      name      = "worker"
      image     = "${aws_ecr_repository.app.repository_url}:latest"
      command   = ["sh", "-c", "python -c 'p = \"/app/app/db/database.py\"; c = open(p).read().replace(\"self._conn.commit()\", \"getattr(self._raw_conn, \\\"commit\\\", lambda: None)(); self._conn.commit()\").replace(\"self._conn.rollback()\", \"getattr(self._raw_conn, \\\"rollback\\\", lambda: None)(); self._conn.rollback()\"); open(p, \"w\").write(c)'; pip install --user --no-cache-dir pypdf; exec python -m app.worker"]
      essential = true

      environment = [
        { name = "ENVIRONMENT", value = var.environment },
        { name = "RAG_MODE", value = "hardened" },

        { name = "STORAGE_BACKEND", value = "s3" },
        { name = "S3_BUCKET", value = aws_s3_bucket.documents.id },
        { name = "S3_REGION", value = var.aws_region },

        { name = "VECTOR_BACKEND", value = "pgvector" },
        { name = "RAG_VECTOR_STORE", value = "pgvector" },

        { name = "QUEUE_BACKEND", value = "sqs" },
        { name = "SQS_DOCUMENT_QUEUE_URL", value = aws_sqs_queue.doc_ingestion.url },
        { name = "SQS_REDTEAM_QUEUE_URL", value = aws_sqs_queue.redteam.url },
        { name = "SQS_DLQ_URL", value = aws_sqs_queue.dlq.url },

        { name = "REDIS_URL", value = "redis://${aws_elasticache_cluster.redis.cache_nodes[0].address}:6379/0" },

        { name = "LOG_FORMAT", value = "json" },
        { name = "LOG_LEVEL", value = "INFO" },

        { name = "LLM_PROVIDER", value = "bedrock" },
        { name = "BEDROCK_MODEL_ID", value = "anthropic.claude-3-haiku-20240307-v1:0" },
        { name = "BEDROCK_REGION", value = var.aws_region }
      ]

      secrets = [
        {
          name      = "DATABASE_URL"
          valueFrom = "${aws_secretsmanager_secret.app_secrets.arn}:DATABASE_URL::"
        },
        {
          name      = "JWT_SECRET"
          valueFrom = "${aws_secretsmanager_secret.app_secrets.arn}:JWT_SECRET::"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"

        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.worker.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "worker"
        }
      }
    }
  ])
}

# 6. ECS Service: Worker
# Worker runs in private subnets and consumes SQS jobs.
resource "aws_ecs_service" "worker" {
  name            = "${var.project_name}-${var.environment}-worker"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.worker.arn
  desired_count   = var.worker_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.ecs_worker.id]
    assign_public_ip = false
  }

  depends_on = [
    aws_iam_role_policy.worker_least_privilege
  ]
}