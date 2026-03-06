# 1. Tạo Google Service Account (GSA) cho ESO
resource "google_service_account" "eso_gcp_sa" {
  account_id   = "${var.project_name}-eso-sa"
  display_name = "Service Account cho ESO (${var.project_name})"
}


# 2. Cấp quyền đọc secret cho GSA trên toàn bộ project
resource "google_project_iam_member" "eso_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.eso_gcp_sa.email}"
}


# 3. Liên kết K8s Service Account (KSA) với GSA thông qua workload identity
resource "google_service_account_iam_member" "eso_workload_identity" {
  service_account_id = google_service_account.eso_gcp_sa.name
  role               = "roles/iam.workloadIdentityUser"
  # Cú pháp: serviceAccount:PROJECT_ID.svc.id.goog[NAMESPACE/KSA_NAME]
  # KSA mặc định của External Secrets Operator thường nằm trong namespace "external-secrets" và tên "external-secrets" hoặc "eso-ksa" (được đặt ở helm)
  member = "serviceAccount:${var.project_id}.svc.id.goog[external-secrets/eso-ksa]"
}

