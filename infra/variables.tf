variable "image_name" {
  description = "Image Docker a deployer en staging"
  type        = string
  default     = "ghcr.io/wiscod/planning-estiam:latest"
}

variable "staging_port" {
  description = "Port expose pour l'environnement staging"
  type        = number
  default     = 8001
}

variable "ics_url" {
  description = "URL du calendrier ICS (confidentielle)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "network_name" {
  description = "Nom du reseau Docker partage"
  type        = string
  default     = "cicd-network"
}
