output "vpc_id" {
  description = "VPC Network ID, dùng cho module kubernetes"
  value       = google_compute_network.vpc_network.id
}

output "vpc_name" {
  description = "VPC Network name"
  value       = google_compute_network.vpc_network.name
}

output "subnet_id" {
  description = "GKE Subnet ID, dùng cho module kubernetes"
  value       = google_compute_subnetwork.gke_subnet.id
}

output "ingress_ip" {
  description = "Static IP cho Ingress, để biết trỏ domain vào chính xác IP nào"
  value       = google_compute_global_address.ingress_ip.address
}
