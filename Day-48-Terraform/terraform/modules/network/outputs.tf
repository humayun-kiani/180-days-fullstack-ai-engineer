# terraform/modules/network/outputs.tf

output "vpc_id" {
  value       = "vpc-${random_id.vpc.hex}"
  description = "ID of the created VPC"
}

output "public_subnet_ids" {
  value = [
    for i in range(length(var.public_subnet_cidrs)) :
    "subnet-pub-${random_id.vpc.hex}-${i}"
  ]
  description = "IDs of public subnets"
}

output "private_subnet_ids" {
  value = [
    for i in range(length(var.private_subnet_cidrs)) :
    "subnet-priv-${random_id.vpc.hex}-${i}"
  ]
  description = "IDs of private subnets"
}