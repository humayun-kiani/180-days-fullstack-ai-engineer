# terraform/modules/security/main.tf
# Security module: security groups, IAM

resource "random_id" "sg" {
  byte_length = 4
}

# API Security Group (simulated)
resource "local_file" "security_group" {
  filename = "${path.module}/../../.simulated/sg-${var.name_prefix}.json"
  content  = jsonencode({
    resource_type = "SecurityGroup"
    id            = "sg-${random_id.sg.hex}"
    name          = "${var.name_prefix}-api-sg"
    vpc_id        = var.vpc_id
    description   = "Security group for Task API"
    ingress_rules = [
      {
        description = "HTTP from anywhere"
        from_port   = 80
        to_port     = 80
        protocol    = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
      },
      {
        description = "HTTPS from anywhere"
        from_port   = 443
        to_port     = 443
        protocol    = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
      },
      {
        description = "Task API port"
        from_port   = var.api_port
        to_port     = var.api_port
        protocol    = "tcp"
        cidr_blocks = var.allowed_cidr_blocks
      }
    ]
    egress_rules = [
      {
        description = "All outbound traffic"
        from_port   = 0
        to_port     = 0
        protocol    = "-1"
        cidr_blocks = ["0.0.0.0/0"]
      }
    ]
    tags = var.tags
  })
}

# IAM Role for instances (simulated)
resource "local_file" "iam_role" {
  filename = "${path.module}/../../.simulated/iam-${var.name_prefix}.json"
  content  = jsonencode({
    resource_type = "IAMRole"
    name          = "${var.name_prefix}-instance-role"
    description   = "Role for Task API instances"
    policies      = [
      "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy",
      "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
    ]
    trust_policy = {
      principal = "ec2.amazonaws.com"
      action    = "sts:AssumeRole"
    }
    tags = var.tags
  })
}