"""Configuration de la base de données SQLAlchemy."""

import os
from typing import AsyncGenerator

from sqlalchemy import create_engine, String
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import structlog

from app.config import settings

# Configuration du logger
logger = structlog.get_logger()

# Base pour les modèles
Base = declarative_base()

# Moteurs de base de données
async_engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
)

sync_engine = create_engine(
    settings.database_url_sync,
    echo=settings.debug,
    pool_pre_ping=True,
)

# Sessions
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine
)

# Helper pour les types UUID selon la base de données
def get_uuid_column():
    """Retourne le type de colonne approprié pour les UUIDs selon la base de données."""
    if settings.database_url.startswith("sqlite"):
        return String(36)  # UUID sous forme de string pour SQLite
    else:
        try:
            from sqlalchemy.dialects.postgresql import UUID
            return UUID(as_uuid=True)
        except ImportError:
            return String(36)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Générateur de session async."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def get_sync_session():
    """Générateur de session sync."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def init_db():
    """Initialise la base de données."""
    import os
    from urllib.parse import urlparse
    
    # Log de la configuration de la base de données
    logger.info(
        "Initialisation de la base de données",
        database_url=settings.database_url,
        database_url_sync=settings.database_url_sync
    )
    
    # Pour SQLite, afficher le chemin absolu du fichier
    if settings.database_url.startswith("sqlite"):
        parsed_url = urlparse(settings.database_url)
        db_path = parsed_url.path
        if db_path.startswith("///"):
            # Chemin absolu : sqlite:///path/to/db.db
            actual_path = db_path[3:]  # Enlever les 3 premiers /
        else:
            # Chemin relatif : sqlite://./db.db
            actual_path = db_path[1:]  # Enlever le premier /
            
        # Résoudre le chemin complet
        full_path = os.path.abspath(actual_path)
        
        logger.info(
            "Configuration SQLite détectée",
            db_file_path=actual_path,
            absolute_path=full_path,
            file_exists=os.path.exists(full_path),
            working_directory=os.getcwd()
        )
    
    async with async_engine.begin() as conn:
        # Créer toutes les tables
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Base de données initialisée avec succès")


async def close_db():
    """Ferme les connexions à la base de données."""
    logger.info("Fermeture des connexions à la base de données")
    
    await async_engine.dispose()
    sync_engine.dispose()
    
    logger.info("Connexions fermées") 