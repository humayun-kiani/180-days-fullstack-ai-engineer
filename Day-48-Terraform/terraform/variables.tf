# terraform/variables.tf
# All input variables — customize these for your environment

# ── Environment ────────────────────────────────────────────────
variable "environment" {
  type        = string
  description = "Deployment environment (development, staging, production)"
  default     = "development"

  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be development, staging, or production."
  }
}

variable "project_name" {
  type        = string
  description = "Project name used for resource naming"
  default     = "task-api"
}

# ── Network ────────────────────────────────────────────────────
variable "vpc_cidr" {
  type        = string
  description = "CIDR block for the VPC"
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  type        = list(string)
  description = "CIDR blocks for public subnets (one per AZ)"
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  type        = list(string)
  description = "CIDR blocks for private subnets (one per AZ)"
  default     = ["10.0.10.0/24", "10.0.11.0/24"]
}

variable "availability_zones" {
  type        = list(string)
  description = "Availability zones to deploy into"
  default     = ["us-east-1a", "us-east-1b"]
}

# ── Compute ────────────────────────────────────────────────────
variable "instance_type" {
  type        = string
  description = "EC2 instance type for API servers"
  default     = "t3.micro"
}

variable "api_instance_count" {
  type        = number
  description = "Number of API server instances"
  default     = 2

  validation {
    condition     = var.api_instance_count >= 1 && var.api_instance_count <= 20
    error_message = "Instance count must be between 1 and 20."
  }
}

variable "api_port" {
  type        = number
  description = "Port the Task API listens on"
  default     = 8000
}

# ── Application ────────────────────────────────────────────────
variable "app_version" {
  type        = string
  description = "Docker image tag to deploy"
  default     = "latest"
}

variable "log_level" {
  type        = string
  description = "Application log level"
  default     = "INFO"

  validation {
    condition     = contains(["DEBUG", "INFO", "WARNING", "ERROR"], var.log_level)
    error_message = "Log level must be DEBUG, INFO, WARNING, or ERROR."
  }
}

variable "max_tasks" {
  type        = number
  description = "Maximum number of tasks the service stores"
  default     = 10000
}

# ── Tagging ────────────────────────────────────────────────────
variable "extra_tags" {
  type        = map(string)
  description = "Additional tags to apply to all resources"
  default     = {}
}