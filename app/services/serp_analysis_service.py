"""Service pour analyser les données SERP stockées et générer des métriques."""

import structlog
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from collections import defaultdict, Counter

from app.models.keyword import Keyword
from app.models.serp_result import SerpResult
from app.models.unique_url import UniqueUrl
from app.models.serp_url_mapping import SerpUrlMapping
from app.models.project import Project

logger = structlog.get_logger()

class SerpAnalysisService:
    """Service pour analyser les données SERP et générer des insights."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_project_dashboard_metrics(self, project_id: str) -> Dict[str, Any]:
        """
        Récupérer les métriques du dashboard basées sur les vraies données SERP.
        
        Args:
            project_id: ID du projet
            
        Returns:
            Dict contenant toutes les métriques du dashboard
        """
        logger.info("Calcul métriques dashboard réelles", project_id=project_id)
        
        # Récupérer le projet et ses données de base
        project_query = select(Project).where(Project.id == project_id)
        project_result = await self.session.execute(project_query)
        project = project_result.scalar_one_or_none()
        
        if not project:
            raise ValueError(f"Projet {project_id} non trouvé")
        
        # Métriques de base
        keywords_query = select(func.count(Keyword.id)).where(
            and_(Keyword.project_id == project_id, Keyword.is_active == True)
        )
        keywords_result = await self.session.execute(keywords_query)
        total_keywords = keywords_result.scalar() or 0
        
        # Récupérer les dernières données SERP
        latest_serp_query = select(SerpResult).where(
            SerpResult.project_id == project_id
        ).order_by(desc(SerpResult.search_date)).limit(100)
        
        serp_results = await self.session.execute(latest_serp_query)
        serp_data = serp_results.scalars().all()
        
        if not serp_data:
            # Pas de données SERP encore
            return {
                "total_keywords": total_keywords,
                "total_serp_results": 0,
                "unique_domains": 0,
                "last_analysis": None,
                "top_competitors": [],
                "keyword_performance": {
                    "total_volume": 0,
                    "avg_position": 0,
                    "visibility_score": 0
                },
                "trends": {
                    "keywords_change": 0,
                    "positions_change": 0,
                    "competitors_change": 0
                }
            }
        
        # Analyser les domaines et concurrents
        domains_analysis = await self._analyze_domains(serp_data)
        
        # Calculer les performances des mots-clés
        keyword_performance = await self._analyze_keyword_performance(project_id, serp_data)
        
        # Tendances (pour l'instant basiques, à améliorer avec l'historique)
        trends = await self._calculate_trends(project_id)
        
        return {
            "total_keywords": total_keywords,
            "total_serp_results": len(serp_data),
            "unique_domains": len(domains_analysis["unique_domains"]),
            "last_analysis": serp_data[0].search_date.isoformat() if serp_data else None,
            "top_competitors": domains_analysis["top_competitors"][:10],
            "keyword_performance": keyword_performance,
            "trends": trends
        }
    
    async def get_share_of_voice_data(self, project_id: str, reference_domain: str) -> Dict[str, Any]:
        """
        Calculer le Share of Voice basé sur les données SERP réelles.
        
        Args:
            project_id: ID du projet
            reference_domain: Domaine de référence du projet
            
        Returns:
            Données de Share of Voice
        """
        logger.info("Calcul Share of Voice réel", project_id=project_id)
        
        # Récupérer les résultats SERP avec les URLs
        serp_query = select(SerpResult, SerpUrlMapping, UniqueUrl).join(
            SerpUrlMapping, SerpResult.id == SerpUrlMapping.serp_result_id
        ).join(
            UniqueUrl, SerpUrlMapping.unique_url_id == UniqueUrl.id
        ).where(SerpResult.project_id == project_id)
        
        results = await self.session.execute(serp_query)
        serp_data = results.all()
        
        if not serp_data:
            return {
                "total_results": 0,
                "domains": [],
                "reference_performance": {
                    "domain": reference_domain,
                    "share": 0,
                    "positions": [],
                    "avg_position": 0
                }
            }
        
        # Analyser par domaine
        domain_stats = defaultdict(lambda: {
            "positions": [],
            "keywords": set(),
            "total_volume": 0
        })
        
        total_positions = 0
        
        for serp_result, url_mapping, unique_url in serp_data:
            domain = unique_url.domain
            position = url_mapping.position
            
            domain_stats[domain]["positions"].append(position)
            domain_stats[domain]["keywords"].add(serp_result.keyword_id)
            total_positions += 1
        
        # Calculer les parts de voix
        domains_sov = []
        reference_performance = None
        
        for domain, stats in domain_stats.items():
            share = (len(stats["positions"]) / total_positions) * 100 if total_positions > 0 else 0
            avg_position = sum(stats["positions"]) / len(stats["positions"]) if stats["positions"] else 0
            
            domain_data = {
                "domain": domain,
                "share": round(share, 2),
                "positions": len(stats["positions"]),
                "keywords": len(stats["keywords"]),
                "avg_position": round(avg_position, 1)
            }
            
            domains_sov.append(domain_data)
            
            # Identifier les performances du domaine de référence
            if reference_domain and (reference_domain in domain or domain in reference_domain):
                reference_performance = domain_data
        
        # Trier par part de voix
        domains_sov.sort(key=lambda x: x["share"], reverse=True)
        
        return {
            "total_results": total_positions,
            "domains": domains_sov[:20],  # Top 20
            "reference_performance": reference_performance or {
                "domain": reference_domain,
                "share": 0,
                "positions": 0,
                "keywords": 0,
                "avg_position": 0
            }
        }
    
    async def get_position_matrix_data(self, project_id: str) -> Dict[str, Any]:
        """
        Générer la matrice de positions basée sur les données réelles.
        """
        logger.info("Génération matrice positions réelle", project_id=project_id)
        
        # Récupérer les mots-clés avec leurs résultats SERP
        query = select(Keyword, SerpResult, SerpUrlMapping, UniqueUrl).join(
            SerpResult, Keyword.id == SerpResult.keyword_id
        ).join(
            SerpUrlMapping, SerpResult.id == SerpUrlMapping.serp_result_id
        ).join(
            UniqueUrl, SerpUrlMapping.unique_url_id == UniqueUrl.id
        ).where(Keyword.project_id == project_id)
        
        results = await self.session.execute(query)
        data = results.all()
        
        # Organiser par mot-clé
        keywords_matrix = defaultdict(lambda: {
            "keyword": "",
            "volume": 0,
            "positions": [],
            "top_domains": []
        })
        
        for keyword, serp_result, url_mapping, unique_url in data:
            kw_id = keyword.id
            keywords_matrix[kw_id]["keyword"] = keyword.keyword
            keywords_matrix[kw_id]["volume"] = keyword.search_volume
            keywords_matrix[kw_id]["positions"].append({
                "domain": unique_url.domain,
                "position": url_mapping.position,
                "title": url_mapping.title,
                "url": unique_url.url
            })
        
        # Trier et nettoyer
        matrix_data = []
        for kw_id, data in keywords_matrix.items():
            # Trier par position
            data["positions"].sort(key=lambda x: x["position"])
            data["top_domains"] = data["positions"][:10]  # Top 10
            
            matrix_data.append({
                "keyword": data["keyword"],
                "volume": data["volume"],
                "total_results": len(data["positions"]),
                "top_positions": data["top_domains"]
            })
        
        # Trier par volume de recherche
        matrix_data.sort(key=lambda x: x["volume"], reverse=True)
        
        return {
            "keywords": matrix_data,
            "total_keywords": len(matrix_data),
            "total_positions": sum(len(k["top_positions"]) for k in matrix_data)
        }
    
    async def _analyze_domains(self, serp_data: List[SerpResult]) -> Dict[str, Any]:
        """Analyser les domaines présents dans les résultats SERP."""
        
        # Récupérer les URLs associées aux résultats SERP
        serp_ids = [result.id for result in serp_data]
        
        url_query = select(SerpUrlMapping, UniqueUrl).join(
            UniqueUrl, SerpUrlMapping.unique_url_id == UniqueUrl.id
        ).where(SerpUrlMapping.serp_result_id.in_(serp_ids))
        
        url_results = await self.session.execute(url_query)
        url_data = url_results.all()
        
        domain_counter = Counter()
        unique_domains = set()
        
        for url_mapping, unique_url in url_data:
            domain = unique_url.domain
            domain_counter[domain] += 1
            unique_domains.add(domain)
        
        top_competitors = [
            {"domain": domain, "appearances": count}
            for domain, count in domain_counter.most_common(20)
        ]
        
        return {
            "unique_domains": unique_domains,
            "top_competitors": top_competitors
        }
    
    async def _analyze_keyword_performance(self, project_id: str, serp_data: List[SerpResult]) -> Dict[str, Any]:
        """Analyser les performances des mots-clés."""
        
        # Récupérer les mots-clés avec leur volume
        keywords_query = select(Keyword).where(
            and_(Keyword.project_id == project_id, Keyword.is_active == True)
        )
        keywords_result = await self.session.execute(keywords_query)
        keywords = keywords_result.scalars().all()
        
        total_volume = sum(kw.search_volume for kw in keywords)
        
        # Calculer la position moyenne (basique pour l'instant)
        avg_position = 15.5  # Moyenne théorique pour le top 30
        visibility_score = len(serp_data) * 2.5  # Score basique
        
        return {
            "total_volume": total_volume,
            "avg_position": avg_position,
            "visibility_score": round(visibility_score, 1)
        }
    
    async def _calculate_trends(self, project_id: str) -> Dict[str, Any]:
        """Calculer les tendances (basique pour l'instant)."""
        
        return {
            "keywords_change": 0,
            "positions_change": 0,
            "competitors_change": 0
        } 