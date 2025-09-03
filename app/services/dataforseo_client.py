"""Client DataForSEO pour Shopping Monitor."""

import asyncio
import base64
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import structlog
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

from app.config import settings
from app.core.exceptions import (
    ExternalAPIError,
    RateLimitError,
    ConfigurationError
)

logger = structlog.get_logger()


class DataForSEOClient:
    """Client pour l'API DataForSEO avec gestion d'erreurs et retry."""
    
    def __init__(self):
        """Initialise le client DataForSEO."""
        if not settings.dataforseo_login or not settings.dataforseo_password:
            raise ConfigurationError(
                "Identifiants DataForSEO manquants",
                details={
                    "login_configured": bool(settings.dataforseo_login),
                    "password_configured": bool(settings.dataforseo_password)
                }
            )
        
        self.base_url = settings.dataforseo_base_url
        self.login = settings.dataforseo_login
        self.password = settings.dataforseo_password
        
        # Créer les headers d'authentification
        credentials = f"{self.login}:{self.password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        self.headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json",
            "User-Agent": "ShoppingMonitor/1.0"
        }
        
        # Configuration du client HTTP
        self.timeout = httpx.Timeout(30.0, connect=10.0)
        self.limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
        
        logger.info("Client DataForSEO initialisé", base_url=self.base_url)
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Effectue une requête HTTP avec gestion d'erreurs."""
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        logger.debug(
            "Requête DataForSEO",
            method=method,
            url=url,
            data_size=len(json.dumps(data)) if data else 0
        )
        
        async with httpx.AsyncClient(
            headers=self.headers,
            timeout=self.timeout,
            limits=self.limits
        ) as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params
                )
                
                # Vérifier le statut de la réponse
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    raise RateLimitError("DataForSEO", retry_after)
                
                response.raise_for_status()
                
                # Parser la réponse JSON
                response_data = response.json()
                
                logger.debug(
                    "Réponse DataForSEO reçue",
                    status_code=response.status_code,
                    response_size=len(response.text)
                )
                
                return response_data
                
            except httpx.HTTPStatusError as e:
                logger.error(
                    "Erreur HTTP DataForSEO",
                    status_code=e.response.status_code,
                    response_text=e.response.text[:500]
                )
                
                raise ExternalAPIError(
                    service="DataForSEO",
                    message=f"Erreur HTTP {e.response.status_code}: {e.response.text[:200]}",
                    status_code=e.response.status_code,
                    details={
                        "endpoint": endpoint,
                        "method": method,
                        "response_text": e.response.text[:500]
                    }
                )
            
            except httpx.RequestError as e:
                logger.error("Erreur de connexion DataForSEO", error=str(e))
                
                raise ExternalAPIError(
                    service="DataForSEO",
                    message=f"Erreur de connexion: {str(e)}",
                    details={
                        "endpoint": endpoint,
                        "method": method,
                        "error_type": type(e).__name__
                    }
                )
            
            except json.JSONDecodeError as e:
                logger.error("Erreur de parsing JSON DataForSEO", error=str(e))
                
                raise ExternalAPIError(
                    service="DataForSEO",
                    message="Réponse JSON invalide",
                    details={
                        "endpoint": endpoint,
                        "method": method,
                        "json_error": str(e)
                    }
                )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.RequestError, ExternalAPIError)),
        before_sleep=before_sleep_log(logger, "warning")
    )
    async def get_shopping_serp(
        self,
        keyword: str,
        location: str = "France",
        language: str = "fr",
        max_results: int = 100
    ) -> Dict[str, Any]:
        """
        Récupère les résultats SERP Google Shopping pour un mot-clé.
        
        Args:
            keyword: Mot-clé à rechercher
            location: Localisation (défaut: France)
            language: Langue (défaut: fr)
            max_results: Nombre maximum de résultats (défaut: 100)
            
        Returns:
            Dict contenant les résultats SERP
        """
        logger.info(
            "Scraping SERP Google Shopping",
            keyword=keyword,
            location=location,
            language=language
        )
        
        payload = [{
            "keyword": keyword,
            "location_name": location,
            "language_name": language,
            "device": "desktop",
            "os": "windows",
            "se_domain": "google.fr",
            "depth": max_results,
            "include_serp_info": True,
            "include_html": False,
            "custom_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "tag": f"shopping_monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }]
        
        try:
            response = await self._make_request(
                method="POST",
                endpoint="serp/google/shopping/live/advanced",
                data=payload
            )
            
            # Vérifier la structure de la réponse
            if not response.get("tasks"):
                raise ExternalAPIError(
                    service="DataForSEO",
                    message="Réponse invalide: pas de tâches",
                    details={"response": response}
                )
            
            task = response["tasks"][0]
            if task.get("status_code") != 20000:
                error_message = task.get("status_message", "Erreur inconnue")
                raise ExternalAPIError(
                    service="DataForSEO",
                    message=f"Erreur de tâche: {error_message}",
                    details={
                        "status_code": task.get("status_code"),
                        "status_message": error_message
                    }
                )
            
            results = task.get("result", [])
            if not results:
                logger.warning("Aucun résultat SERP", keyword=keyword)
                return {"items": [], "total_count": 0}
            
            serp_result = results[0]
            items = serp_result.get("items", [])
            
            logger.info(
                "SERP récupérée avec succès",
                keyword=keyword,
                results_count=len(items),
                total_count=serp_result.get("total_count", 0)
            )
            
            return {
                "items": items,
                "total_count": serp_result.get("total_count", 0),
                "serp_info": serp_result.get("serp_info", {}),
                "scraped_at": datetime.now().isoformat(),
                "keyword": keyword,
                "location": location,
                "language": language
            }
            
        except Exception as e:
            logger.error(
                "Erreur lors du scraping SERP",
                keyword=keyword,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=8),
        retry=retry_if_exception_type((httpx.RequestError, ExternalAPIError)),
        before_sleep=before_sleep_log(logger, "warning")
    )
    async def get_search_volume(
        self,
        keywords: List[str],
        location: str = "France",
        language: str = "fr"
    ) -> Dict[str, Any]:
        """
        Récupère le volume de recherche pour une liste de mots-clés.
        
        Args:
            keywords: Liste des mots-clés
            location: Localisation (défaut: France)
            language: Langue (défaut: fr)
            
        Returns:
            Dict contenant les volumes de recherche
        """
        logger.info(
            "Récupération volumes de recherche",
            keywords_count=len(keywords),
            location=location
        )
        
        payload = [{
            "keywords": keywords,
            "location_name": location,
            "language_name": language,
            "tag": f"volume_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }]
        
        try:
            response = await self._make_request(
                method="POST",
                endpoint="keywords_data/google/search_volume/live",
                data=payload
            )
            
            # Vérifier la structure de la réponse
            if not response.get("tasks"):
                raise ExternalAPIError(
                    service="DataForSEO",
                    message="Réponse invalide: pas de tâches",
                    details={"response": response}
                )
            
            task = response["tasks"][0]
            if task.get("status_code") != 20000:
                error_message = task.get("status_message", "Erreur inconnue")
                raise ExternalAPIError(
                    service="DataForSEO",
                    message=f"Erreur de tâche: {error_message}",
                    details={
                        "status_code": task.get("status_code"),
                        "status_message": error_message
                    }
                )
            
            results = task.get("result", [])
            
            logger.info(
                "Volumes de recherche récupérés",
                keywords_count=len(keywords),
                results_count=len(results)
            )
            
            return {
                "results": results,
                "scraped_at": datetime.now().isoformat(),
                "location": location,
                "language": language
            }
            
        except Exception as e:
            logger.error(
                "Erreur lors de la récupération des volumes",
                keywords_count=len(keywords),
                error=str(e),
                error_type=type(e).__name__
            )
            raise
    
    async def batch_scrape_keywords(
        self,
        keywords_data: List[Dict[str, Any]],
        max_concurrent: Optional[int] = None,
        delay_between_requests: float = 1.0
    ) -> List[Dict[str, Any]]:
        """
        Scrape plusieurs mots-clés en batch avec limitation de concurrence.
        
        Args:
            keywords_data: Liste des données de mots-clés à scraper
            max_concurrent: Nombre maximum de requêtes simultanées
            delay_between_requests: Délai entre les requêtes en secondes
            
        Returns:
            Liste des résultats de scraping
        """
        if max_concurrent is None:
            max_concurrent = settings.max_concurrent_requests
        
        logger.info(
            "Début du scraping batch",
            keywords_count=len(keywords_data),
            max_concurrent=max_concurrent,
            delay=delay_between_requests
        )
        
        # Créer un semaphore pour limiter la concurrence
        semaphore = asyncio.Semaphore(max_concurrent)
        results = []
        
        async def scrape_single_keyword(keyword_data: Dict[str, Any]) -> Dict[str, Any]:
            """Scrape un seul mot-clé avec semaphore."""
            async with semaphore:
                try:
                    # Délai entre les requêtes
                    if delay_between_requests > 0:
                        await asyncio.sleep(delay_between_requests)
                    
                    result = await self.get_shopping_serp(
                        keyword=keyword_data["keyword"],
                        location=keyword_data.get("location", "France"),
                        language=keyword_data.get("language", "fr"),
                        max_results=keyword_data.get("max_results", 100)
                    )
                    
                    # Ajouter les métadonnées du mot-clé
                    result.update({
                        "keyword_id": keyword_data.get("keyword_id"),
                        "project_id": keyword_data.get("project_id"),
                        "success": True,
                        "error": None
                    })
                    
                    return result
                    
                except Exception as e:
                    logger.error(
                        "Erreur scraping mot-clé",
                        keyword=keyword_data["keyword"],
                        error=str(e)
                    )
                    
                    return {
                        "keyword_id": keyword_data.get("keyword_id"),
                        "project_id": keyword_data.get("project_id"),
                        "keyword": keyword_data["keyword"],
                        "success": False,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "scraped_at": datetime.now().isoformat()
                    }
        
        # Lancer toutes les tâches de scraping
        tasks = [scrape_single_keyword(kw_data) for kw_data in keywords_data]
        results = await asyncio.gather(*tasks, return_exceptions=False)
        
        # Compter les succès et échecs
        successful = sum(1 for r in results if r.get("success", False))
        failed = len(results) - successful
        
        logger.info(
            "Scraping batch terminé",
            total=len(results),
            successful=successful,
            failed=failed
        )
        
        return results
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test la connexion à l'API DataForSEO.
        
        Returns:
            Dict avec les informations de connexion
        """
        logger.info("Test de connexion DataForSEO")
        
        try:
            response = await self._make_request(
                method="GET",
                endpoint="user"
            )
            
            user_info = response.get("tasks", [{}])[0].get("result", {})
            
            logger.info(
                "Connexion DataForSEO réussie",
                user=user_info.get("login"),
                balance=user_info.get("money", {}).get("balance")
            )
            
            return {
                "connected": True,
                "user_info": user_info,
                "tested_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error("Échec du test de connexion DataForSEO", error=str(e))
            
            return {
                "connected": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "tested_at": datetime.now().isoformat()
            } 