"""Service pour l'intégration avec l'API DataForSEO."""

import httpx
import json
import structlog
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.keyword import Keyword

logger = structlog.get_logger()

class DataForSEOService:
    """Service pour interagir avec l'API DataForSEO."""
    
    def __init__(self):
        # Credentials DataForSEO
        self.auth_header = "Basic dG9vbHNAc2xhc2hyLmZyOmQyODc2OTRmZjFiYmVjYzQ="
        self.base_url = "https://api.dataforseo.com/v3"
        
        # Configuration par défaut
        self.default_config = {
            "location_code": 2250,  # France
            "language_code": "fr",
            "device": "desktop",
            "os": "windows",
            "depth": 100
        }
    
    async def get_serp_results(
        self, 
        keywords: List[str],
        location_code: int = 2250,
        language_code: str = "fr",
        device: str = "desktop"
    ) -> Dict[str, Any]:
        """
        Récupérer les résultats SERP pour une liste de mots-clés.
        
        Args:
            keywords: Liste des mots-clés à analyser
            location_code: Code de localisation (2250 = France)
            language_code: Code de langue (fr)
            device: Type d'appareil (desktop, mobile, tablet)
            
        Returns:
            Dict contenant les résultats pour chaque mot-clé
        """
        logger.info("Début analyse SERP DataForSEO", keywords_count=len(keywords))
        
        headers = {
            'Authorization': self.auth_header,
            'Content-Type': 'application/json'
        }
        
        url = f"{self.base_url}/serp/google/shopping/live/advanced"
        
        # Résultats combinés
        combined_results = {
            "version": "0.1.20250724",
            "status_code": 20000,
            "status_message": "Ok.",
            "time": "0 sec.",
            "cost": 0,
            "tasks_count": len(keywords),
            "tasks_error": 0,
            "tasks": []
        }
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                # Traiter chaque mot-clé individuellement
                for keyword in keywords:
                    payload = [{
                        "keyword": keyword,
                        "location_code": location_code,
                        "language_code": language_code,
                        "device": device,
                        "os": "windows",
                        "depth": 10
                    }]
                    
                    logger.info("Appel API DataForSEO pour mot-clé", keyword=keyword, url=url)
                    
                    response = await client.post(
                        url,
                        headers=headers,
                        json=payload
                    )
                    
                    response.raise_for_status()
                    data = response.json()
                    
                    # Ajouter les tâches au résultat combiné
                    if data.get('tasks'):
                        combined_results['tasks'].extend(data['tasks'])
                        combined_results['cost'] += data.get('cost', 0)
                        
                        # Compter les erreurs
                        for task in data['tasks']:
                            if task.get('status_code') != 20000:
                                combined_results['tasks_error'] += 1
                    
                    logger.info(
                        "Réponse API DataForSEO reçue", 
                        keyword=keyword,
                        status_code=response.status_code,
                        task_status=data.get('tasks', [{}])[0].get('status_code') if data.get('tasks') else None
                    )
                
                logger.info(
                    "Analyse SERP terminée", 
                    total_tasks=len(combined_results['tasks']),
                    errors=combined_results['tasks_error']
                )
                
                return combined_results
                
        except httpx.HTTPStatusError as e:
            logger.error(
                "Erreur HTTP DataForSEO", 
                status_code=e.response.status_code,
                response_text=e.response.text
            )
            raise Exception(f"Erreur API DataForSEO: {e.response.status_code}")
            
        except Exception as e:
            logger.error("Erreur lors de l'appel DataForSEO", error=str(e))
            raise
    
    async def process_and_save_serp_results(
        self,
        session: AsyncSession,
        project_id: str,
        serp_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Traiter et sauvegarder les résultats SERP en base.
        
        Args:
            session: Session SQLAlchemy
            project_id: ID du projet
            serp_data: Données brutes de l'API DataForSEO
            
        Returns:
            Statistiques de traitement
        """
        from app.models.serp_result import SerpResult
        from app.models.competitor import Competitor
        from app.models.keyword import Keyword
        from sqlalchemy import select
        from urllib.parse import urlparse
        
        logger.info("Début traitement résultats SERP", project_id=project_id)
        
        stats = {
            "keywords_processed": 0,
            "shopping_results_found": 0,
            "shopping_results_saved": 0,
            "competitors_detected": 0,
            "errors": []
        }
        
        # Récupérer les mots-clés du projet pour mapping
        keywords_query = select(Keyword).where(Keyword.project_id == project_id)
        keywords_result = await session.execute(keywords_query)
        keywords_map = {kw.keyword: kw for kw in keywords_result.scalars().all()}
        
        # Récupérer les concurrents existants
        competitors_query = select(Competitor).where(Competitor.project_id == project_id)
        competitors_result = await session.execute(competitors_query)
        competitors_map = {comp.domain: comp for comp in competitors_result.scalars().all()}
        
        for task in serp_data.get('tasks', []):
            if task.get('status_code') != 20000:
                stats['errors'].append(f"Erreur API pour {task.get('data', {}).get('keyword', 'unknown')}: {task.get('status_message')}")
                continue
                
            keyword_text = task.get('data', {}).get('keyword')
            if not keyword_text or keyword_text not in keywords_map:
                continue
                
            keyword_obj = keywords_map[keyword_text]
            stats['keywords_processed'] += 1
            
            # Traiter les résultats
            shopping_position = 0  # Position globale dans tous les résultats shopping
            for result in task.get('result', []):
                for item in result.get('items', []):
                    # On ne traite que les popular_products (résultats shopping)
                    if item.get('type') != 'popular_products':
                        continue
                    
                    # Debug: logger la structure des popular_products
                    logger.debug(f"Structure popular_products pour {keyword_text}: {item}")
                    
                    # Traiter chaque produit dans popular_products
                    for product in item.get('items', []):
                        if product.get('type') != 'popular_products_element':
                            continue
                        
                        shopping_position += 1  # Incrémenter la position shopping globale
                        stats['shopping_results_found'] += 1
                        
                        try:
                            # Debug: logger la structure du produit
                            logger.debug(f"Structure produit pour {keyword_text}: {product}")
                            
                            # Extraire les informations du produit
                            title = product.get('title', '')
                            seller = product.get('seller', '')
                            description = product.get('description', '')
                            
                            # URL réelle du produit - chercher dans tous les champs possibles
                            product_url = None
                            possible_url_fields = ['url', 'link', 'click_url', 'href', 'product_url', 'shopping_url', 'buy_url']
                            
                            for field in possible_url_fields:
                                if product.get(field):
                                    product_url = product.get(field)
                                    logger.debug(f"URL trouvée dans le champ '{field}': {product_url}")
                                    break
                            
                            # Si aucune URL trouvée, logger tous les champs disponibles
                            if not product_url:
                                logger.debug(f"Aucune URL trouvée. Champs disponibles: {list(product.keys())}")
                            
                            # Prix
                            price_info = product.get('price', {})
                            price = None
                            currency = None
                            if price_info and isinstance(price_info, dict):
                                price = price_info.get('current')
                                currency = price_info.get('currency', 'EUR')
                            
                            # Rating
                            rating_info = product.get('rating', {})
                            rating = None
                            if rating_info and isinstance(rating_info, dict):
                                rating = rating_info.get('value')
                            
                            # Déterminer le domaine du vendeur
                            domain = seller.lower().replace(' ', '').replace('.', '') if seller else ''
                            if 'leroymerlin' in domain or 'leroy merlin' in seller.lower():
                                domain = 'leroymerlin.fr'
                            elif 'bricodepot' in domain or 'brico depot' in seller.lower():
                                domain = 'bricodepot.fr'
                            elif 'castorama' in domain:
                                domain = 'castorama.fr'
                            elif 'lapeyre' in domain:
                                domain = 'lapeyre.fr'
                            elif 'point.p' in seller.lower() or 'pointp' in domain:
                                domain = 'pointp.fr'
                            elif 'somfy' in seller.lower() or 'somfy' in domain:
                                domain = 'somfy.fr'  # Ajouter Somfy
                            else:
                                # Essayer d'extraire le domaine du seller
                                domain = seller.lower().replace(' ', '').replace('et plus', '') + '.fr'
                            
                            # Vérifier/créer le concurrent
                            competitor = None
                            if domain and domain not in competitors_map:
                                # Créer un nouveau concurrent
                                competitor = Competitor(
                                    project_id=project_id,
                                    name=seller,
                                    domain=domain,
                                    brand_name=seller,
                                    is_main_brand=False
                                )
                                session.add(competitor)
                                await session.flush()  # Pour obtenir l'ID
                                competitors_map[domain] = competitor
                                stats['competitors_detected'] += 1
                                logger.info(f"Nouveau concurrent détecté: {seller} ({domain})")
                            else:
                                competitor = competitors_map.get(domain)
                            
                            # Créer le résultat SERP avec la vraie position shopping
                            # Utiliser uniquement l'URL réelle du produit si disponible
                            final_url = None
                            if product_url:
                                # Utiliser l'URL réelle du produit
                                final_url = product_url
                                logger.debug(f"URL réelle utilisée pour {title}: {product_url}")
                            else:
                                # Pas d'URL disponible - on laisse final_url à None
                                logger.debug(f"Aucune URL disponible pour {title}")
                            
                            serp_result = SerpResult(
                                project_id=project_id,
                                keyword_id=keyword_obj.id,
                                competitor_id=competitor.id if competitor else None,
                                scraped_at=datetime.utcnow(),
                                position=shopping_position,  # Position dans les résultats shopping (1, 2, 3...)
                                url=final_url,  # URL réelle du produit ou URL de recherche
                                domain=domain,
                                title=title,
                                description=description,
                                price=price,
                                currency=currency,
                                merchant_name=seller,
                                rating=rating
                            )
                            
                            session.add(serp_result)
                            stats['shopping_results_saved'] += 1
                            
                        except Exception as e:
                            error_msg = f"Erreur traitement produit {title[:50]}: {str(e)}"
                            stats['errors'].append(error_msg)
                            logger.error(error_msg)
        
        # Sauvegarder en base
        try:
            await session.commit()
            logger.info("Résultats SERP sauvegardés", **stats)
        except Exception as e:
            await session.rollback()
            error_msg = f"Erreur sauvegarde: {str(e)}"
            stats['errors'].append(error_msg)
            logger.error(error_msg)
            raise
        
        return stats

    async def analyze_keywords_for_project(
        self,
        session: AsyncSession,
        project_id: str,
        keyword_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyser tous les mots-clés d'un projet ou une sélection.
        
        Args:
            session: Session SQLAlchemy
            project_id: ID du projet
            keyword_ids: Liste optionnelle d'IDs de mots-clés spécifiques
            
        Returns:
            Résultats de l'analyse
        """
        logger.info("Début analyse projet", project_id=project_id)
        
        # Récupérer les mots-clés à analyser
        query = select(Keyword).where(
            Keyword.project_id == project_id,
            Keyword.is_active == True
        )
        
        if keyword_ids:
            query = query.where(Keyword.id.in_(keyword_ids))
        
        result = await session.execute(query)
        keywords = result.scalars().all()
        
        if not keywords:
            raise Exception("Aucun mot-clé actif trouvé pour ce projet")
        
        keyword_list = [kw.keyword for kw in keywords]
        
        logger.info(f"Analyse de {len(keyword_list)} mots-clés", keywords=keyword_list)
        
        # Appeler l'API DataForSEO
        serp_data = await self.get_serp_results(keyword_list)
        
        # Traiter et sauvegarder les résultats
        processing_stats = await self.process_and_save_serp_results(
            session, project_id, serp_data
        )
        
        # Statistiques finales
        stats = {
            "keywords_processed": len(keyword_list),
            "results_received": len(serp_data.get('tasks', [])),
            "api_calls": 1,
            **processing_stats
        }
        
        logger.info("Analyse terminée", **stats)
        
        return {
            "project_id": project_id,
            "keywords_analyzed": len(keyword_list),
            "analysis_date": datetime.utcnow().isoformat(),
            "stats": stats,
            "raw_data": serp_data  # Pour debug, peut être retiré en prod
        } 