resource "google_artifact_registry_repository" "docker_repo" {
  repository_id = "${var.project_name}-docker"
  location      = var.region
  format        = "DOCKER" # Artifact Registry hỗ trợ nhiều format khác nhau
  # Chọn Docker để lưu Docker images
  description = "Docker repository cho ${var.project_name}"
}
