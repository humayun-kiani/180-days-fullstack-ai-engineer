# terraform/outputs.tf
# Export key values after apply

output "environment" {
  value       = var.environment
  description = "Current deployment environment"
}

output "vpc_id" {
  value       = module.network.vpc_id
  description = "ID of the created VPC"
}

output "public_subnet_ids" {
  value       = module.network.public_subnet_ids
  description = "IDs of public subnets"
}

output "private_subnet_ids" {
  value       = module.network.private_subnet_ids
  description = "IDs of private subnets"
}

output "security_group_id" {
  value       = module.security.security_group_id
  description = "ID of the API security group"
}

output "instance_ids" {
  value       = module.compute.instance_ids
  description = "IDs of all API server instances"
}

output "load_balancer_dns" {
  value       = module.compute.load_balancer_dns
  description = "DNS name of the load balancer"
}

output "api_url" {
  value       = module.compute.api_url
  description = "URL to access the Task API"
}

output "deployment_summary" {
  value = {
    environment    = var.environment
    instance_count = local.effective_instance_count
    instance_type  = local.current_env.instance_type
    api_url        = module.compute.api_url
    log_level      = local.current_env.log_level
  }
  description = "Summary of the deployed infrastructure"
}