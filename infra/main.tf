terraform {
  required_version = ">= 1.6"
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

# ── Service Account ──────────────────────────────────────────────────────────
resource "google_service_account" "backend" {
  account_id   = "fieldfix-backend"
  display_name = "FieldFix Backend Service Account"
}

locals {
  backend_roles = [
    "roles/aiplatform.user",
    "roles/datastore.user",
    "roles/storage.objectViewer",
    "roles/storage.objectCreator",
    "roles/secretmanager.secretAccessor",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
  ]
}

resource "google_project_iam_member" "backend_roles" {
  for_each = toset(local.backend_roles)
  project  = var.project_id
  role     = each.value
  member   = "serviceAccount:${google_service_account.backend.email}"
}

# ── Firestore ─────────────────────────────────────────────────────────────────
resource "google_firestore_database" "fieldfix" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"
}

resource "google_firestore_index" "cases_by_model_time" {
  project    = var.project_id
  database   = google_firestore_database.fieldfix.name
  collection = "fault_cases"
  fields {
    field_path = "equipment_model"
    order      = "ASCENDING"
  }
  fields {
    field_path = "resolved"
    order      = "ASCENDING"
  }
  fields {
    field_path = "timestamp"
    order      = "DESCENDING"
  }
}

# ── Cloud Storage ─────────────────────────────────────────────────────────────
resource "google_storage_bucket" "knowledge_base" {
  name                        = "${var.project_id}-fieldfix-kb"
  location                    = "US-CENTRAL1"
  uniform_bucket_level_access = true
  versioning { enabled = true }
  lifecycle_rule {
    action { type = "Delete" }
    condition { age = 365 }
  }
}

resource "google_storage_bucket" "tf_state" {
  name                        = "fieldfix-tf-state"
  location                    = "US-CENTRAL1"
  uniform_bucket_level_access = true
  versioning { enabled = true }
}

# ── Artifact Registry ─────────────────────────────────────────────────────────
resource "google_artifact_registry_repository" "fieldfix" {
  location      = var.region
  repository_id = "fieldfix"
  format        = "DOCKER"
}

# ── Cloud Run ─────────────────────────────────────────────────────────────────
resource "google_cloud_run_v2_service" "backend" {
  name     = "fieldfix-backend"
  location = var.region

  template {
    service_account = google_service_account.backend.email

    scaling {
      min_instance_count = 1
      max_instance_count = 10
    }

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/fieldfix/backend:${var.image_tag}"

      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "GCP_REGION"
        value = var.region
      }
      env {
        name  = "GCS_BUCKET_NAME"
        value = google_storage_bucket.knowledge_base.name
      }
      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }

      resources {
        limits = {
          memory = "2Gi"
          cpu    = "2"
        }
        startup_cpu_boost = true
      }

      startup_probe {
        http_get { path = "/health" }
        initial_delay_seconds = 10
        period_seconds        = 5
        failure_threshold     = 10
      }

      liveness_probe {
        http_get { path = "/health" }
        period_seconds    = 30
        failure_threshold = 3
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# Allow unauthenticated access (public demo)
resource "google_cloud_run_service_iam_member" "public" {
  location = google_cloud_run_v2_service.backend.location
  service  = google_cloud_run_v2_service.backend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
