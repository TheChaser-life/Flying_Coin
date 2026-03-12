# ===== CICD Outputs =====
# Dùng trong GitHub Actions workflow
output "workload_identity_provider" {
  description = "Full name của Workload Identity Provider - dùng trong GitHub Actions"
  value       = module.cicd.workload_identity_provider
}

output "cicd_sa_email" {
  description = "Email của CI/CD Service Account - dùng trong GitHub Actions"
  value       = module.cicd.cicd_sa_email
}
