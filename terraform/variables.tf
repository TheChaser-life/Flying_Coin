variable "region" {
  description = "Khu vực triển khai dự án"
  type        = string
}

variable "zone" {
  description = "Zone triển khai cluster"
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
  default     = "e2-standard-4"
}

variable "impersonate_service_account" {
  description = "Service account để impersonate"
  type        = string
  default     = null
}

variable "disk_size" {
  type = number
}

variable "disk_type" {
  type = string
}

variable "github_repo" {
  description = "GitHub repository (format: owner/repo) được phép xác thực với GCP qua Workload Identity"
  type        = string
  default     = "TheChaser-life/Flying_Coin"
}

# Khi gặp lỗi 409 "already exists" (resource cũ chưa xóa hết, Workload Identity Pool soft-delete 30 ngày),
# set resource_suffix = "-v2" để tạo resource mới với tên khác. Sau khi xóa hết resource cũ có thể bỏ suffix.
variable "resource_suffix" {
  description = "Hậu tố cho tên resource (vd: -v2) để tránh conflict khi deploy lại từ đầu"
  type        = string
  default     = ""
}
