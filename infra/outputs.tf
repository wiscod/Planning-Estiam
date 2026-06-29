output "staging_url" {
  description = "URL de l'environnement staging"
  value       = "http://localhost:${var.staging_port}"
}

output "container_name" {
  description = "Nom du conteneur staging"
  value       = docker_container.staging.name
}

output "image_deployed" {
  description = "Image deployee"
  value       = var.image_name
}
