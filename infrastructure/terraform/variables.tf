variable "aws_region" {
  type        = string
  description = "AWS region for the regional workload."
  default     = "us-east-1"
}

variable "environment" {
  type        = string
  description = "Isolated environment name."
  validation {
    condition     = contains(["staging", "production"], var.environment)
    error_message = "environment must be staging or production"
  }
}

variable "image_uri" {
  type        = string
  description = "Immutable ECR image URI including digest."
  validation {
    condition     = strcontains(var.image_uri, "@sha256:")
    error_message = "image_uri must be pinned by sha256 digest"
  }
}

variable "desired_count" {
  type    = number
  default = 2
}

variable "municipal_imports_enabled" {
  type        = bool
  description = "Enable the governed municipal import API only after source-rights and staging approval."
  default     = false
}

variable "municipal_max_upload_bytes" {
  type        = number
  description = "Maximum accepted municipal feed upload in bytes."
  default     = 5242880
  validation {
    condition     = var.municipal_max_upload_bytes >= 1024 && var.municipal_max_upload_bytes <= 10485760
    error_message = "municipal_max_upload_bytes must be between 1024 and 10485760"
  }
}

variable "billing_enabled" {
  type        = bool
  description = "Enable store verification only after store products and the gateway are approved."
  default     = false
  validation {
    condition = !var.billing_enabled || (
      startswith(var.billing_gateway_url, "https://") &&
      can(regex("^arn:aws[a-z-]*:secretsmanager:", var.billing_gateway_token_secret_arn)) &&
      (var.apple_premium_product_id != "" || var.google_premium_product_id != "")
    )
    error_message = "billing_enabled requires an HTTPS gateway, token secret ARN, and at least one store product ID"
  }
}

variable "billing_gateway_url" {
  type        = string
  description = "Exact HTTPS store-verification gateway endpoint; empty while billing is disabled."
  default     = ""
}

variable "billing_gateway_token_secret_arn" {
  type        = string
  description = "Secrets Manager ARN containing only the verification-gateway bearer token."
  default     = ""
}

variable "apple_premium_product_id" {
  type        = string
  description = "App Store Connect product identifier approved for the premium entitlement."
  default     = ""
}

variable "google_premium_product_id" {
  type        = string
  description = "Google Play product identifier approved for the premium entitlement."
  default     = ""
}

variable "observability_provider" {
  type        = string
  description = "Provider-neutral telemetry mode. OpenTelemetry requires an injected SDK/exporter."
  default     = "memory"
  validation {
    condition     = contains(["disabled", "memory", "opentelemetry"], var.observability_provider)
    error_message = "observability_provider must be disabled, memory, or opentelemetry"
  }
}

variable "observability_export_enabled" {
  type        = bool
  description = "Enable OTLP export only after the collector and explicit egress are approved."
  default     = false
  validation {
    condition = !var.observability_export_enabled || (
      var.observability_provider == "opentelemetry" &&
      startswith(var.observability_otlp_endpoint, "https://")
    )
    error_message = "observability export requires the opentelemetry provider and an HTTPS endpoint"
  }
}

variable "observability_otlp_endpoint" {
  type        = string
  description = "Approved HTTPS OTLP collector endpoint; empty while export is disabled."
  default     = ""
}

variable "product_analytics_enabled" {
  type        = bool
  description = "Global opt-in analytics gate; individual user consent remains mandatory."
  default     = false
  validation {
    condition     = !var.product_analytics_enabled || var.product_analytics_provider == "external"
    error_message = "enabled product analytics requires the external provider in deployed environments"
  }
}

variable "product_analytics_provider" {
  type        = string
  description = "Product analytics sink; external remains unavailable until an adapter is injected."
  default     = "disabled"
  validation {
    condition     = contains(["disabled", "memory", "external"], var.product_analytics_provider)
    error_message = "product_analytics_provider must be disabled, memory, or external"
  }
}

variable "product_analytics_retention_days" {
  type        = number
  description = "Maximum product-event retention; legal approval may reduce this value."
  default     = 30
  validation {
    condition     = var.product_analytics_retention_days >= 1 && var.product_analytics_retention_days <= 90
    error_message = "product_analytics_retention_days must be between 1 and 90"
  }
}

