terraform {
  required_version = ">= 1.10.0, < 2.0.0"

  # Bucket, key, region, and KMS key are supplied from an untracked backend
  # configuration file. Native S3 lockfiles replace deprecated DynamoDB locks.
  backend "s3" {
    encrypt      = true
    use_lockfile = true
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Application = "parkshield-ai"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"

  default_tags {
    tags = {
      Application = "parkshield-ai"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}
