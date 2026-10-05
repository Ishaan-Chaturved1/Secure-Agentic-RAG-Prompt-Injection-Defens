# ---------------------------------------------------------------------------
# AWS Secrets Manager (No plaintext credentials committed to Git)
# ---------------------------------------------------------------------------

resource "random_password" "jwt_secret" {
  length  = 64
  special = false
}

resource "aws_secretsmanager_secret" "app_secrets" {
  name                    = "${var.project_name}/production-secrets"
  description             = "Production database credentials and cryptographic secrets"
  recovery_window_in_days = 7

  tags = {
    Name = "${var.project_name}-secrets"
  }
}

resource "aws_secretsmanager_secret_version" "app_secrets_val" {
  secret_id = aws_secretsmanager_secret.app_secrets.id

  secret_string = jsonencode({
    DATABASE_URL = "postgresql+psycopg2://${var.db_username}:${random_password.db_master_password.result}@${aws_db_instance.postgres.endpoint}/${var.db_name}"
    JWT_SECRET   = random_password.jwt_secret.result
  })
}
