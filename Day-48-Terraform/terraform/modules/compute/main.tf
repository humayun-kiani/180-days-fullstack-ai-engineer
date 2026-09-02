# terraform/modules/compute/main.tf
# Compute module: API servers

resource "random_id" "server" {
  count       = var.instance_count
  byte_length = 4
}

# Simulate EC2 instances / compute nodes
resource "local_file" "api_instances" {
  count    = var.instance_count
  filename = "${path.module}/../../.simulated/instance-${count.index}-${var.name_prefix}.json"
  content  = jsonencode({
    resource_type  = "ComputeInstance"
    id             = "i-${random_id.server[count.index].hex}"
    name           = "${var.name_prefix}-api-${count.index + 1}"
    instance_type  = var.instance_type
    subnet_id      = var.private_subnet_ids[count.index % length(var.private_subnet_ids)]
    security_group = var.security_group_id
    private_ip     = "10.0.10.${count.index + 10}"
    environment_vars = {
      ENVIRONMENT = var.environment
      LOG_LEVEL   = var.log_level
      MAX_TASKS   = tostring(var.max_tasks)
      POD_NAME    = "${var.name_prefix}-api-${count.index + 1}"
    }
    user_data = <<-USERDATA
      #!/bin/bash
      apt-get update
      apt-get install -y docker.io
      docker pull ${var.container_image}:${var.app_version}
      docker run -d \
        --name task-api \
        -p ${var.api_port}:8000 \
        -e ENVIRONMENT=${var.environment} \
        -e LOG_LEVEL=${var.log_level} \
        ${var.container_image}:${var.app_version}
    USERDATA
    tags = var.tags
  })
}

# Load Balancer (simulated)
resource "random_id" "lb" {
  byte_length = 4
}

resource "local_file" "load_balancer" {
  filename = "${path.module}/../../.simulated/lb-${var.name_prefix}.json"
  content  = jsonencode({
    resource_type = "LoadBalancer"
    id            = "lb-${random_id.lb.hex}"
    name          = "${var.name_prefix}-alb"
    dns_name      = "${var.name_prefix}-alb-${random_id.lb.hex}.us-east-1.elb.amazonaws.com"
    type          = "application"
    scheme        = "internet-facing"
    targets = [
      for i in range(var.instance_count) :
      "i-${random_id.server[i].hex}:${var.api_port}"
    ]
    health_check = {
      path     = "/health"
      port     = var.api_port
      protocol = "HTTP"
      interval = 30
    }
    tags = var.tags
  })
}