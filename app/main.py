"""Application FastAPI principale pour Shopping Monitor."""

from contextlib import asynccontextmanager
import os
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
import structlog
import time

from app.config import settings
from app.database import init_db, close_db
from app.services.cache_service import cache_service
from app.core.exceptions import ShoppingMonitorException


# Configuration du logger
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie de l'application."""
    # Startup
    logger.info("Démarrage de Shopping Monitor", environment=settings.environment)
    
    try:
        # Initialiser la base de données
        await init_db()
        logger.info("Base de données initialisée")
        
        # Initialiser le cache Redis
        await cache_service.connect()
        
        yield
        
    finally:
        # Shutdown
        logger.info("Arrêt de Shopping Monitor")
        await cache_service.disconnect()
        await close_db()
        logger.info("Connexions fermées")


# Création de l'application FastAPI
app = FastAPI(
    title="Shopping Monitor API",
    description="API de monitoring Google Shopping avec approche projet-centric",
    version="1.0.0",
    root_path=settings.root_path,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# Configuration CORS
if settings.debug:
    # En mode développement, autoriser toutes les origines
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["*"],
    )
else:
    # En production, utiliser la liste configurée
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["*"],
    )


# Middleware de logging des requêtes
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware pour logger les requêtes."""
    start_time = time.time()
    
    # Informations de la requête
    client_ip = request.client.host if request.client else "unknown"
    method = request.method
    url = str(request.url)
    
    logger.info(
        "Requête reçue",
        method=method,
        url=url,
        client_ip=client_ip
    )
    
    # Traitement de la requête
    response = await call_next(request)
    
    # Calcul du temps de traitement
    process_time = time.time() - start_time
    
    logger.info(
        "Requête traitée",
        method=method,
        url=url,
        status_code=response.status_code,
        process_time=f"{process_time:.3f}s"
    )
    
    # Ajouter le temps de traitement aux headers
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


# Gestionnaire d'exceptions global
@app.exception_handler(ShoppingMonitorException)
async def shopping_monitor_exception_handler(request: Request, exc: ShoppingMonitorException):
    """Gestionnaire pour les exceptions métier."""
    logger.error(
        "Erreur métier",
        error_type=exc.__class__.__name__,
        error_message=str(exc),
        url=str(request.url)
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_type,
            "message": exc.message,
            "details": exc.details
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Gestionnaire pour les exceptions générales."""
    logger.error(
        "Erreur inattendue",
        error_type=exc.__class__.__name__,
        error_message=str(exc),
        url=str(request.url),
        exc_info=True
    )
    
    # En production, ne pas exposer les détails techniques
    if settings.environment == "production":
        return JSONResponse(
            status_code=500,
            content={
                "error": "InternalServerError",
                "message": "Une erreur inattendue s'est produite"
            }
        )
    else:
        return JSONResponse(
            status_code=500,
            content={
                "error": exc.__class__.__name__,
                "message": str(exc)
            }
        )


# Routes de base
@app.get("/")
async def root():
    """Endpoint racine."""
    return {
        "message": "Shopping Monitor API",
        "version": "1.0.0",
        "environment": settings.environment,
        "docs": "/docs" if settings.debug else "disabled"
    }


@app.get("/health")
async def health_check():
    """Endpoint de vérification de santé."""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "timestamp": time.time()
    }


# Import et inclusion des routes
from app.api import projects, scraping, analytics

app.include_router(
    projects.router,
    prefix="/api/v1/projects",
    tags=["projects"]
)

app.include_router(
    scraping.router,
    prefix="/api/v1/scraping",
    tags=["scraping"]
)

app.include_router(
    analytics.router,
    prefix="/api/v1/analytics",
    tags=["analytics"]
)

# Servir les fichiers statiques du frontend
static_dir = Path("/app/static")
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    
    # Route pour servir l'index.html sur toutes les routes frontend
    @app.get("/{path:path}")
    async def serve_frontend(path: str):
        """Servir le frontend React pour toutes les routes non-API."""
        # Éviter de servir l'index pour les routes API
        if path.startswith("api/") or path.startswith("docs") or path.startswith("redoc"):
            raise HTTPException(status_code=404, detail="Not found")
        
        # Si c'est un fichier statique, le laisser passer
        static_file = static_dir / path
        if static_file.exists() and static_file.is_file():
            return FileResponse(static_file)
        
        # Sinon, servir index.html pour le routing React
        index_file = static_dir / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        
        raise HTTPException(status_code=404, detail="Frontend not found")

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    ) 