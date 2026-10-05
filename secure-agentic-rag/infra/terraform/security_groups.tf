# ---------------------------------------------------------------------------
# Security Groups with Least Privilege (Zero 0.0.0.0/0 on internal data stores)
# ---------------------------------------------------------------------------

# 1. ALB Security Group (Public facing entry point)
resource "aws_security_group" "alb" {
  name        = "${var.project_name}-${var.environment}-alb-sg"
  description = "Controls public HTTPS/HTTP ingress to Application Load Balancer"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "Allow HTTPS from anywhere"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Allow HTTP for redirect to HTTPS"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Allow outbound traffic to VPC"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-alb-sg"
  }
}

# 2. ECS Backend Security Group (Private subnet only)
resource "aws_security_group" "ecs_backend" {
  name        = "${var.project_name}-${var.environment}-ecs-backend-sg"
  description = "Allows ingress only from ALB on container port"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "Allow traffic strictly from ALB target group"
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    description = "Allow outbound internet access via NAT gateway for AWS APIs"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-ecs-backend-sg"
  }
}

# 3. ECS Worker Security Group (Private subnet only - no public ingress)
resource "aws_security_group" "ecs_worker" {
  name        = "${var.project_name}-${var.environment}-ecs-worker-sg"
  description = "Background task worker with no inbound access"
  vpc_id      = aws_vpc.main.id

  egress {
    description = "Allow outbound internet access via NAT gateway to poll SQS and S3"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-ecs-worker-sg"
  }
}

# 4. RDS PostgreSQL Security Group (Strictly isolated - NO 0.0.0.0/0)
resource "aws_security_group" "rds" {
  name        = "${var.project_name}-${var.environment}-rds-sg"
  description = "Controls PostgreSQL ingress strictly from authorized ECS tasks"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "PostgreSQL access from ECS Backend API"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_backend.id]
  }

  ingress {
    description     = "PostgreSQL access from ECS Worker task"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_worker.id]
  }

  egress {
    description = "Allow outbound response traffic within VPC"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [var.vpc_cidr]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-rds-sg"
  }
}

# 5. ElastiCache Redis Security Group (Strictly isolated - NO 0.0.0.0/0)
resource "aws_security_group" "redis" {
  name        = "${var.project_name}-${var.environment}-redis-sg"
  description = "Controls Redis ingress strictly from authorized ECS tasks"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "Redis access from ECS Backend API"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_backend.id]
  }

  ingress {
    description     = "Redis access from ECS Worker task"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_worker.id]
  }

  egress {
    description = "Allow outbound response traffic within VPC"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [var.vpc_cidr]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-redis-sg"
  }
}
