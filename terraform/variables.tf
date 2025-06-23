# variables.tf

variable "gcp_project_id" {
  description = "The GCP Project ID to deploy resources into."
  type        = string
}

variable "gcp_region" {
  description = "The GCP region to deploy resources into."
  type        = string
  default     = "asia-east1"      #eg. us-east1
}

variable "app_name" {
  description = "The name of the application."
  type        = string
  default     = "vn-prototype"
}