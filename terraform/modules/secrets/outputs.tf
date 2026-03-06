output "eso_gcp_sa_email" {
  description = "Email của Google Service Account dành cho ESO"
  value       = google_service_account.eso_gcp_sa.email
}

output "eso_gcp_sa_name" {
  description = "Tên đầy đủ của Google Service Account dành cho ESO"
  value       = google_service_account.eso_gcp_sa.name
}
