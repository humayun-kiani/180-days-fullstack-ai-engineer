# terraform/environments/development/main.tf
# Development environment — minimal, cheap, easy to recreate

module "task_api_dev" {
  source = "../../"

  environment          = "development"
  project_name         = "task-api"
  api_instance_count   = 1        # single instance in dev
  app_version          = "latest"
  max_tasks            = 100      # smaller limit in dev

  # Smaller network for dev
  vpc_cidr             = "10.0.0.0/16"
  public_subnet_cidrs  = ["10.0.1.0/24"]
  private_subnet_cidrs = ["10.0.10.0/24"]
  availability_zones   = ["us-east-1a"]

  extra_tags = {
    CostCenter  = "engineering-dev"
    AutoDestroy = "true"    # reminder to clean up dev resources
  }
}

output "dev_api_url" {
  value = module.task_api_dev.api_url
}