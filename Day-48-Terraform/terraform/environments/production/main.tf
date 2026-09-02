# terraform/environments/production/main.tf
# Production environment — HA, monitored, protected

module "task_api_prod" {
  source = "../../"

  environment          = "production"
  project_name         = "task-api"
  api_instance_count   = 3        # 3 instances for HA
  app_version          = "1.2.0"  # pinned version in prod
  max_tasks            = 100000

  # Multi-AZ for high availability
  vpc_cidr             = "10.0.0.0/16"
  public_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  private_subnet_cidrs = ["10.0.10.0/24", "10.0.11.0/24", "10.0.12.0/24"]
  availability_zones   = ["us-east-1a", "us-east-1b", "us-east-1c"]

  extra_tags = {
    CostCenter  = "engineering-prod"
    Criticality = "high"
    SLA         = "99.99%"
  }
}

output "prod_api_url" {
  value       = module.task_api_prod.api_url
  description = "Production API URL"
}

output "prod_instance_count" {
  value = module.task_api_prod.deployment_summary.instance_count
}