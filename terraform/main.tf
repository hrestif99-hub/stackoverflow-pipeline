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
  region  = var.region
}

# Bucket GCS — data lake
resource "google_storage_bucket" "data_lake" {
  name          = var.bucket_name
  location      = var.region
  force_destroy = true
}

# Dataset BigQuery — warehouse
resource "google_bigquery_dataset" "stackoverflow" {
  dataset_id = var.dataset_id
  location   = var.region
}

# Topic Pub/Sub — boîte aux lettres
resource "google_pubsub_topic" "stackoverflow_topic" {
  name = "stackoverflow-questions"
}

# Secret Manager — coffre-fort pour la clé API
resource "google_secret_manager_secret" "stackoverflow_api_key" {
  secret_id = "stackoverflow-api-key"

  replication {
    auto {}
  }
}

# Permission IAM — Cloud Function peut lire les secrets
resource "google_project_iam_member" "cloud_function_secret_access" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:783967523848-compute@developer.gserviceaccount.com"
}