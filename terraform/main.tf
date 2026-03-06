terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 6.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = ">= 2.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = ">= 2.0"
    }
  }
}

provider "google" {
  region  = var.region
  project = var.project_id
}

# Lấy token chứng thực của account Google đang chạy Terraform
data "google_client_config" "default" {}

provider "kubernetes" {
  host                   = "https://${module.kubernetes.cluster_endpoint}" # url của K8s API server để terraform gọi đến
  token                  = data.google_client_config.default.access_token  # token chứng thực của account Google đang chạy Terraform
  cluster_ca_certificate = base64decode(module.kubernetes.cluster_ca_cert) # chứng chỉ dùng để mã hóa kết nối HTTPS đến K8s Master
}

provider "helm" {
  kubernetes {
    host                   = "https://${module.kubernetes.cluster_endpoint}" # 
    token                  = data.google_client_config.default.access_token
    cluster_ca_certificate = base64decode(module.kubernetes.cluster_ca_cert)
  }
}

module "networking" {
  source        = "./modules/networking"
  project_name  = var.project_name
  region        = var.region
  subnet_cidr   = var.subnet_cidr
  pods_cidr     = var.pods_cidr
  services_cidr = var.services_cidr
}

module "kubernetes" {
  source           = "./modules/kubernetes"
  project_id       = var.project_id
  project_name     = var.project_name
  region           = var.region
  subnet_id        = module.networking.subnet_id
  vpc_id           = module.networking.vpc_id
  node_count       = var.node_count
  machine_type     = var.machine_type
  eso_gcp_sa_email = module.secrets.eso_gcp_sa_email
}

module "registry" {
  source       = "./modules/registry"
  project_id   = var.project_id
  project_name = var.project_name
  region       = var.region
}

module "storage" {
  source       = "./modules/storage"
  project_name = var.project_name
  region       = var.region
}

module "secrets" {
  source       = "./modules/secrets"
  project_id   = var.project_id
  project_name = var.project_name
}
