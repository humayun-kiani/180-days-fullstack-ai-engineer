# terraform/modules/compute/variables.tf

variable "name_prefix" {
  type = string
}

variable "environment" {
  type = string
}

variable "instance_count" {
  type    = number
  default = 2
}

variable "instance_type" {
  type    = string
  default = "t3.micro"
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "security_group_id" {
  type = string
}

variable "api_port" {
  type    = number
  default = 8000
}

variable "container_image" {
  type    = string
  default = "task-api"
}

variable "app_version" {
  type    = string
  default = "latest"
}

variable "log_level" {
  type    = string
  default = "INFO"
}

variable "max_tasks" {
  type    = number
  default = 10000
}

variable "tags" {
  type    = map(string)
  default = {}
}