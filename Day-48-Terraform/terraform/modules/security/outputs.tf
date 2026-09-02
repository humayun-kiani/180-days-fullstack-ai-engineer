output "security_group_id" {
  value = "sg-${random_id.sg.hex}"
}

output "iam_role_arn" {
  value = "arn:aws:iam::123456789012:role/${var.name_prefix}-instance-role"
}