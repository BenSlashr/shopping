"""Service principal de scraping pour Shopping Monitor."""

import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime
from uuid import UUID
import structlog
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Project, Keyword, SerpResult, Competitor
from app.services.dataforseo_client import DataForSEOClient
from app.services.url_deduplication import URLDeduplicationService
from app.services.competitor_detection import CompetitorDetectionService
from app.core.exceptions import (
    DatabaseError,
    ScrapingError,
    NotFoundError,
    ExternalAPIError
)

logger = structlog.get_logger()


class ScrapingService:
    """Service principal pour l'orchestration du scraping."""
    
    def __init__(self, session: AsyncSession):
        """
        Initialise le service de scraping.
        
        Args:
            session: Session de base de données async
        """
        self.session = session
        self.dataforseo_client = DataForSEOClient()
        self.url_service = URLDeduplicationService(session)
        self.competitor_service = CompetitorDetectionService(session)
    
    async def get_project_with_keywords(self, project_id: UUID) -> Dict[str, Any]:
        """
        Récupère un projet avec ses mots-clés actifs.
        
        Args:
            project_id: ID du projet
            
        Returns:
            Dict avec le projet et ses mots-clés
        """
        try:
            # Récupérer le projet
            project_stmt = select(Project).where(Project.id == project_id)
            project_result = await self.session.execute(project_stmt)
            project = project_result.scalar_one_or_none()
            
            if not project:
                raise NotFoundError("Project", str(project_id))
            
            if not project.is_active:
                raise ScrapingError(
                    f"Le projet '{project.name}' n'est pas actif",
                    details={"project_id": str(project_id)}
                )
            
            # Récupérer les mots-clés actifs
            keywords_stmt = select(Keyword).where(
                and_(
                    Keyword.project_id == project_id,
                    Keyword.is_active == True
                )
            )
            keywords_result = await self.session.execute(keywords_stmt)
            keywords = keywords_result.scalars().all()
            
            if not keywords:
                raise ScrapingError(
                    f"Aucun mot-clé actif trouvé pour le projet '{project.name}'",
                    details={"project_id": str(project_id)}
                )
            
            logger.info(
                "Projet et mots-clés récupérés",
                project_id=str(project_id),
                project_name=project.name,
                keywords_count=len(keywords)
            )
            
            return {
                "project": project,
                "keywords": keywords
            }
            
        except Exception as e:
            if isinstance(e, (NotFoundError, ScrapingError)):
                raise
            
            logger.error(
                "Erreur lors de la récupération du projet",
                project_id=str(project_id),
                error=str(e)
            )
            raise DatabaseError(
                "Erreur lors de la récupération du projet",
                details={"project_id": str(project_id), "error": str(e)}
            )
    
    async def scrape_single_keyword(
        self,
        keyword: Keyword,
        max_results: int = 100
    ) -> Dict[str, Any]:
        """
        Scrape un seul mot-clé.
        
        Args:
            keyword: Mot-clé à scraper
            max_results: Nombre maximum de résultats
            
        Returns:
            Dict avec les résultats de scraping
        """
        logger.info(
            "Début du scraping d'un mot-clé",
            keyword_id=str(keyword.id),
            keyword=keyword.keyword,
            location=keyword.location
        )
        
        try:
            # Scraper via DataForSEO
            serp_data = await self.dataforseo_client.get_shopping_serp(
                keyword=keyword.keyword,
                location=keyword.location,
                language=keyword.language,
                max_results=max_results
            )
            
            if not serp_data.get("items"):
                logger.warning(
                    "Aucun résultat SERP trouvé",
                    keyword=keyword.keyword
                )
                return {
                    "keyword_id": str(keyword.id),
                    "success": True,
                    "results_count": 0,
                    "serp_results": [],
                    "message": "Aucun résultat trouvé"
                }
            
            # Déduplication des URLs
            deduplicated_results = await self.url_service.deduplicate_serp_results(
                serp_data["items"]
            )
            
            # Traiter et sauvegarder les résultats
            serp_results = await self.process_and_save_serp_results(
                keyword=keyword,
                serp_items=deduplicated_results,
                serp_metadata=serp_data
            )
            
            logger.info(
                "Scraping d'un mot-clé terminé",
                keyword_id=str(keyword.id),
                results_count=len(serp_results)
            )
            
            return {
                "keyword_id": str(keyword.id),
                "success": True,
                "results_count": len(serp_results),
                "serp_results": serp_results,
                "scraped_at": serp_data.get("scraped_at")
            }
            
        except ExternalAPIError as e:
            logger.error(
                "Erreur API lors du scraping",
                keyword_id=str(keyword.id),
                error=str(e)
            )
            raise
            
        except Exception as e:
            logger.error(
                "Erreur lors du scraping d'un mot-clé",
                keyword_id=str(keyword.id),
                error=str(e)
            )
            raise ScrapingError(
                f"Erreur lors du scraping du mot-clé '{keyword.keyword}'",
                details={
                    "keyword_id": str(keyword.id),
                    "keyword": keyword.keyword,
                    "error": str(e)
                }
            )
    
    async def process_and_save_serp_results(
        self,
        keyword: Keyword,
        serp_items: List[Dict[str, Any]],
        serp_metadata: Dict[str, Any]
    ) -> List[SerpResult]:
        """
        Traite et sauvegarde les résultats SERP.
        
        Args:
            keyword: Mot-clé source
            serp_items: Items SERP dédupliqués
            serp_metadata: Métadonnées du scraping
            
        Returns:
            Liste des SerpResult créés
        """
        serp_results = []
        
        try:
            for position, item in enumerate(serp_items, 1):
                # Extraire les données du produit
                product_data = self.extract_product_data(item)
                
                # Créer le résultat SERP
                serp_result = SerpResult(
                    project_id=keyword.project_id,
                    keyword_id=keyword.id,
                    competitor_id=None,  # Sera mis à jour plus tard
                    position=position,
                    url=item.get("url"),
                    domain=self.extract_domain_from_url(item.get("url", "")),
                    title=product_data.get("title"),
                    description=product_data.get("description"),
                    price=product_data.get("price"),
                    currency=product_data.get("currency"),
                    price_original=product_data.get("price_original"),
                    discount_percentage=product_data.get("discount_percentage"),
                    availability=product_data.get("availability"),
                    stock_status=product_data.get("stock_status"),
                    merchant_name=product_data.get("merchant_name"),
                    merchant_url=product_data.get("merchant_url"),
                    rating=product_data.get("rating"),
                    reviews_count=product_data.get("reviews_count"),
                    image_url=product_data.get("image_url"),
                    additional_images=product_data.get("additional_images"),
                    raw_data=item  # Données brutes complètes
                )
                
                self.session.add(serp_result)
                serp_results.append(serp_result)
            
            # Flush pour obtenir les IDs
            await self.session.flush()
            
            # Créer les mappings URL si nécessaire
            if serp_results:
                serp_ids = [str(sr.id) for sr in serp_results]
                unique_url_ids = [item.get("unique_url_id") for item in serp_items if item.get("unique_url_id")]
                
                if len(serp_ids) == len(unique_url_ids):
                    await self.url_service.create_serp_url_mappings(serp_ids, unique_url_ids)
            
            logger.info(
                "Résultats SERP sauvegardés",
                keyword_id=str(keyword.id),
                results_count=len(serp_results)
            )
            
            return serp_results
            
        except Exception as e:
            logger.error(
                "Erreur lors de la sauvegarde des résultats SERP",
                keyword_id=str(keyword.id),
                error=str(e)
            )
            raise DatabaseError(
                "Erreur lors de la sauvegarde des résultats SERP",
                details={"keyword_id": str(keyword.id), "error": str(e)}
            )
    
    def extract_product_data(self, serp_item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrait les données produit d'un item SERP.
        
        Args:
            serp_item: Item SERP brut
            
        Returns:
            Dict avec les données produit normalisées
        """
        try:
            # Extraction des prix
            price = None
            currency = None
            price_original = None
            discount_percentage = None
            
            if "price" in serp_item:
                price_data = serp_item["price"]
                if isinstance(price_data, dict):
                    price = price_data.get("current")
                    currency = price_data.get("currency")
                    price_original = price_data.get("regular")
                    discount_percentage = price_data.get("discount_percentage")
                elif isinstance(price_data, (int, float)):
                    price = price_data
            
            # Extraction des données marchand
            merchant_data = serp_item.get("merchant", {})
            merchant_name = merchant_data.get("name") if isinstance(merchant_data, dict) else None
            merchant_url = merchant_data.get("url") if isinstance(merchant_data, dict) else None
            
            # Extraction des ratings
            rating_data = serp_item.get("rating", {})
            rating = None
            reviews_count = None
            
            if isinstance(rating_data, dict):
                rating = rating_data.get("rating_value")
                reviews_count = rating_data.get("reviews_count")
            
            # Images
            additional_images = None
            if "images" in serp_item and isinstance(serp_item["images"], list):
                additional_images = {"images": serp_item["images"]}
            
            return {
                "title": serp_item.get("title"),
                "description": serp_item.get("description"),
                "price": price,
                "currency": currency,
                "price_original": price_original,
                "discount_percentage": discount_percentage,
                "availability": serp_item.get("availability"),
                "stock_status": serp_item.get("stock_status"),
                "merchant_name": merchant_name,
                "merchant_url": merchant_url,
                "rating": rating,
                "reviews_count": reviews_count,
                "image_url": serp_item.get("image_url"),
                "additional_images": additional_images
            }
            
        except Exception as e:
            logger.warning(
                "Erreur lors de l'extraction des données produit",
                error=str(e),
                serp_item_keys=list(serp_item.keys()) if serp_item else []
            )
            return {}
    
    def extract_domain_from_url(self, url: str) -> str:
        """
        Extrait le domaine d'une URL.
        
        Args:
            url: URL source
            
        Returns:
            Domaine extrait
        """
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Supprimer www.
            if domain.startswith('www.'):
                domain = domain[4:]
            
            return domain
            
        except Exception:
            return ""
    
    async def scrape_project(
        self,
        project_id: UUID,
        max_concurrent: Optional[int] = None,
        max_results_per_keyword: int = 100,
        detect_competitors: bool = True
    ) -> Dict[str, Any]:
        """
        Scrape tous les mots-clés d'un projet.
        
        Args:
            project_id: ID du projet
            max_concurrent: Nombre maximum de requêtes simultanées
            max_results_per_keyword: Nombre maximum de résultats par mot-clé
            detect_competitors: Si True, détecte automatiquement les nouveaux concurrents
            
        Returns:
            Dict avec les résultats du scraping
        """
        scraping_start = datetime.now()
        
        logger.info(
            "Début du scraping de projet",
            project_id=str(project_id),
            max_concurrent=max_concurrent,
            detect_competitors=detect_competitors
        )
        
        try:
            # Récupérer le projet et ses mots-clés
            project_data = await self.get_project_with_keywords(project_id)
            project = project_data["project"]
            keywords = project_data["keywords"]
            
            # Scraper tous les mots-clés
            scraping_results = []
            successful_scrapes = 0
            failed_scrapes = 0
            
            # Utiliser un semaphore pour limiter la concurrence
            if max_concurrent is None:
                max_concurrent = min(len(keywords), 5)  # Max 5 par défaut
            
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def scrape_with_semaphore(keyword):
                async with semaphore:
                    try:
                        result = await self.scrape_single_keyword(
                            keyword=keyword,
                            max_results=max_results_per_keyword
                        )
                        return result
                    except Exception as e:
                        logger.error(
                            "Erreur lors du scraping d'un mot-clé",
                            keyword_id=str(keyword.id),
                            error=str(e)
                        )
                        return {
                            "keyword_id": str(keyword.id),
                            "success": False,
                            "error": str(e),
                            "error_type": type(e).__name__
                        }
            
            # Lancer tous les scrapings
            tasks = [scrape_with_semaphore(keyword) for keyword in keywords]
            scraping_results = await asyncio.gather(*tasks, return_exceptions=False)
            
            # Compter les succès et échecs
            for result in scraping_results:
                if result.get("success", False):
                    successful_scrapes += 1
                else:
                    failed_scrapes += 1
            
            # Commit des résultats
            await self.session.commit()
            
            # Détection automatique des concurrents
            new_competitors = []
            if detect_competitors and successful_scrapes > 0:
                try:
                    new_competitors = await self.competitor_service.detect_new_competitors(
                        project_id=str(project_id),
                        min_appearances=2,
                        min_authority_score=20.0,
                        auto_create=True
                    )
                    
                    # Mettre à jour les associations
                    await self.competitor_service.update_competitor_associations(str(project_id))
                    await self.session.commit()
                    
                except Exception as e:
                    logger.warning(
                        "Erreur lors de la détection de concurrents",
                        project_id=str(project_id),
                        error=str(e)
                    )
            
            scraping_end = datetime.now()
            duration = (scraping_end - scraping_start).total_seconds()
            
            result = {
                "project_id": str(project_id),
                "project_name": project.name,
                "success": True,
                "scraping_start": scraping_start.isoformat(),
                "scraping_end": scraping_end.isoformat(),
                "duration_seconds": round(duration, 2),
                "keywords_scraped": len(keywords),
                "successful_scrapes": successful_scrapes,
                "failed_scrapes": failed_scrapes,
                "new_competitors_detected": len(new_competitors),
                "total_results": sum(r.get("results_count", 0) for r in scraping_results if r.get("success")),
                "scraping_results": scraping_results,
                "new_competitors": new_competitors
            }
            
            logger.info(
                "Scraping de projet terminé",
                project_id=str(project_id),
                duration=duration,
                successful=successful_scrapes,
                failed=failed_scrapes,
                new_competitors=len(new_competitors)
            )
            
            return result
            
        except Exception as e:
            await self.session.rollback()
            
            logger.error(
                "Erreur lors du scraping de projet",
                project_id=str(project_id),
                error=str(e)
            )
            
            if isinstance(e, (NotFoundError, ScrapingError, ExternalAPIError)):
                raise
            
            raise ScrapingError(
                f"Erreur lors du scraping du projet",
                details={"project_id": str(project_id), "error": str(e)}
            )
    
    async def get_scraping_status(self, project_id: UUID) -> Dict[str, Any]:
        """
        Récupère le statut du scraping pour un projet.
        
        Args:
            project_id: ID du projet
            
        Returns:
            Dict avec le statut du scraping
        """
        try:
            # Récupérer les derniers résultats SERP
            latest_serp_stmt = select(SerpResult.scraped_at).where(
                SerpResult.project_id == project_id
            ).order_by(SerpResult.scraped_at.desc()).limit(1)
            
            latest_result = await self.session.execute(latest_serp_stmt)
            last_scrape = latest_result.scalar_one_or_none()
            
            # Compter les résultats par date
            if last_scrape:
                count_stmt = select(SerpResult).where(
                    and_(
                        SerpResult.project_id == project_id,
                        SerpResult.scraped_at >= last_scrape.date()
                    )
                )
                count_result = await self.session.execute(count_stmt)
                recent_results = len(count_result.scalars().all())
            else:
                recent_results = 0
            
            return {
                "project_id": str(project_id),
                "last_scrape": last_scrape.isoformat() if last_scrape else None,
                "recent_results_count": recent_results,
                "status": "completed" if last_scrape else "never_scraped"
            }
            
        except Exception as e:
            logger.error(
                "Erreur lors de la récupération du statut",
                project_id=str(project_id),
                error=str(e)
            )
            raise DatabaseError(
                "Erreur lors de la récupération du statut de scraping",
                details={"project_id": str(project_id), "error": str(e)}
            ) 