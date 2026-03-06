variable "project_id" {
  description = "ID project trên GCP"
  type        = string
}

variable "project_name" {
  description = "Tên project dùng làm tiền tố cho các resource"
  type        = string
}

variable "region" {
  description = "GCP Region để triển khai ứng dụng"
  type        = string
}
