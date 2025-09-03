"""Service de cache Redis pour optimiser les performances des analytics."""

import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Any, Dict
import asyncio

import redis.asyncio as redis
import structlog

from app.config import settings

logger = structlog.get_logger()


class CacheService:
    """Service de cache Redis pour les calculs analytics."""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.default_ttl = 3600  # 1 heure par défaut
        self.cache_prefix = "shopping_monitor"
    
    async def connect(self):
        """Initialise la connexion Redis."""
        try:
            self.redis_client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            # Test de connexion
            await self.redis_client.ping()
            logger.info("Connexion Redis établie", redis_url=settings.redis_url)
        except Exception as e:
            logger.warning("Impossible de se connecter à Redis", error=str(e))
            self.redis_client = None
    
    async def disconnect(self):
        """Ferme la connexion Redis."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Connexion Redis fermée")
    
    def _generate_cache_key(self, prefix: str, **kwargs) -> str:
        """Génère une clé de cache unique basée sur les paramètres."""
        # Créer une chaîne unique à partir des paramètres
        params_str = json.dumps(kwargs, sort_keys=True, default=str)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()
        
        return f"{self.cache_prefix}:{prefix}:{params_hash}"
    
    async def get(self, cache_key: str) -> Optional[Any]:
        """Récupère une valeur du cache."""
        if not self.redis_client:
            return None
        
        try:
            cached_data = await self.redis_client.get(cache_key)
            if cached_data:
                logger.debug("Cache hit", cache_key=cache_key)
                return json.loads(cached_data)
            else:
                logger.debug("Cache miss", cache_key=cache_key)
                return None
        except Exception as e:
            logger.error("Erreur lecture cache", error=str(e), cache_key=cache_key)
            return None
    
    async def set(self, cache_key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Stocke une valeur dans le cache."""
        if not self.redis_client:
            return False
        
        try:
            ttl = ttl or self.default_ttl
            serialized_value = json.dumps(value, default=str)
            
            await self.redis_client.setex(cache_key, ttl, serialized_value)
            logger.debug("Cache set", cache_key=cache_key, ttl=ttl)
            return True
        except Exception as e:
            logger.error("Erreur écriture cache", error=str(e), cache_key=cache_key)
            return False
    
    async def delete(self, cache_key: str) -> bool:
        """Supprime une clé du cache."""
        if not self.redis_client:
            return False
        
        try:
            result = await self.redis_client.delete(cache_key)
            logger.debug("Cache delete", cache_key=cache_key, deleted=bool(result))
            return bool(result)
        except Exception as e:
            logger.error("Erreur suppression cache", error=str(e), cache_key=cache_key)
            return False
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalide toutes les clés correspondant à un pattern."""
        if not self.redis_client:
            return 0
        
        try:
            keys = await self.redis_client.keys(f"{self.cache_prefix}:{pattern}*")
            if keys:
                deleted = await self.redis_client.delete(*keys)
                logger.info("Cache pattern invalidated", pattern=pattern, deleted=deleted)
                return deleted
            return 0
        except Exception as e:
            logger.error("Erreur invalidation pattern", error=str(e), pattern=pattern)
            return 0
    
    # Méthodes spécialisées pour les analytics
    
    async def get_share_of_voice(
        self, project_id: str, period_start: datetime, period_end: datetime
    ) -> Optional[Dict]:
        """Récupère le Share of Voice du cache."""
        cache_key = self._generate_cache_key(
            "share_of_voice",
            project_id=project_id,
            period_start=period_start,
            period_end=period_end
        )
        return await self.get(cache_key)
    
    async def set_share_of_voice(
        self, project_id: str, period_start: datetime, period_end: datetime, data: Dict
    ) -> bool:
        """Stocke le Share of Voice dans le cache."""
        cache_key = self._generate_cache_key(
            "share_of_voice",
            project_id=project_id,
            period_start=period_start,
            period_end=period_end
        )
        # TTL plus long pour les données historiques
        ttl = 7200 if period_end < datetime.utcnow() - timedelta(days=1) else 1800
        return await self.set(cache_key, data, ttl)
    
    async def get_position_matrix(
        self, project_id: str, period_start: datetime, period_end: datetime
    ) -> Optional[Dict]:
        """Récupère la matrice de positions du cache."""
        cache_key = self._generate_cache_key(
            "position_matrix",
            project_id=project_id,
            period_start=period_start,
            period_end=period_end
        )
        return await self.get(cache_key)
    
    async def set_position_matrix(
        self, project_id: str, period_start: datetime, period_end: datetime, data: Dict
    ) -> bool:
        """Stocke la matrice de positions dans le cache."""
        cache_key = self._generate_cache_key(
            "position_matrix",
            project_id=project_id,
            period_start=period_start,
            period_end=period_end
        )
        ttl = 7200 if period_end < datetime.utcnow() - timedelta(days=1) else 1800
        return await self.set(cache_key, data, ttl)
    
    async def get_dashboard_metrics(self, project_id: str) -> Optional[Dict]:
        """Récupère les métriques dashboard du cache."""
        cache_key = self._generate_cache_key("dashboard", project_id=project_id)
        return await self.get(cache_key)
    
    async def set_dashboard_metrics(self, project_id: str, data: Dict) -> bool:
        """Stocke les métriques dashboard dans le cache."""
        cache_key = self._generate_cache_key("dashboard", project_id=project_id)
        # TTL court pour le dashboard (données temps réel)
        return await self.set(cache_key, data, 300)  # 5 minutes
    
    async def get_opportunities(
        self, project_id: str, period_start: datetime, period_end: datetime
    ) -> Optional[Dict]:
        """Récupère les opportunités du cache."""
        cache_key = self._generate_cache_key(
            "opportunities",
            project_id=project_id,
            period_start=period_start,
            period_end=period_end
        )
        return await self.get(cache_key)
    
    async def set_opportunities(
        self, project_id: str, period_start: datetime, period_end: datetime, data: Dict
    ) -> bool:
        """Stocke les opportunités dans le cache."""
        cache_key = self._generate_cache_key(
            "opportunities",
            project_id=project_id,
            period_start=period_start,
            period_end=period_end
        )
        # TTL moyen pour les opportunités
        return await self.set(cache_key, data, 3600)  # 1 heure
    
    async def invalidate_project_cache(self, project_id: str):
        """Invalide tout le cache d'un projet."""
        patterns = [
            f"share_of_voice:*project_id*{project_id}*",
            f"position_matrix:*project_id*{project_id}*",
            f"dashboard:*project_id*{project_id}*",
            f"opportunities:*project_id*{project_id}*",
            f"trends:*project_id*{project_id}*",
            f"competitors:*project_id*{project_id}*"
        ]
        
        total_deleted = 0
        for pattern in patterns:
            deleted = await self.invalidate_pattern(pattern)
            total_deleted += deleted
        
        logger.info("Cache projet invalidé", project_id=project_id, total_deleted=total_deleted)
        return total_deleted


# Instance globale du service de cache
cache_service = CacheService()


async def get_cache_service() -> CacheService:
    """Dépendance FastAPI pour le service de cache."""
    return cache_service 