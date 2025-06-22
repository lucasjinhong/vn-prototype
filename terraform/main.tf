# main.tf

# 1. ARTIFACT REGISTRY
# Create a Google Artifact Registry to store Docker images
resource "google_artifact_registry_repository" "my_app_repo" {
  provider      = google-beta
  project       = var.gcp_project_id
  location      = var.gcp_region
  repository_id = "${var.app_name}-repo"
  description   = "Docker repository for ${var.app_name}"
  format        = "DOCKER"
}

# 2. GKE CLUSTER
# Create the GKE Cluster
resource "google_container_cluster" "primary" {
  name     = "${var.app_name}-gke-cluster"
  location = var.gcp_region
  enable_autopilot   = true
}