output "cluster_endpoint" {
  description = "Endpoint của GKE cluster để chạy lệnh kubectl"
  value       = google_container_cluster.gke_cluster.endpoint
}

output "cluster_name" {
  description = "Tên của cụm GKE"
  value       = google_container_cluster.gke_cluster.name
}

output "service_account_email" {
  description = "Email của GKE service account"
  value       = google_service_account.gke_service_account.email
}

output "cluster_ca_cert" {
  description = "Chứng chỉ dùng để mã hóa kết nối HTTPS đến K8s Master"
  value       = google_container_cluster.gke_cluster.master_auth[0].cluster_ca_certificate
}
