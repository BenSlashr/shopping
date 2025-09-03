"""Service de déduplication des URLs pour Shopping Monitor."""

import hashlib
from typing import List, Dict, Optional, Set, Any
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from datetime import datetime, timedelta
import structlog
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UniqueUrl, SerpUrlMapping, SerpResult
from app.core.exceptions import DatabaseError

logger = structlog.get_logger()


class URLDeduplicationService:
    """Service pour la déduplication et gestion des URLs uniques."""
    
    def __init__(self, session: AsyncSession):
        """
        Initialise le service de déduplication.
        
        Args:
            session: Session de base de données async
        """
        self.session = session
    
    def normalize_url(self, url: str) -> str:
        """
        Normalise une URL pour la déduplication.
        
        Args:
            url: URL à normaliser
            
        Returns:
            URL normalisée
        """
        if not url:
            return ""
        
        try:
            # Parser l'URL
            parsed = urlparse(url.lower().strip())
            
            # Nettoyer le domaine
            domain = parsed.netloc
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # Nettoyer le path
            path = parsed.path.rstrip('/')
            if not path:
                path = '/'
            
            # Normaliser les paramètres de requête
            query_params = parse_qs(parsed.query)
            
            # Supprimer les paramètres de tracking communs
            tracking_params = {
                'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
                'gclid', 'fbclid', 'ref', 'referrer', '_ga', 'mc_eid', 'mc_cid',
                'source', 'campaign', 'medium', 'content', 'term'
            }
            
            cleaned_params = {
                k: v for k, v in query_params.items() 
                if k.lower() not in tracking_params
            }
            
            # Reconstruire la query string
            if cleaned_params:
                # Trier les paramètres pour la consistance
                sorted_params = sorted(cleaned_params.items())
                query_string = urlencode(sorted_params, doseq=True)
            else:
                query_string = ''
            
            # Reconstruire l'URL normalisée
            normalized = urlunparse((
                parsed.scheme or 'https',
                domain,
                path,
                '',  # params
                query_string,
                ''   # fragment
            ))
            
            return normalized
            
        except Exception as e:
            logger.warning(
                "Erreur lors de la normalisation d'URL",
                url=url,
                error=str(e)
            )
            return url.lower().strip()
    
    def generate_url_hash(self, url: str) -> str:
        """
        Génère un hash unique pour une URL.
        
        Args:
            url: URL à hasher
            
        Returns:
            Hash MD5 de l'URL normalisée
        """
        normalized_url = self.normalize_url(url)
        return hashlib.md5(normalized_url.encode('utf-8')).hexdigest()
    
    def extract_domain(self, url: str) -> str:
        """
        Extrait le domaine d'une URL.
        
        Args:
            url: URL source
            
        Returns:
            Domaine extrait
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Supprimer www.
            if domain.startswith('www.'):
                domain = domain[4:]
            
            return domain
            
        except Exception:
            return ""
    
    async def get_or_create_unique_url(
        self,
        url: str,
        product_data: Optional[Dict[str, Any]] = None
    ) -> UniqueUrl:
        """
        Récupère ou crée une URL unique.
        
        Args:
            url: URL à traiter
            product_data: Données du produit (optionnel)
            
        Returns:
            Instance UniqueUrl
        """
        normalized_url = self.normalize_url(url)
        domain = self.extract_domain(url)
        
        try:
            # Chercher si l'URL existe déjà
            stmt = select(UniqueUrl).where(UniqueUrl.url == normalized_url)
            result = await self.session.execute(stmt)
            unique_url = result.scalar_one_or_none()
            
            if unique_url:
                # Mettre à jour les données produit si fournies
                if product_data and not unique_url.product_data:
                    unique_url.product_data = product_data
                    unique_url.scraping_status = "completed"
                    unique_url.last_scraped = datetime.now()
                
                logger.debug("URL unique existante trouvée", url=normalized_url)
                return unique_url
            
            # Créer une nouvelle URL unique
            unique_url = UniqueUrl(
                url=normalized_url,
                domain=domain,
                product_data=product_data,
                scraping_status="completed" if product_data else "pending",
                last_scraped=datetime.now() if product_data else None
            )
            
            self.session.add(unique_url)
            await self.session.flush()  # Pour obtenir l'ID
            
            logger.debug("Nouvelle URL unique créée", url=normalized_url)
            return unique_url
            
        except Exception as e:
            logger.error(
                "Erreur lors de la gestion d'URL unique",
                url=url,
                error=str(e)
            )
            raise DatabaseError(
                "Erreur lors de la gestion d'URL unique",
                details={"url": url, "error": str(e)}
            )
    
    async def deduplicate_serp_results(
        self,
        serp_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Déduplique une liste de résultats SERP par URL.
        
        Args:
            serp_results: Liste des résultats SERP bruts
            
        Returns:
            Liste des résultats dédupliqués avec unique_url_id
        """
        logger.info(
            "Début de la déduplication SERP",
            results_count=len(serp_results)
        )
        
        deduplicated = []
        seen_urls = set()
        url_to_unique_id = {}
        
        try:
            for result in serp_results:
                url = result.get("url", "")
                if not url:
                    continue
                
                normalized_url = self.normalize_url(url)
                
                # Vérifier si on a déjà traité cette URL
                if normalized_url in seen_urls:
                    # Ajouter l'ID de l'URL unique existante
                    result["unique_url_id"] = url_to_unique_id[normalized_url]
                    deduplicated.append(result)
                    continue
                
                # Extraire les données produit du résultat SERP
                product_data = {
                    "title": result.get("title"),
                    "description": result.get("description"),
                    "price": result.get("price"),
                    "currency": result.get("currency"),
                    "merchant": result.get("merchant", {}).get("name"),
                    "rating": result.get("rating", {}).get("rating_value"),
                    "reviews_count": result.get("rating", {}).get("reviews_count"),
                    "image_url": result.get("image_url"),
                    "scraped_at": datetime.now().isoformat()
                }
                
                # Créer ou récupérer l'URL unique
                unique_url = await self.get_or_create_unique_url(
                    url=url,
                    product_data=product_data
                )
                
                # Ajouter à nos structures de tracking
                seen_urls.add(normalized_url)
                url_to_unique_id[normalized_url] = unique_url.id
                
                # Ajouter l'ID à notre résultat
                result["unique_url_id"] = unique_url.id
                result["normalized_url"] = normalized_url
                
                deduplicated.append(result)
            
            logger.info(
                "Déduplication terminée",
                original_count=len(serp_results),
                deduplicated_count=len(deduplicated),
                unique_urls=len(seen_urls)
            )
            
            return deduplicated
            
        except Exception as e:
            logger.error(
                "Erreur lors de la déduplication",
                error=str(e),
                results_count=len(serp_results)
            )
            raise DatabaseError(
                "Erreur lors de la déduplication des résultats SERP",
                details={"error": str(e)}
            )
    
    async def create_serp_url_mappings(
        self,
        serp_result_ids: List[str],
        unique_url_ids: List[str]
    ) -> List[SerpUrlMapping]:
        """
        Crée les mappings entre résultats SERP et URLs uniques.
        
        Args:
            serp_result_ids: Liste des IDs de résultats SERP
            unique_url_ids: Liste des IDs d'URLs uniques correspondants
            
        Returns:
            Liste des mappings créés
        """
        if len(serp_result_ids) != len(unique_url_ids):
            raise ValueError("Les listes d'IDs doivent avoir la même longueur")
        
        mappings = []
        
        try:
            for serp_id, url_id in zip(serp_result_ids, unique_url_ids):
                mapping = SerpUrlMapping(
                    serp_result_id=serp_id,
                    unique_url_id=url_id
                )
                mappings.append(mapping)
                self.session.add(mapping)
            
            await self.session.flush()
            
            logger.info(
                "Mappings SERP-URL créés",
                mappings_count=len(mappings)
            )
            
            return mappings
            
        except Exception as e:
            logger.error(
                "Erreur lors de la création des mappings",
                error=str(e)
            )
            raise DatabaseError(
                "Erreur lors de la création des mappings SERP-URL",
                details={"error": str(e)}
            )
    
    async def get_urls_needing_scraping(
        self,
        limit: int = 100,
        max_age_hours: int = 24
    ) -> List[UniqueUrl]:
        """
        Récupère les URLs qui ont besoin d'être scrapées.
        
        Args:
            limit: Nombre maximum d'URLs à retourner
            max_age_hours: Âge maximum en heures pour considérer qu'un scraping est obsolète
            
        Returns:
            Liste des URLs à scraper
        """
        try:
            # Calculer la date limite
            cutoff_date = datetime.now() - timedelta(hours=max_age_hours)
            
            # Requête pour les URLs qui ont besoin d'être scrapées
            stmt = select(UniqueUrl).where(
                and_(
                    UniqueUrl.scraping_status.in_(["pending", "failed"]),
                    or_(
                        UniqueUrl.last_scraped.is_(None),
                        UniqueUrl.last_scraped < cutoff_date
                    )
                )
            ).limit(limit)
            
            result = await self.session.execute(stmt)
            urls = result.scalars().all()
            
            logger.info(
                "URLs nécessitant un scraping trouvées",
                count=len(urls),
                limit=limit
            )
            
            return urls
            
        except Exception as e:
            logger.error(
                "Erreur lors de la récupération des URLs à scraper",
                error=str(e)
            )
            raise DatabaseError(
                "Erreur lors de la récupération des URLs à scraper",
                details={"error": str(e)}
            )
    
    async def update_scraping_status(
        self,
        unique_url_id: str,
        status: str,
        product_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> None:
        """
        Met à jour le statut de scraping d'une URL unique.
        
        Args:
            unique_url_id: ID de l'URL unique
            status: Nouveau statut (pending, completed, failed)
            product_data: Données du produit (si completed)
            error_message: Message d'erreur (si failed)
        """
        try:
            stmt = select(UniqueUrl).where(UniqueUrl.id == unique_url_id)
            result = await self.session.execute(stmt)
            unique_url = result.scalar_one_or_none()
            
            if not unique_url:
                logger.warning("URL unique non trouvée", unique_url_id=unique_url_id)
                return
            
            unique_url.scraping_status = status
            unique_url.last_scraped = datetime.now()
            
            if product_data:
                unique_url.product_data = product_data
            
            if error_message and status == "failed":
                if not unique_url.product_data:
                    unique_url.product_data = {}
                unique_url.product_data["error"] = error_message
            
            logger.debug(
                "Statut de scraping mis à jour",
                unique_url_id=unique_url_id,
                status=status
            )
            
        except Exception as e:
            logger.error(
                "Erreur lors de la mise à jour du statut",
                unique_url_id=unique_url_id,
                error=str(e)
            )
            raise DatabaseError(
                "Erreur lors de la mise à jour du statut de scraping",
                details={"unique_url_id": unique_url_id, "error": str(e)}
            ) 