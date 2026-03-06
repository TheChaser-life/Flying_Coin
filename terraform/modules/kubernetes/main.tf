# Tạo GKE Cluster
resource "google_container_cluster" "gke_cluster" {
  name     = "${var.project_name}-gke-cluster"
  location = var.region

  remove_default_node_pool = true # Xóa default node pool để tạo pool riêng
  initial_node_count       = 1    # GKE bắt buộc phải có ít nhất 1 node khi tạo cluster

  network    = var.vpc_id    # Đặt cluster vào VPC từ module networking đã tạo
  subnetwork = var.subnet_id # Đặt nodes vào subnet từ module networking đã tạo

  ip_allocation_policy {
    cluster_secondary_range_name  = "pods-range"     # Pods dùng dãy IP đã định nghĩa trong module networking 
    services_secondary_range_name = "services-range" # Services dùng dãy IP đã định nghĩa trong module networking
  }

  private_cluster_config {
    enable_private_nodes = true # Nodes sẽ không có public IP
    # -> bên ngoài internet không thể truy cập trực tiếp vào Nodes
    # -> Nodes ra internet thông qua Cloud NAT từ module networking
    enable_private_endpoint = false # K8s API endpoint (master) có public IP
    # -> Có thể thực hiện lệnh kubectl từ bên ngoài như cloud shell hoặc laptop cá nhân
    master_ipv4_cidr_block = "172.16.0.0/28" # Dải ip riêng cho K8s master
  }

  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog" # Bật tính năng workload identity cho toàn bộ cụm GKE và định nghĩa workload pool
    # Khi bạn thêm cấu hình này vào google_container_cluster, 
    # GCP sẽ tạo ra một Workload Pool có tên định dạng là [PROJECT_ID].svc.id.goog
    # Pool này đóng vai trò như một cơ quan trung gian xác thực (Identity Provider). 
    # Nó cho phép Google Cloud tin tưởng và chấp nhận danh tính của các Kubernetes Service Account (KSA) đến từ cụm GKE này, mà không cần bất kỳ file key (mật khẩu) nào cả
  }
}

# Tạo node pool, máy chạy các pods
resource "google_container_node_pool" "primary" {
  name       = "${var.project_name}-node-pool"
  location   = var.region
  cluster    = google_container_cluster.gke_cluster.id # Gắn node pool vào cluster đã tạo ở trên
  node_count = var.node_count
  node_config {
    machine_type    = var.machine_type                                 # Loại máy (VD: e2-standard-2, ...)
    service_account = google_service_account.gke_service_account.email # Chỉ định service account cho node
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform" # Cho phép node truy cập tất cả các APIs của GCP (Artifact Registry, Cloud Storage, ...)
      # Nếu service account có quyền truy cập
    ]

    workload_metadata_config {
      mode = "GKE_METADATA" # Cấu hình cách thức các Pod chạy trên các node lấy thông tin định danh
      # Không cho Pod dùng chung quyền của Node nữa
      # Cần kiểm tra danh tính KSA của Pod và chỉ cấp Token đúng với những gì KSA đó được phép
    }
  }
}

# Tạo namespace "database" cho postgresql, rabbitmq, redis
resource "kubernetes_namespace_v1" "database" {
  metadata { name = "database" }
}

# Tạo namespace "external-secrets"
resource "kubernetes_namespace_v1" "external_secrets" {
  metadata { name = "external-secrets" }
}

# Tạo namespace "dev" cho phát triển các service
resource "kubernetes_namespace_v1" "dev" {
  metadata { name = "dev" }
}

# Tạo namespace "staging" cho test các service
resource "kubernetes_namespace_v1" "staging" {
  metadata { name = "staging" }
}

# Tạo namespace "production" cho production
resource "kubernetes_namespace_v1" "production" {
  metadata { name = "production" }
}

# Tạo namespace "logging_monitoring" cho prometheus stack và elastic stack
resource "kubernetes_namespace_v1" "logging_monitoring" {
  metadata { name = "logging_monitoring" }
}

# Tạo namespace "mlops" cho airflow và MLflow
resource "kubernetes_namespace_v1" "mlops" {
  metadata { name = "mlops" }
}

# Tạo service account "eso-ksa" 
resource "kubernetes_service_account_v1" "eso_ksa" {
  metadata {
    name      = "eso-ksa"
    namespace = "external-secrets"
    annotations = {
      "iam.gke.io/gcp-service-account" = var.eso_gcp_sa_email # map Kubernetes Service Account → Google Service Account (GSA).
    }
  }
}

# Cài đặt external secrets helm chart
resource "helm_release" "external_secrets" {
  name       = "external-secrets"
  repository = "https://charts.external-secrets.io"
  chart      = "external-secrets"
  namespace  = "external-secrets"
  set {
    name  = "serviceAccount.create"
    value = "false"
  }
  set {
    name  = "serviceAccount.name"
    value = "eso-ksa"
  }
}

# Tạo service account, cấp quyền tối thiểu cho GKE nodes
resource "google_service_account" "gke_service_account" {
  account_id   = "${var.project_name}-gke-sa"
  display_name = "GKE Service Account for ${var.project_name}"
}

# Cấp các quyền cần thiêt cho service account ở trên
# Pull Docker images
resource "google_project_iam_member" "sa_registry" {
  project = var.project_id
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:${google_service_account.gke_service_account.email}"
}

# Đọc/ghi MLflow model files trên Cloud storage
resource "google_project_iam_member" "sa_storage" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.gke_service_account.email}"
}

# Ghi logs
resource "google_project_iam_member" "sa_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.gke_service_account.email}"
}

# Ghi metrics
resource "google_project_iam_member" "sa_monitoring" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.gke_service_account.email}"
}

