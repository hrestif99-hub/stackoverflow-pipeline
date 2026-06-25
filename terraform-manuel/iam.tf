terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
}

# Permission IAM — Cloud Function peut lire les secrets
resource "google_project_iam_member" "cloud_function_secret_access" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:783967523848-compute@developer.gserviceaccount.com"
}
