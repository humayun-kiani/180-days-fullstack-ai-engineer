# terraform/locals.tf
# Computed values derived from variables

locals {
  # ── Naming convention ─────────────────────────────────────
  # All resources follow: {project}-{environment}-{resource_type}
  name_prefix = "${var.project_name}-${var.environment}"

  # ── Common tags ───────────────────────────────────────────
  # Merged onto every resource
  common_tags = merge(
    {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
      CreatedAt   = timestamp()    # when terraform apply ran
    },
    var.extra_tags
  )

  # ── Environment-specific config ───────────────────────────
  # Different defaults per environment without separate files
  env_config = {
    development = {
      instance_type      = "t3.micro"
      instance_count     = 1
      enable_monitoring  = false
      deletion_protection = false
      log_level          = "DEBUG"
    }
    staging = {
      instance_type      = "t3.small"
      instance_count     = 2
      enable_monitoring  = true
      deletion_protection = false
      log_level          = "INFO"
    }
    production = {
      instance_type      = "t3.medium"
      instance_count     = 3
      enable_monitoring  = true
      deletion_protection = true
      log_level          = "WARNING"
    }
  }

  # Get the config for the current environment
  current_env = local.env_config[var.environment]

  # Effective instance count (variable overrides env default)
  effective_instance_count = (
    var.api_instance_count != 2    # 2 is the variable default
    ? var.api_instance_count       # user overrode it
    : local.current_env.instance_count  # use env default
  )

  # ── Network calculations ──────────────────────────────────
  subnet_count = length(var.public_subnet_cidrs)

  # ── Port rules (for security group) ──────────────────────
  allowed_ports = {
    api     = { port = var.api_port, description = "Task API" }
    http    = { port = 80, description = "HTTP redirect" }
    https   = { port = 443, description = "HTTPS" }
    ssh     = { port = 22, description = "SSH admin access" }
  }
}