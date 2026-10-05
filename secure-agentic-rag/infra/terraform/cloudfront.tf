# ---------------------------------------------------------------------------
# CloudFront Distribution for Frontend SPA (S3 Origin with OAC)
# Serves React frontend from private S3 bucket via CDN edge locations.
# All backend API paths are proxied to the ALB as a full reverse proxy.
# ---------------------------------------------------------------------------

# 1. Origin Access Control — modern S3-to-CloudFront auth (replaces legacy OAI)
resource "aws_cloudfront_origin_access_control" "frontend" {
  name                              = "${var.project_name}-${var.environment}-frontend-oac"
  description                       = "OAC for frontend S3 bucket"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# Backend API path patterns that CloudFront proxies to the ALB
locals {
  api_path_patterns = [
    "/api/*",
    "/api",
  ]

  backend_path_patterns = [
    "/health",
    "/auth/*",
    "/query",
    "/documents",
    "/documents/*",
    "/workspaces",
    "/workspaces/*",
    "/user/*",
    "/red-team/*",
    "/security/*",
    "/audit/*",
  ]
}

# 1b. CloudFront Function: strip /api prefix before forwarding to ALB
resource "aws_cloudfront_function" "api_rewrite" {
  name    = "${var.project_name}-${var.environment}-api-rewrite"
  runtime = "cloudfront-js-2.0"
  comment = "Strip /api prefix from request URI before routing to ALB"
  publish = true
  code    = <<-EOT
function handler(event) {
    var request = event.request;
    var uri = request.uri;
    if (uri.startsWith('/api/')) {
        request.uri = uri.replace(/^\/api/, '');
    } else if (uri === '/api') {
        request.uri = '/';
    }
    return request;
}
EOT
}


# 2. CloudFront Distribution
resource "aws_cloudfront_distribution" "frontend" {
  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"
  comment             = "${var.project_name} ${var.environment} frontend"
  price_class         = "PriceClass_100" # US + Europe edges (cost-effective)

  # --- S3 Origin (static assets) ---
  origin {
    domain_name              = aws_s3_bucket.frontend.bucket_regional_domain_name
    origin_id                = "s3-frontend"
    origin_access_control_id = aws_cloudfront_origin_access_control.frontend.id
  }

  # --- ALB Origin (API reverse proxy) ---
  origin {
    domain_name = aws_lb.main.dns_name
    origin_id   = "alb-backend"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  # --- Default behavior: S3 static assets ---
  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "s3-frontend"
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = false

      cookies {
        forward = "none"
      }
    }

    min_ttl     = 0
    default_ttl = 86400
    max_ttl     = 31536000
    compress    = true
  }

  # --- /api and /api/* behaviors: rewrite URI and proxy to ALB ---
  dynamic "ordered_cache_behavior" {
    for_each = local.api_path_patterns
    content {
      path_pattern           = ordered_cache_behavior.value
      allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
      cached_methods         = ["GET", "HEAD"]
      target_origin_id       = "alb-backend"
      viewer_protocol_policy = "redirect-to-https"

      forwarded_values {
        query_string = true
        headers      = ["Authorization", "Origin", "Host"]

        cookies {
          forward = "all"
        }
      }

      min_ttl     = 0
      default_ttl = 0
      max_ttl     = 0
      compress    = true

      function_association {
        event_type   = "viewer-request"
        function_arn = aws_cloudfront_function.api_rewrite.arn
      }
    }
  }

  # --- Backend direct API behaviors: proxy each path pattern to ALB ---
  dynamic "ordered_cache_behavior" {
    for_each = local.backend_path_patterns
    content {
      path_pattern           = ordered_cache_behavior.value
      allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
      cached_methods         = ["GET", "HEAD"]
      target_origin_id       = "alb-backend"
      viewer_protocol_policy = "redirect-to-https"

      forwarded_values {
        query_string = true
        headers      = ["Authorization", "Origin", "Host"]

        cookies {
          forward = "all"
        }
      }

      min_ttl     = 0
      default_ttl = 0
      max_ttl     = 0
      compress    = true
    }
  }

  # --- SPA fallback: all 403/404 → index.html for client-side routing ---
  custom_error_response {
    error_code            = 403
    response_code         = 200
    response_page_path    = "/index.html"
    error_caching_min_ttl = 10
  }

  custom_error_response {
    error_code            = 404
    response_code         = 200
    response_page_path    = "/index.html"
    error_caching_min_ttl = 10
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-cdn"
  }
}

# 3. S3 Bucket Policy — grant CloudFront OAC read access to the frontend bucket
resource "aws_s3_bucket_policy" "frontend_cdn_access" {
  bucket = aws_s3_bucket.frontend.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowCloudFrontServicePrincipalReadOnly"
        Effect = "Allow"
        Principal = {
          Service = "cloudfront.amazonaws.com"
        }
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.frontend.arn}/*"
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = aws_cloudfront_distribution.frontend.arn
          }
        }
      }
    ]
  })
}

