# Output dùng trong GitHub Actions workflow
# Ví dụ: google-github-actions/auth@v2 cần workload_identity_provider
output "workload_identity_provider" {
  description = "Full name của Workload Identity Provider - dùng trong GitHub Actions"
  value       = google_iam_workload_identity_pool_provider.github_provider.name
  # Format: projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/POOL_ID/providers/PROVIDER_ID
}

output "cicd_sa_email" {
  description = "Email của CI/CD Service Account - dùng trong GitHub Actions"
  value       = google_service_account.cicd_sa.email
  # Format: flying-coin-cicd-sa@flying-coin-489803.iam.gserviceaccount.com
}
