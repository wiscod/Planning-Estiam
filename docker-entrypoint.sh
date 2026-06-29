#!/bin/sh
set -e

if [ "$#" -gt 0 ]; then
    exec "$@"
fi

echo "==> Initialisation du planning (ICS -> JSON)..."
python3 src/scraper.py

echo "==> Demarrage de l'API sur le port 8000..."
exec uvicorn src.api:app --host 0.0.0.0 --port 8000
