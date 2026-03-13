variable "project_name" {
  description = "Tên project dùng làm tiền tố cho các resource"
  type        = string
}

variable "region" {
  description = "GCP Region để triển khai ứng dụng"
  type        = string
}

variable "subnet_cidr" {
  description = "Dãy IP cho các node"
  type        = string
}

variable "pods_cidr" {
  description = "Dãy IP cho các pods"
  type        = string
}

variable "services_cidr" {
  description = "Dãy IP cho các service (ClusterIP, ...)"
  type        = string
}

variable "resource_suffix" {
  description = "Hậu tố cho tên resource (vd: -v2) để tránh conflict"
  type        = string
  default     = ""
}
