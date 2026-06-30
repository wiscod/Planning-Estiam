terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
  required_version = ">= 1.0"
}

provider "docker" {}



resource "docker_container" "staging" {
  name    = "planning-estiam-staging"
  image   = var.image_name
  restart = "unless-stopped"

  ports {
    internal = 8000
    external = var.staging_port
  }

  env = [
    "ICS_URL=${var.ics_url}"
  ]

  networks_advanced {
    name = var.network_name
  }

  healthcheck {
    test     = ["CMD", "python3", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
    interval = "30s"
    timeout  = "10s"
    retries  = 3
  }

}
