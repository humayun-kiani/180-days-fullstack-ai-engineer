# terraform/providers.tf
# Configure the providers Terraform uses

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    # For real cloud deployment — uncomment what you need:

    # aws = {
    #   source  = "hashicorp/aws"
    #   version = "~> 5.0"
    # }

    # google = {
    #   source  = "hashicorp/google"
    #   version = "~> 5.0"
    # }

    # Local provider — works without any cloud account
    local = {
      source  = "hashicorp/local"
      version = "~> 2.4"
    }

    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }

  # Remote state backend (uncomment for team use):
  # backend "s3" {
  #   bucket         = "task-api-terraform-state"
  #   key            = "infra/terraform.tfstate"
  #   region         = "us-east-1"
  #   dynamodb_table = "terraform-state-lock"
  #   encrypt        = true
  # }
}

# Local provider — no configuration needed
provider "local" {}
provider "random" {}

# AWS provider (comment out if not using AWS):
# provider "aws" {
#   region = var.aws_region
#
#   default_tags {
#     tags = {
#       ManagedBy   = "Terraform"
#       Project     = "TaskAPI"
#       Environment = var.environment
#     }
#   }
# }