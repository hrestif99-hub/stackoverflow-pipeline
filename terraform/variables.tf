variable "project_id" {
  description = "L'ID du projet GCP"
  type        = string
  default     = "stackoverflow-pipeline"
}

variable "region" {
  description = "La région GCP où créer les ressources"
  type        = string
  default     = "europe-west1"
}

variable "dataset_id" {
  description = "L'ID du dataset BigQuery"
  type        = string
  default     = "stackoverflow"
}

variable "bucket_name" {
  description = "Le nom du bucket GCS"
  type        = string
  default     = "stackoverflow-pipeline-lake"
}