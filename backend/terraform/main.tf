# Terraform Configuration for QTC on GCP
# Main configuration

terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
  }

  backend "gcs" {
    # Configure before running: gsutil mb gs://qtc-terraform-state
    bucket  = "qtc-terraform-state"
    prefix  = "prod"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "cloud_run" {
  service            = "run.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "firestore" {
  service            = "firestore.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "storage" {
  service            = "storage-googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "cloud_build" {
  service            = "cloudbuild.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "compute" {
  service            = "compute.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "secretmanager" {
  service            = "secretmanager.googleapis.com"
  disable_on_destroy = false
}

# Cloud Run - Backend Service
resource "google_cloud_run_service" "backend" {
  name     = "${var.app_name}-backend"
  location = var.region

  template {
    spec {
      service_account_name = var.backend_service_account_email

      containers {
        image = "gcr.io/${var.project_id}/${var.app_name}-backend:latest"

        resources {
          limits = {
            memory = var.backend_memory
            cpu    = var.backend_cpu
          }
        }

        env {
          name  = "DISABLE_AUTH"
          value = "false"
        }

        env {
          name  = "GOOGLE_APPLICATION_CREDENTIALS"
          value = "/var/secrets/gcp/credentials.json"
        }

        env {
          name  = "GOOGLE_CLOUD_PROJECT"
          value = var.project_id
        }

        env {
          name = "OPENAI_API_KEY"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.openai_key.id
              key  = "latest"
            }
          }
        }

        env {
          name = "STRIPE_API_KEY"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.stripe_key.id
              key  = "latest"
            }
          }
        }

        env {
          name = "STRIPE_WEBHOOK_SECRET"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.stripe_webhook.id
              key  = "latest"
            }
          }
        }
      }

      timeout_seconds = 3600
    }

    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale" = var.max_instances
        "autoscaling.knative.dev/minScale" = var.min_instances
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [google_project_service.cloud_run]
}

# Cloud Run - Frontend Service
resource "google_cloud_run_service" "frontend" {
  name     = "${var.app_name}-frontend"
  location = var.region

  template {
    spec {
      service_account_name = var.frontend_service_account_email

      containers {
        image = "gcr.io/${var.project_id}/${var.app_name}-frontend:latest"

        resources {
          limits = {
            memory = var.frontend_memory
            cpu    = var.frontend_cpu
          }
        }

        env {
          name  = "PORT"
          value = "8080"
        }
      }

      timeout_seconds = 3600
    }

    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale" = var.max_instances
        "autoscaling.knative.dev/minScale" = var.min_instances
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [google_project_service.cloud_run]
}

# Allow unauthenticated access to both services
resource "google_cloud_run_service_iam_member" "backend_public" {
  service  = google_cloud_run_service.backend.name
  location = google_cloud_run_service.backend.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_service_iam_member" "frontend_public" {
  service  = google_cloud_run_service.frontend.name
  location = google_cloud_run_service.frontend.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# GCS Bucket for documents/uploads
resource "google_storage_bucket" "documents" {
  name          = var.gcs_bucket_name
  location      = var.region
  force_destroy = false

  uniform_bucket_level_access = true

  cors {
    origin      = ["https://*"]
    method      = ["GET", "POST", "PUT", "DELETE"]
    response_header = ["Content-Type", "Access-Control-Allow-Origin"]
    max_age_seconds = 3600
  }

  depends_on = [google_project_service.storage]
}

# Secret Manager - OpenAI API Key
resource "google_secret_manager_secret" "openai_key" {
  secret_id = "openai-api-key"
  replication {
    auto {}
  }
  depends_on = [google_project_service.secretmanager]
}

resource "google_secret_manager_secret_version" "openai_key" {
  secret      = google_secret_manager_secret.openai_key.id
  secret_data = var.openai_api_key
}

# Secret Manager - Stripe API Key
resource "google_secret_manager_secret" "stripe_key" {
  secret_id = "stripe-api-key"
  replication {
    auto {}
  }
  depends_on = [google_project_service.secretmanager]
}

resource "google_secret_manager_secret_version" "stripe_key" {
  secret      = google_secret_manager_secret.stripe_key.id
  secret_data = var.stripe_api_key
}

# Secret Manager - Stripe Webhook Secret
resource "google_secret_manager_secret" "stripe_webhook" {
  secret_id = "stripe-webhook-secret"
  replication {
    auto {}
  }
  depends_on = [google_project_service.secretmanager]
}

resource "google_secret_manager_secret_version" "stripe_webhook" {
  secret      = google_secret_manager_secret.stripe_webhook.id
  secret_data = var.stripe_webhook_secret
}

# Firestore Database (if not already created)
resource "google_firestore_database" "database" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.firestore_region
  type        = "FIRESTORE_NATIVE"
}

# Outputs
output "backend_url" {
  value       = google_cloud_run_service.backend.status[0].url
  description = "Backend Cloud Run service URL"
}

output "frontend_url" {
  value       = google_cloud_run_service.frontend.status[0].url
  description = "Frontend Cloud Run service URL"
}

output "gcs_bucket" {
  value       = google_storage_bucket.documents.name
  description = "GCS bucket for documents"
}
