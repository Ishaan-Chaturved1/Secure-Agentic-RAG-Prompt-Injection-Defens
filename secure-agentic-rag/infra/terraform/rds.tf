# ---------------------------------------------------------------------------
# Amazon RDS PostgreSQL with pgvector (Private subnets only)
# ---------------------------------------------------------------------------

resource "aws_db_subnet_group" "rds" {
  name        = "${var.project_name}-${var.environment}-rds-subnet-group"
  subnet_ids  = aws_subnet.private[*].id
  description = "Private subnets for RDS PostgreSQL cluster"

  tags = {
    Name = "${var.project_name}-${var.environment}-rds-subnet-group"
  }
}

resource "aws_db_parameter_group" "postgres" {
  name        = "${var.project_name}-${var.environment}-pg16-params"
  family      = "postgres16"
  description = "Parameter group enabling pgvector extension and connection limits"

  tags = {
    Name = "${var.project_name}-${var.environment}-pg16-params"
  }
}

resource "random_password" "db_master_password" {
  length           = 32
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

resource "aws_db_instance" "postgres" {
  identifier     = "${var.project_name}-${var.environment}-db"
  engine         = "postgres"
  engine_version = "16.4"
  instance_class = var.db_instance_class

  allocated_storage     = 20
  max_allocated_storage = 100
  storage_type          = "gp3"
  storage_encrypted     = true

  db_name  = var.db_name
  username = var.db_username
  password = random_password.db_master_password.result

  db_subnet_group_name   = aws_db_subnet_group.rds.name
  parameter_group_name   = aws_db_parameter_group.postgres.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  # Strictly private - NO public access
  publicly_accessible = false
  multi_az            = var.multi_az_db

  # Automated backups and maintenance
  backup_retention_period   = 7
  backup_window             = "03:00-04:00"
  maintenance_window        = "Mon:04:00-Mon:05:00"
  copy_tags_to_snapshot     = true
  deletion_protection       = var.environment == "production" ? true : false
  skip_final_snapshot       = var.environment == "production" ? false : true
  final_snapshot_identifier = "${var.project_name}-${var.environment}-db-final-snapshot"

  tags = {
    Name = "${var.project_name}-${var.environment}-db"
  }
}
