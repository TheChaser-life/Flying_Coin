resource "google_storage_bucket" "mlflow_artifacts" {
  name     = "${var.project_name}-mlflow-artifacts"
  location = var.region
  uniform_bucket_level_access = true

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

resource "google_storage_bucket" "ml_datasets" {
  name     = "${var.project_name}-ml-datasets"
  location = var.region
  uniform_bucket_level_access = true

  force_destroy = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 30 # Dataset giữ lâu hơn model (30 ngày)
    }
    action {
      type = "Delete"
    }
  }
}
