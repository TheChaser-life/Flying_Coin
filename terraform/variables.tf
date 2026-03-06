variable "region" {
  description = "Khu vực triển khai dự án"
  type        = string
}

variable "project_id" {
  description = "Project ID trên GCP"
  type        = string
}

variable "project_name" {
  description = "Tên project trên GCP"
  type        = string
}

variable "subnet_cidr" {
  description = "Dải IP cho các node trong cụm"
  type        = string
}

variable "pods_cidr" {
  description = "Dải IP cho các pods"
  type        = string

}

variable "services_cidr" {
  description = "Dải IP cho các service"
  type        = string

}

variable "node_count" {
  description = "Số lượng node trong cluster"
  type        = number

}

variable "machine_type" {
  description = "Loại máy cho các node"
  type        = string

}

