"""Configuration de l'application avec Pydantic Settings."""

from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuration de l'application."""
    
    # Base de données
    database_url: str = Field(
        default="postgresql+asyncpg://shopping_user:shopping_password@localhost:5432/shopping_monitor",
        description="URL de connexion à PostgreSQL (async)"
    )
    database_url_sync: str = Field(
        default="postgresql://shopping_user:shopping_password@localhost:5432/shopping_monitor",
        description="URL de connexion à PostgreSQL (sync pour Alembic)"
    )
    
    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="URL de connexion à Redis"
    )
    
    # DataForSEO API
    dataforseo_login: str = Field(
        default="",
        description="Login DataForSEO API"
    )
    dataforseo_password: str = Field(
        default="",
        description="Mot de passe DataForSEO API"
    )
    dataforseo_base_url: str = Field(
        default="https://api.dataforseo.com/v3",
        description="URL de base DataForSEO API"
    )
    
    # FastAPI Security
    secret_key: str = Field(
        default="your-super-secret-key-change-this-in-production",
        description="Clé secrète pour JWT"
    )
    algorithm: str = Field(
        default="HS256",
        description="Algorithme de chiffrement JWT"
    )
    access_token_expire_minutes: int = Field(
        default=30,
        description="Durée d'expiration des tokens en minutes"
    )
    
    # Environnement
    environment: str = Field(
        default="development",
        description="Environnement (development, staging, production)"
    )
    debug: bool = Field(
        default=True,
        description="Mode debug"
    )
    log_level: str = Field(
        default="INFO",
        description="Niveau de log"
    )
    
    # CORS
    allowed_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173",
        description="Origines autorisées pour CORS (séparées par des virgules)"
    )
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Convertit la chaîne d'origines en liste."""
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]
    
    # API Configuration
    root_path: str = Field(
        default="",
        description="Base path pour l'API (ex: /shopping)"
    )
    
    # Scraping
    max_concurrent_requests: int = Field(
        default=5,
        description="Nombre maximum de requêtes simultanées"
    )
    request_delay_seconds: float = Field(
        default=1.0,
        description="Délai entre les requêtes en secondes"
    )
    max_retries: int = Field(
        default=3,
        description="Nombre maximum de tentatives"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Instance globale des settings
settings = Settings() 