# ── stage 1 : installation des dépendances ──────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── stage 2 : image de production ───────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Packages installés copiés depuis le builder (sans pip, tests, etc.)
COPY --from=builder /install /usr/local

# Code source et assets
COPY src/                ./src/
COPY public/index.html   ./public/index.html
COPY tests/              ./tests/
COPY docker-entrypoint.sh .

# Dossiers runtime et utilisateur non-root
RUN mkdir -p logs public/data \
    && useradd -m -u 1001 appuser \
    && chown -R appuser:appuser /app \
    && chmod +x docker-entrypoint.sh

# PYTHONPATH permet d'importer scraper depuis src/ sans package
ENV PYTHONPATH=/app/src

USER appuser

EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
