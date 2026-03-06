resource "google_storage_bucket" "mlflow_artifacts" {
  name     = "${var.project_name}-mlflow-artifacts"
  location = var.region

  force_destroy = true # Cho phép xóa bucket kể cả khi còn object bên trong
  # -> Dùng để bật tắt terraform trong quá trình phát triển

  versioning {
    enabled = true # Giữ lại các version cũ của model
  }

  lifecycle_rule {
    condition {
      age = 7 # Tự động xóa các model cũ hơn 7 ngày
    }
    action {
      type = "Delete"
    }
  }
}
