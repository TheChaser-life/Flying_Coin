output "mlflow_bucket_url" {
  description = "URL bucket để MLflow lưu model"
  value       = google_storage_bucket.mlflow_artifacts.url
}

output "mlflow_bucket_name" {
  description = "Tên bucket MLflow"
  value       = google_storage_bucket.mlflow_artifacts.name
}
