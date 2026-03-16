# Terraform Configuration for QTC on GCP
# Main variables file

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "app_name" {
  description = "Application name"
  type        = string
  default     = "qtc"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "backend_service_account_email" {
  description = "Backend service account email"
  type        = string
}

variable "frontend_service_account_email" {
  description = "Frontend service account email"
  type        = string
}

variable "backend_memory" {
  description = "Backend Cloud Run memory"
  type        = string
  default     = "512Mi"
}

variable "backend_cpu" {
  description = "Backend Cloud Run CPU"
  type        = string
  default     = "1"
}

variable "frontend_memory" {
  description = "Frontend Cloud Run memory"
  type        = string
  default     = "256Mi"
}

variable "frontend_cpu" {
  description = "Frontend Cloud Run CPU"
  type        = string
  default     = "1"
}

variable "max_instances" {
  description = "Max instances for Cloud Run autoscaling"
  type        = number
  default     = 10
}

variable "min_instances" {
  description = "Min instances for Cloud Run (0 = fully serverless)"
  type        = number
  default     = 0
}

variable "enable_cdn" {
  description = "Enable Cloud CDN for frontend"
  type        = bool
  default     = true
}

variable "firestore_region" {
  description = "Firestore region"
  type        = string
  default     = "us-central1"
}

variable "gcs_bucket_name" {
  description = "GCS bucket for documents and uploads"
  type        = string
  default     = "qtc-documents-zheight"
}
