output "backend_url" {
  description = "URL of the deployed Cloud Run backend"
  value       = google_cloud_run_v2_service.backend.uri
}

output "knowledge_base_bucket" {
  description = "Name of the Cloud Storage knowledge base bucket"
  value       = google_storage_bucket.knowledge_base.name
}

output "service_account_email" {
  description = "Backend service account email"
  value       = google_service_account.backend.email
}

output "artifact_registry" {
  description = "Artifact Registry repository path"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/fieldfix"
}
