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
