# terraform/modules/compute/outputs.tf

output "instance_ids" {
  value = [for r in random_id.server : "i-${r.hex}"]
}

output "load_balancer_dns" {
  value = "${var.name_prefix}-alb-${random_id.lb.hex}.us-east-1.elb.amazonaws.com"
}

output "api_url" {
  value = "http://${var.name_prefix}-alb-${random_id.lb.hex}.us-east-1.elb.amazonaws.com"
}