variable "alarm_email" {
  type        = string
  description = "Optional operational alert email."
  default     = ""
}

variable "smtp_host" {
  type        = string
  description = "SMTP host used for verification and recovery messages."
  validation {
    condition     = length(trimspace(var.smtp_host)) > 0
    error_message = "smtp_host cannot be empty"
  }
}

variable "smtp_username" {
  type        = string
  description = "SMTP account name; the password remains in Secrets Manager."
  validation {
    condition     = length(trimspace(var.smtp_username)) > 0
    error_message = "smtp_username cannot be empty"
  }
}

variable "smtp_password_secret_arn" {
  type        = string
  description = "ARN of an existing Secrets Manager secret containing only the SMTP password."
  validation {
    condition     = can(regex("^arn:aws[a-z-]*:secretsmanager:", var.smtp_password_secret_arn))
    error_message = "smtp_password_secret_arn must be a Secrets Manager ARN"
  }
}

variable "email_from" {
  type        = string
  description = "Verified sender address."
  default     = "no-reply@parkshield.ai"
  validation {
    condition     = can(regex("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$", var.email_from))
    error_message = "email_from must be an email address"
  }
}

variable "push_provider_url" {
  type        = string
  description = "HTTPS endpoint for the production push gateway."
  validation {
    condition     = startswith(var.push_provider_url, "https://")
    error_message = "push_provider_url must use HTTPS"
  }
}

variable "push_provider_token_secret_arn" {
  type        = string
  description = "ARN of an existing Secrets Manager secret containing only the push token."
  validation {
    condition     = can(regex("^arn:aws[a-z-]*:secretsmanager:", var.push_provider_token_secret_arn))
    error_message = "push_provider_token_secret_arn must be a Secrets Manager ARN"
  }
}

variable "tow_provider_url" {
  type        = string
  description = "HTTPS endpoint for the contracted municipal tow lookup gateway."
  validation {
    condition     = startswith(var.tow_provider_url, "https://")
    error_message = "tow_provider_url must use HTTPS"
  }
}

variable "tow_provider_token_secret_arn" {
  type        = string
  description = "ARN of an existing Secrets Manager secret containing only the tow token."
  validation {
    condition     = can(regex("^arn:aws[a-z-]*:secretsmanager:", var.tow_provider_token_secret_arn))
    error_message = "tow_provider_token_secret_arn must be a Secrets Manager ARN"
  }
}

variable "provider_egress_cidrs" {
  type        = list(string)
  description = "Explicit SMTP, push, and tow-provider ranges; unrestricted internet is rejected."
  validation {
    condition = (
      length(var.provider_egress_cidrs) > 0 &&
      alltrue([for cidr in var.provider_egress_cidrs : can(cidrhost(cidr, 0))]) &&
      !contains(var.provider_egress_cidrs, "0.0.0.0/0")
    )
    error_message = "provider_egress_cidrs must contain valid explicit CIDRs and cannot include 0.0.0.0/0"
  }
}

variable "origin_domain_name" {
  type        = string
  description = "Private origin hostname covered by the ALB certificate."
  validation {
    condition     = length(split(".", var.origin_domain_name)) >= 2
    error_message = "origin_domain_name must be a DNS hostname"
  }
}

variable "route53_zone_id" {
  type        = string
  description = "Existing Route 53 public hosted-zone ID for origin_domain_name."
  validation {
    condition     = can(regex("^Z[A-Z0-9]+$", var.route53_zone_id))
    error_message = "route53_zone_id must be a Route 53 hosted-zone ID"
  }
}

variable "origin_certificate_arn" {
  type        = string
  description = "Regional ACM certificate ARN covering origin_domain_name."
  validation {
    condition     = can(regex("^arn:aws[a-z-]*:acm:", var.origin_certificate_arn))
    error_message = "origin_certificate_arn must be an ACM certificate ARN"
  }
}

variable "vpc_cidr" {
  type    = string
  default = "10.42.0.0/16"
}
