variable "name_prefix" { type = string }
variable "environment"  { type = string }
variable "vpc_id"       { type = string }
variable "api_port"     { type = number; default = 8000 }
variable "allowed_cidr_blocks" {
  type    = list(string)
  default = ["0.0.0.0/0"]
}
variable "tags" { type = map(string); default = {} }