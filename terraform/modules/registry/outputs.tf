output "repository_url" {
  description = "URL registry để push/pull Docker images"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_repo.repository_id}"
}

output "repository_id" {
  description = "ID của repository"
  value       = google_artifact_registry_repository.docker_repo.repository_id
}
