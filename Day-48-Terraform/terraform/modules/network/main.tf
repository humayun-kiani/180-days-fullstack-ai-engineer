# terraform/modules/network/main.tf
# Network module: VPC, subnets, routing
# This defines the network topology for the Task API

# ── VPC ───────────────────────────────────────────────────────
# Using local_file to simulate resources (works without cloud account)
resource "local_file" "vpc_config" {
  filename = "${path.module}/../../.simulated/vpc-${var.name_prefix}.json"
  content  = jsonencode({
    resource_type  = "VPC"
    id             = "vpc-${random_id.vpc.hex}"
    name           = "${var.name_prefix}-vpc"
    cidr_block     = var.vpc_cidr
    environment    = var.environment
    dns_enabled    = true
    dns_hostnames  = true
    tags           = var.tags
  })
}

resource "random_id" "vpc" {
  byte_length = 4
}

# ── Public Subnets ────────────────────────────────────────────
resource "local_file" "public_subnets" {
  count    = length(var.public_subnet_cidrs)
  filename = "${path.module}/../../.simulated/subnet-public-${count.index}-${var.name_prefix}.json"
  content  = jsonencode({
    resource_type     = "PublicSubnet"
    id                = "subnet-pub-${random_id.vpc.hex}-${count.index}"
    name              = "${var.name_prefix}-public-${count.index + 1}"
    cidr_block        = var.public_subnet_cidrs[count.index]
    availability_zone = var.availability_zones[count.index % length(var.availability_zones)]
    public_ip_on_launch = true
    route_table        = "rtb-public-${random_id.vpc.hex}"
    tags              = var.tags
  })
}

# ── Private Subnets ───────────────────────────────────────────
resource "local_file" "private_subnets" {
  count    = length(var.private_subnet_cidrs)
  filename = "${path.module}/../../.simulated/subnet-private-${count.index}-${var.name_prefix}.json"
  content  = jsonencode({
    resource_type     = "PrivateSubnet"
    id                = "subnet-priv-${random_id.vpc.hex}-${count.index}"
    name              = "${var.name_prefix}-private-${count.index + 1}"
    cidr_block        = var.private_subnet_cidrs[count.index]
    availability_zone = var.availability_zones[count.index % length(var.availability_zones)]
    public_ip_on_launch = false
    nat_gateway       = "nat-${random_id.vpc.hex}"
    tags              = var.tags
  })
}

# ── Internet Gateway ──────────────────────────────────────────
resource "local_file" "internet_gateway" {
  filename = "${path.module}/../../.simulated/igw-${var.name_prefix}.json"
  content  = jsonencode({
    resource_type = "InternetGateway"
    id            = "igw-${random_id.vpc.hex}"
    name          = "${var.name_prefix}-igw"
    vpc_id        = "vpc-${random_id.vpc.hex}"
    tags          = var.tags
  })
}