# Tạo VPC network
resource "google_compute_network" "vpc_network" {
  name                    = "${var.project_name}-vpc${var.resource_suffix}"
  auto_create_subnetworks = false # Tự tạo subnet
}

# Tạo subnet
# Với kiến trúc của GKE, ta cần tạo 3 dãy IP:
# - Dãy IP cho các Node trong GKE
# - Dãy IP cho các Pod trong GKE
# - Dãy IP cho các Service trong GKE
# Traffic bỏ qua Node-level proxy, đi thẳng vào Pod. 
# Nhưng Ingress resource vẫn cần tồn tại để GCP Load Balancer biết route /v1/auth → auth pods, /v1/market → market pods.
# Traffic từ internet -> GKE Load Balancer -> GKE Load Balancer đọc các ingress resource để biết gửi đến pod nào -> GKE Load Balancer gửi traffic đến các pods
resource "google_compute_subnetwork" "gke_subnet" {
  name          = "${var.project_name}-gke-subnet${var.resource_suffix}"
  ip_cidr_range = var.subnet_cidr # Dãy IP của các Node trong GKE
  network       = google_compute_network.vpc_network.id
  region        = var.region

  secondary_ip_range {
    range_name    = "pods-range"
    ip_cidr_range = var.pods_cidr # Dãy IP của các Pod trong GKE
  }

  secondary_ip_range {
    range_name    = "services-range"
    ip_cidr_range = var.services_cidr # Dãy IP của các Service trong GKE
  }
}

# Tạo Cloud Router
resource "google_compute_router" "router" {
  name    = "${var.project_name}-router${var.resource_suffix}"
  region  = var.region
  network = google_compute_network.vpc_network.id # Gắn router vào VPC phía trên
}

# Tạo Cloud NAT
resource "google_compute_router_nat" "nat" {
  name                               = "${var.project_name}-nat${var.resource_suffix}"
  router                             = google_compute_router.router.name # Gắn NAT vào router phía trên
  nat_ip_allocate_option             = "AUTO_ONLY"                       # GCP tự gán public IP tạm cho NAT
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"   # Cho phép NAT chuyển traffic từ tất cả các subnet + tất cả các IP ranges
}

# Tạo firewall cho phép health check từ GCP
# Mặc định GCP có rule ngầm chặn mọi traffic từ internet vào VPC
# Traffic từ internet sẽ đi vào Load Balancer bên ngoài VPC
# Load Balancer sẽ đổi đổi source IP thành IP của Google được cấu hình bên dưới
# Do đó firewall sẽ cho phép traffic từ Load Balancer vào VPC
resource "google_compute_firewall" "allow_health_check" {
  name    = "${var.project_name}-allow-health-check${var.resource_suffix}"
  network = google_compute_network.vpc_network.id

  allow {
    protocol = "tcp"
    ports    = ["80", "443"]
  }

  source_ranges = [
    "130.211.0.0/22", # GCP health check IP range
    "35.191.0.0/16"   # GCP Health check IP range
  ]
}

# Tạo static IP cho ingress,
# GKE ingress tự động tạo Load Balancer và gán static IP này cho LB đó
# domain sẽ trỏ về IP này
resource "google_compute_global_address" "ingress_ip" {
  name = "${var.project_name}-ingress-ip${var.resource_suffix}"
}
