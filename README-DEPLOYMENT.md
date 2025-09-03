# Déploiement Shopping Monitor sur VPS

## 📋 Instructions de déploiement

### 1. Prérequis sur le VPS
- Docker installé
- Répertoire `/seo-tools/shopping/` créé
- Accès aux services PostgreSQL et Redis via docker-compose principal

### 2. Structure des fichiers
```
/seo-tools/
├── docker-compose.yml          # Docker compose principal (géré ailleurs)
└── shopping/                   # Ce projet
    ├── app/                    # Backend FastAPI
    ├── frontend/               # Frontend React (sera buildé)
    ├── static/                 # Frontend buildé (généré)
    ├── Dockerfile              # Configuration Docker
    ├── .env.production         # Variables d'environnement prod
    └── ...
```

### 3. Configuration des chemins
L'application est configurée pour fonctionner sur `https://outils.agence-slashr.fr/shopping/` :

**Backend :**
- `ROOT_PATH=/shopping` dans `.env.production`
- FastAPI configuré avec `root_path=settings.root_path`
- Routes API : `/shopping/api/v1/*`
- Health check : `/shopping/health`

**Frontend :**
- `base: '/shopping/'` dans `vite.config.ts`
- `basename="/shopping"` dans React Router
- API URL : `/shopping` en production

### 4. Variables d'environnement à personnaliser

Modifier `.env.production` :
```bash
# Base de données SQLite (déjà configurée)
DATABASE_URL=sqlite+aiosqlite:///./shopping_monitor.db
DATABASE_URL_SYNC=sqlite:///./shopping_monitor.db

# Redis - adapter selon votre config (optionnel)
REDIS_URL=redis://redis:6379/0

# Sécurité - CHANGER ABSOLUMENT
SECRET_KEY=VOTRE_CLE_SECRETE_TRES_LONGUE_ET_COMPLEXE

# DataForSEO - vos vraies clés API (déjà configurées)
DATAFORSEO_LOGIN=tools@slashr.fr
DATAFORSEO_PASSWORD=d287694ff1bbecca4

# Domaine - adapter si nécessaire
ALLOWED_ORIGINS="https://outils.agence-slashr.fr"
```

### 5. Build et déploiement

```bash
# 1. Copier les fichiers sur le VPS dans /seo-tools/shopping/
rsync -avz . user@vps:/seo-tools/shopping/

# 2. Build de l'image Docker (multi-stage : frontend + backend)
cd /seo-tools/shopping/
docker build -t shopping-monitor .

# 3. Démarrer le container (exemple - adapter selon votre docker-compose)
docker run -d \
  --name shopping-monitor \
  --env-file .env.production \
  --network seo-tools_default \
  -v /seo-tools/shopping/data:/app \
  -p 8000:8000 \
  shopping-monitor
```

### 6. Configuration Caddy

Dans votre Caddyfile principal, ajouter :
```caddy
# Sous-chemin pour Shopping Monitor
outils.agence-slashr.fr {
    handle_path /shopping/* {
        reverse_proxy shopping-monitor:8000
    }
    
    # Autres outils...
}
```

### 7. Migration de la base de données

```bash
# Entrer dans le container
docker exec -it shopping-monitor bash

# Lancer les migrations (SQLite sera créé automatiquement)
alembic upgrade head
```

**Note** : Avec SQLite, la base sera créée automatiquement au premier démarrage. Pas besoin de setup préalable.

### 8. Vérification

- API : https://outils.agence-slashr.fr/shopping/health
- Frontend : https://outils.agence-slashr.fr/shopping/
- Documentation : https://outils.agence-slashr.fr/shopping/docs (si DEBUG=True)

### 9. Monitoring

L'application inclut :
- Health check automatique dans le Dockerfile
- Logs structurés avec des métriques
- Middleware de monitoring des requêtes

### 10. Notes importantes

- **Frontend buildé automatiquement** : Le Dockerfile multi-stage builde le React et l'embarque
- **Pas de Node.js nécessaire** en production
- **Serveur de fichiers statiques** intégré dans FastAPI
- **Configuration flexible** dev/prod avec variables d'environnement
- **Sécurité** : utilisateur non-root dans le container

### 11. Commandes utiles

```bash
# Voir les logs
docker logs shopping-monitor -f

# Redémarrer
docker restart shopping-monitor

# Shell dans le container
docker exec -it shopping-monitor bash

# Rebuild complet
docker build --no-cache -t shopping-monitor .
```