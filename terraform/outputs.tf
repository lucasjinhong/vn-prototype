# terraform/outputs.tf

output "gke_cluster_name" {
  description = "The name of the GKE cluster."
  value       = google_container_cluster.primary.name
}

output "gcp_project_id" {
  description = "The GCP project ID."
  value       = var.gcp_project_id
}

output "gcp_region" {
  description = "The GCP region of the cluster."
  value       = var.gcp_region
}