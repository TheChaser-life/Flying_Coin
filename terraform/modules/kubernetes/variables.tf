variable "project_id" {
  description = "ID project trên GCP"
  type        = string
}

variable "project_name" {
  description = "Tên của project trên GCP"
  type        = string
}

variable "region" {
  description = "Khu vực triển khai cluster"
  type        = string
}

variable "zone" {
  description = "Zone triển khai cluster"
  type        = string
}

variable "subnet_id" {
  description = "ID của subnet trong VPC đã tạo ở module networking"
  type        = string
}

variable "vpc_id" {
  description = "ID của VPC đã tạo ở module networking"
  type        = string
}

variable "node_count" {
  description = "Số lượng node trong cluster"
  type        = number
}

variable "machine_type" {
  description = "Loại máy cho các node trong cụm"
  type        = string
}

variable "eso_gcp_sa_email" {
  description = "email của GSA để map với KSA"
}

variable "disk_size" {
  type = number
}

variable "disk_type" {
  type = string
}
