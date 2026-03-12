# 1. Tạo GCP Service Account riêng cho CI/CD pipeline
resource "google_service_account" "cicd_sa" {
  account_id   = "${var.project_name}-cicd-sa"
  display_name = "CI/CD Service Account cho ${var.project_name}"
  description  = "Service Account dành cho GitHub Actions CI/CD pipeline"
}

# 2. Tạo Workload Identity Pool - "Phòng chờ" cho danh tính bên ngoài (GitHub)
resource "google_iam_workload_identity_pool" "github_pool" {
  workload_identity_pool_id = "${var.project_name}-github-pool"
  display_name              = "GitHub Actions Pool"
  description               = "Pool xác thực cho GitHub Actions CI/CD"
}

# 3. Tạo Workload Identity Provider - Kết nối GitHub OIDC vào Pool
resource "google_iam_workload_identity_pool_provider" "github_provider" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github_pool.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider"
  display_name                       = "GitHub Actions Provider"
  description                        = "OIDC Provider cho GitHub Actions"

  # Cấu hình OIDC - chỉ chấp nhận token từ GitHub
  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }

  # Map các claim trong JWT token của GitHub sang GCP attributes
  attribute_mapping = {
    "google.subject"       = "assertion.sub"                 # Subject (unique ID)
    "attribute.actor"      = "assertion.actor"               # Ai trigger workflow
    "attribute.repository" = "assertion.repository"          # Repo nào
    "attribute.ref"        = "assertion.ref"                 # Branch/tag nào
  }

  # CHỈ cho phép repo cụ thể - ngăn repo khác xác thực
  attribute_condition = "assertion.repository == \"${var.github_repo}\""
}


# 4. Cho phép danh tính từ GitHub pool impersonate (mượn quyền) cicd_sa
resource "google_service_account_iam_member" "github_sa_binding" {
  service_account_id = google_service_account.cicd_sa.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github_pool.name}/attribute.repository/${var.github_repo}"
}

# 5. Cấp quyền cho cicd_sa - chỉ những gì CI/CD cần

# Push/pull Docker images lên Artifact Registry
resource "google_project_iam_member" "cicd_registry" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.cicd_sa.email}"
}

# Deploy workloads lên GKE (kubectl apply, tạo/cập nhật Deployments, Services...)
resource "google_project_iam_member" "cicd_gke" {
  project = var.project_id
  role    = "roles/container.developer"
  member  = "serviceAccount:${google_service_account.cicd_sa.email}"
}
