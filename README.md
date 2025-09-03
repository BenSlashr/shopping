# 🛒 Shopping Monitor

Outil de monitoring Google Shopping avec approche projet-centric pour comparer performance vs concurrents.

## 🎯 Fonctionnalités

- **Monitoring multi-projets** : Organisez vos campagnes par projet
- **Tracking concurrentiel** : Surveillez vos concurrents automatiquement  
- **Analytics avancées** : Part de voix, matrice de positions, opportunités
- **API DataForSEO** : Données SERP Google Shopping en temps réel
- **Dashboard interactif** : Interface React moderne
- **Architecture évolutive** : FastAPI + PostgreSQL + Redis

## 🏗️ Architecture

### Backend
- **FastAPI** : API REST haute performance
- **SQLAlchemy** : ORM avec support async
- **PostgreSQL** : Base de données principale
- **Redis** : Cache et sessions
- **Alembic** : Migrations de base de données

### Frontend  
- **React** : Interface utilisateur moderne
- **Chart.js/Recharts** : Visualisations de données
- **Material-UI** : Composants UI

## 🚀 Installation

### Prérequis

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (recommandé)
- PostgreSQL 15+ (si installation locale)
- Redis 7+ (si installation locale)

### 1. Cloner le projet

```bash
git clone <repository-url>
cd shopping-monito
```

### 2. Configuration environnement

```bash
cp env.example .env
# Éditer .env avec vos configurations
```

### 3. Installation avec Docker (Recommandé)

```bash
# Démarrer PostgreSQL et Redis
docker-compose up postgres redis

# Ou avec pgAdmin pour la gestion DB
docker-compose --profile tools up postgres redis pgadmin
```

### 4. Installation locale

```bash
# Backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou venv\Scripts\activate  # Windows

pip install -r requirements.txt

# Frontend (dans un autre terminal)
cd frontend
npm install
```

## 🗄️ Base de données

### Migrations avec Alembic

```bash
# Créer une migration
alembic revision --autogenerate -m "Description"

# Appliquer les migrations
alembic upgrade head

# Revenir en arrière
alembic downgrade -1
```

### Structure des tables

```sql
-- Projets (entité principale)
projects (id, name, description, created_at, updated_at, is_active)

-- Concurrents par projet  
competitors (id, project_id, name, domain, brand_name, is_main_brand)

-- Mots-clés par projet
keywords (id, project_id, keyword, location, language, search_volume, is_active)

-- Résultats SERP (données DataForSEO)
serp_results (id, project_id, keyword_id, competitor_id, position, price, rating, ...)

-- URLs uniques (déduplication)
unique_urls (id, url, domain, product_data, scraping_status)
```

## 🔧 Configuration

### Variables d'environnement (.env)

```bash
# Base de données
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/shopping_monitor
DATABASE_URL_SYNC=postgresql://user:password@localhost:5432/shopping_monitor

# Redis
REDIS_URL=redis://localhost:6379/0

# DataForSEO API
DATAFORSEO_LOGIN=your_login
DATAFORSEO_PASSWORD=your_password

# FastAPI
SECRET_KEY=your-super-secret-key
DEBUG=True
ENVIRONMENT=development
```

## 🚦 Démarrage

### Avec Docker

```bash
# Services uniquement (DB + Redis)
docker-compose up postgres redis

# Application complète
docker-compose --profile full up

# Avec outils de développement
docker-compose --profile tools up
```

### Installation locale

```bash
# Backend (terminal 1)
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (terminal 2) 
cd frontend
npm start
```

## 📊 Utilisation

### 1. Créer un projet

```bash
curl -X POST "http://localhost:8000/api/v1/projects" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mon Projet E-commerce",
    "description": "Monitoring produits électronique"
  }'
```

### 2. Ajouter des concurrents

```bash
curl -X POST "http://localhost:8000/api/v1/projects/{project_id}/competitors" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Amazon",
    "domain": "amazon.fr",
    "brand_name": "Amazon",
    "is_main_brand": false
  }'
```

