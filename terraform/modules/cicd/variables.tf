variable "project_id" {
  description = "ID của project GCP"
  type        = string
}

variable "project_name" {
  description = "Tên project (dùng làm prefix cho các resource)"
  type        = string
}

variable "github_repo" {
  description = "GitHub repository (format: owner/repo) được phép xác thực với GCP"
  type        = string
}
