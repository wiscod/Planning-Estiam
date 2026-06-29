# Planning ESTIAM

API REST qui expose le planning des cours ESTIAM à partir d'un calendrier ICS.

## Ce que fait l'application

- Télécharge le calendrier ICS depuis Hyperplanning
- Parse les événements et les stocke en JSON
- Expose une API REST FastAPI avec les endpoints suivants :

| Endpoint | Méthode | Description |
|---|---|---|
| `/health` | GET | Retourne `{"status": "ok"}` — utilisé par le healthcheck |
| `/planning` | GET | Retourne tous les cours au format JSON |
| `/planning/week/{n}` | GET | Retourne les cours de la semaine N |
| `/refresh` | POST | Relance le scraping ICS |
| `/metrics` | GET | Métriques Prometheus (requêtes, refreshes) |

## Prérequis

- Docker & Docker Compose
- Python 3.11+ (pour le développement local)
- Terraform >= 1.0 (pour le provisionnement staging)

## Lancer localement

```bash
# Copier les variables d'environnement
cp .env.example .env
# Remplir ICS_URL dans .env

# Installer les dépendances
make install

# Rafraîchir le planning (génère public/data/planning.json)
make refresh

# Lancer l'API
make run
# → http://localhost:8000
```

## Lancer avec Docker

```bash
docker-compose up --build
# → http://localhost:8000
```

## Tests

```bash
make test
# Résultats dans coverage.xml
```

## Lancer le monitoring (Prometheus + Grafana)

```bash
# Prérequis : le réseau cicd-network doit exister
docker network create cicd-network 2>/dev/null || true

# Démarrer Prometheus et Grafana
cd monitoring/
docker-compose up -d

# Prometheus : http://localhost:9090
# Grafana    : http://localhost:3000  (admin / admin)
```

## Lancer le pipeline CI/CD

Le pipeline Jenkins complet couvre 9 stages :

1. **Checkout** — clone le repo, affiche le SHA
2. **Lint** — flake8 sur `src/` et `tests/`
3. **Build & Test** — build Docker + pytest avec coverage
4. **SonarQube Analysis** — analyse qualité du code
5. **Quality Gate** — bloque si le seuil qualité n'est pas atteint
6. **Security Scan** — scan CVE avec Trivy
7. **Push** — pousse l'image sur `ghcr.io/wiscod`
8. **IaC Apply** — provisionne le staging via Terraform (Docker provider)
9. **Smoke Test** — vérifie que `/health` répond 200

### Credentials Jenkins requis

| ID credential | Type | Usage |
|---|---|---|
| `sonar-token` | Secret text | Token SonarQube |
| `github-token` | Username/Password | Push sur ghcr.io |
| `ics-url` | Secret text | URL du calendrier ICS |

## Architecture

```
Planning-Estiam/
├── src/
│   ├── api.py          # FastAPI — endpoints REST + métriques
│   └── scraper.py      # Parser ICS → JSON
├── tests/              # Tests unitaires pytest
├── infra/              # Terraform — provisionnement Docker staging
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
├── monitoring/         # Prometheus + Grafana
│   ├── prometheus.yml
│   ├── docker-compose.yml
│   └── grafana/
├── public/             # Frontend HTML statique
├── Dockerfile          # Multi-stage, image slim, non-root
├── docker-compose.yml  # Stack locale avec cicd-network
└── Jenkinsfile         # Pipeline CI/CD 9 stages
```