### 3. Ajouter des mots-clés

```bash
curl -X POST "http://localhost:8000/api/v1/projects/{project_id}/keywords" \
  -H "Content-Type: application/json" \
  -d '{
    "keyword": "smartphone samsung",
    "location": "France",
    "language": "fr"
  }'
```

### 4. Lancer le scraping

```bash
curl -X POST "http://localhost:8000/api/v1/projects/{project_id}/scrape"
```

## 📈 Analytics

### Endpoints disponibles

- `GET /api/v1/projects/{id}/dashboard` - Métriques globales
- `GET /api/v1/projects/{id}/share-of-voice` - Part de voix
- `GET /api/v1/projects/{id}/position-matrix` - Matrice positions
- `GET /api/v1/projects/{id}/opportunities` - Opportunités manquées
- `GET /api/v1/projects/{id}/competitor-comparison` - Comparatif
- `GET /api/v1/projects/{id}/trend-analysis` - Analyses tendances

### Métriques calculées

- **Part de voix** : % d'apparitions vs concurrents
- **Score de visibilité** : Pondération position × volume recherche
- **Position moyenne** : Moyenne des positions sur tous les mots-clés
- **Compétitivité prix** : Positionnement prix vs marché

## 🔌 API DataForSEO

### Configuration

1. Créer un compte sur [DataForSEO](https://dataforseo.com/)
2. Récupérer vos identifiants API
3. Les ajouter dans `.env`

### Endpoints utilisés

- `serp/google/shopping/live/advanced` - SERP Google Shopping
- `keywords_data/google/search_volume/live` - Volume de recherche

## 🧪 Tests

```bash
# Tests unitaires
pytest

# Tests avec coverage
pytest --cov=app --cov-report=html

# Tests d'intégration
pytest tests/integration/

# Tests de charge
pytest tests/load/
```

## 📝 Développement

### Structure du projet

```
shopping-monito/
├── app/                    # Backend FastAPI
│   ├── models/            # Modèles SQLAlchemy
│   ├── schemas/           # Schemas Pydantic
│   ├── api/               # Routes FastAPI
│   ├── services/          # Logique métier
│   ├── core/              # Utilitaires
│   └── main.py            # Point d'entrée
├── frontend/              # Application React
├── alembic/               # Migrations DB
├── tests/                 # Tests
├── docker-compose.yml     # Services Docker
└── requirements.txt       # Dépendances Python
```

### Conventions de code

- **Python** : Black, isort, flake8, mypy
- **JavaScript** : ESLint, Prettier
- **Commits** : Conventional Commits
- **Branches** : GitFlow

### Ajout d'une nouvelle fonctionnalité

1. Créer une branche `feature/nom-fonctionnalite`
2. Ajouter les modèles SQLAlchemy si nécessaire
3. Créer les schemas Pydantic
4. Implémenter les services métier
5. Ajouter les routes API
6. Écrire les tests
7. Mettre à jour la documentation

## 🚀 Déploiement

### Production

```bash
# Build des images
docker-compose -f docker-compose.prod.yml build

# Déploiement
docker-compose -f docker-compose.prod.yml up -d

# Migrations
docker-compose exec api alembic upgrade head
```

### Variables d'environnement production

```bash
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=<strong-secret-key>
DATABASE_URL=<production-db-url>
REDIS_URL=<production-redis-url>
```

## 📚 Documentation

- **API** : http://localhost:8000/docs (Swagger)
- **ReDoc** : http://localhost:8000/redoc
- **pgAdmin** : http://localhost:5050 (si activé)

## 🤝 Contribution

1. Fork du projet
2. Créer une branche feature
3. Commits avec messages clairs
4. Tests pour les nouvelles fonctionnalités
5. Pull request avec description détaillée

## 📄 Licence

MIT License - voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 🆘 Support

- **Issues** : Utiliser GitHub Issues
- **Discussions** : GitHub Discussions
- **Email** : support@shoppingmonitor.com

---

**Développé avec ❤️ pour le monitoring e-commerce** 