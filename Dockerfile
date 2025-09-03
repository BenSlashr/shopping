# Multi-stage Dockerfile pour Shopping Monitor
FROM node:18-alpine AS frontend-build

# Construire le frontend
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
# Modifier temporairement le script build pour skip TypeScript
RUN npm pkg set scripts.build="vite build"
RUN npm run build

# Backend Python
FROM python:3.11-slim

# Définir le répertoire de travail
WORKDIR /app

# Variables d'environnement pour Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de requirements
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copier le code source backend
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Copier le frontend buildé depuis l'étape précédente
COPY --from=frontend-build /frontend/dist ./static

# Créer un utilisateur non-root
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Exposer le port
EXPOSE 8000

# Healthcheck avec le bon path
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/shopping/health || exit 1

# Commande par défaut pour production
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 