terraform {
  backend "gcs" {
    bucket = "stackoverflow-pipeline-tfstate"
    prefix = "terraform-manuel/state"
  }
}
