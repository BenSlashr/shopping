"""Service de détection automatique des concurrents."""

from typing import List, Dict, Set, Optional, Any
from collections import Counter
from urllib.parse import urlparse
import structlog
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Competitor, SerpResult, Project
from app.core.exceptions import DatabaseError

logger = structlog.get_logger()


class CompetitorDetectionService:
    """Service pour la détection automatique de nouveaux concurrents."""
    
    def __init__(self, session: AsyncSession):
        """
        Initialise le service de détection.
        
        Args:
            session: Session de base de données async
        """
        self.session = session
    
    def extract_domain_from_url(self, url: str) -> str:
        """
        Extrait le domaine d'une URL.
        
        Args:
            url: URL source
            
        Returns:
            Domaine nettoyé
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
    
    def normalize_domain(self, domain: str) -> str:
        """
        Normalise un domaine pour la comparaison.
        
        Args:
            domain: Domaine à normaliser
            
        Returns:
            Domaine normalisé
        """
        if not domain:
            return ""
        
        domain = domain.lower().strip()
        
        # Supprimer les préfixes communs
        prefixes = ['www.', 'shop.', 'store.', 'm.', 'mobile.']
        for prefix in prefixes:
            if domain.startswith(prefix):
                domain = domain[len(prefix):]
                break
        
        return domain
    
    def is_marketplace_domain(self, domain: str) -> bool:
        """
        Vérifie si un domaine est une marketplace connue.
        
        Args:
            domain: Domaine à vérifier
            
        Returns:
            True si c'est une marketplace
        """
        marketplaces = {
            'amazon.fr', 'amazon.com', 'amazon.de', 'amazon.co.uk',
            'ebay.fr', 'ebay.com', 'ebay.de', 'ebay.co.uk',
            'cdiscount.com', 'fnac.com', 'darty.com', 'boulanger.com',
            'leclerc.fr', 'carrefour.fr', 'auchan.fr',
            'priceminister.com', 'rakuten.fr',
            'manomano.fr', 'leroy-merlin.fr', 'castorama.fr',
            'zalando.fr', 'zalando.com', 'asos.com',
            'booking.com', 'expedia.fr', 'hotels.com'
        }
        
        normalized = self.normalize_domain(domain)
        return normalized in marketplaces
    
    def calculate_domain_authority_score(
        self,
        domain: str,
        appearances: int,
        avg_position: float,
        price_competitiveness: float = 0.5
    ) -> float:
        """
        Calcule un score d'autorité pour un domaine.
        
        Args:
            domain: Domaine à évaluer
            appearances: Nombre d'apparitions
            avg_position: Position moyenne
            price_competitiveness: Score de compétitivité prix (0-1)
            
        Returns:
            Score d'autorité (0-100)
        """
        # Score de base basé sur les apparitions
        appearance_score = min(appearances * 2, 50)  # Max 50 points
        
        # Score de position (plus la position est bonne, plus le score est élevé)
        position_score = max(0, 30 - avg_position)  # Max 30 points
        
        # Score de prix (compétitivité)
        price_score = price_competitiveness * 20  # Max 20 points
        
        # Bonus pour les marketplaces connues
        marketplace_bonus = 10 if self.is_marketplace_domain(domain) else 0
        
        total_score = appearance_score + position_score + price_score + marketplace_bonus
        return min(total_score, 100)
    
    async def get_existing_competitors(self, project_id: str) -> Set[str]:
        """
        Récupère les domaines des concurrents existants.
        
        Args:
            project_id: ID du projet
            
        Returns:
            Set des domaines existants
        """
        try:
            stmt = select(Competitor.domain).where(Competitor.project_id == project_id)
            result = await self.session.execute(stmt)
            domains = result.scalars().all()
            
            # Normaliser les domaines
            normalized_domains = {self.normalize_domain(domain) for domain in domains}
            
            logger.debug(
                "Concurrents existants récupérés",
                project_id=project_id,
                count=len(normalized_domains)
            )
            
            return normalized_domains
            
        except Exception as e:
            logger.error(
                "Erreur lors de la récupération des concurrents existants",
                project_id=project_id,
                error=str(e)
            )
            raise DatabaseError(
                "Erreur lors de la récupération des concurrents existants",
                details={"project_id": project_id, "error": str(e)}
            )
    
    async def analyze_serp_domains(
        self,
        project_id: str,
        min_appearances: int = 3,
        min_authority_score: float = 25.0
    ) -> List[Dict[str, Any]]:
        """
        Analyse les domaines présents dans les résultats SERP.
        
        Args:
            project_id: ID du projet
            min_appearances: Nombre minimum d'apparitions pour être considéré
            min_authority_score: Score minimum d'autorité
            
        Returns:
            Liste des domaines candidats avec leurs métriques
        """
        try:
            # Récupérer tous les résultats SERP du projet
            stmt = select(SerpResult).where(SerpResult.project_id == project_id)
            result = await self.session.execute(stmt)
            serp_results = result.scalars().all()
            
            if not serp_results:
                logger.info("Aucun résultat SERP trouvé", project_id=project_id)
                return []
            
            # Analyser les domaines
            domain_stats = {}
            
            for serp_result in serp_results:
                if not serp_result.domain:
                    continue
                
                domain = self.normalize_domain(serp_result.domain)
                if not domain:
                    continue
                
                if domain not in domain_stats:
                    domain_stats[domain] = {
                        'domain': domain,
                        'original_domain': serp_result.domain,
                        'appearances': 0,
                        'positions': [],
                        'prices': [],
                        'titles': set(),
                        'merchants': set()
                    }
                
                stats = domain_stats[domain]
                stats['appearances'] += 1
                
                if serp_result.position:
                    stats['positions'].append(serp_result.position)
                
                if serp_result.price:
                    stats['prices'].append(float(serp_result.price))
                
                if serp_result.title:
                    stats['titles'].add(serp_result.title[:100])  # Limiter la taille
                
                if serp_result.merchant_name:
                    stats['merchants'].add(serp_result.merchant_name)
            
            # Calculer les métriques finales
            candidates = []
            
            for domain, stats in domain_stats.items():
                if stats['appearances'] < min_appearances:
                    continue
                
                # Calculer les métriques
                avg_position = sum(stats['positions']) / len(stats['positions']) if stats['positions'] else 100
                avg_price = sum(stats['prices']) / len(stats['prices']) if stats['prices'] else 0
                
                # Calculer la compétitivité prix (simple approximation)
                price_competitiveness = 0.5  # Valeur par défaut
                if stats['prices'] and len(domain_stats) > 1:
                    all_prices = []
                    for other_stats in domain_stats.values():
                        all_prices.extend(other_stats['prices'])
                    
                    if all_prices:
                        median_price = sorted(all_prices)[len(all_prices) // 2]
                        if median_price > 0:
                            # Plus le prix est bas par rapport à la médiane, plus c'est compétitif
                            price_competitiveness = max(0, min(1, (median_price - avg_price) / median_price + 0.5))
                
                # Calculer le score d'autorité
                authority_score = self.calculate_domain_authority_score(
                    domain=domain,
                    appearances=stats['appearances'],
                    avg_position=avg_position,
                    price_competitiveness=price_competitiveness
                )
                
                if authority_score >= min_authority_score:
                    candidates.append({
                        'domain': domain,
                        'original_domain': stats['original_domain'],
                        'appearances': stats['appearances'],
                        'avg_position': round(avg_position, 2),
                        'avg_price': round(avg_price, 2) if avg_price > 0 else None,
                        'price_competitiveness': round(price_competitiveness, 3),
                        'authority_score': round(authority_score, 2),
                        'is_marketplace': self.is_marketplace_domain(domain),
                        'unique_titles': len(stats['titles']),
                        'unique_merchants': len(stats['merchants']),
                        'suggested_name': self.suggest_competitor_name(domain, stats['merchants'])
                    })
            
            # Trier par score d'autorité décroissant
            candidates.sort(key=lambda x: x['authority_score'], reverse=True)
            
            logger.info(
                "Analyse des domaines terminée",
                project_id=project_id,
                total_domains=len(domain_stats),
                candidates=len(candidates)
            )
            
            return candidates
            
        except Exception as e:
            logger.error(
                "Erreur lors de l'analyse des domaines SERP",
                project_id=project_id,
                error=str(e)
            )
            raise DatabaseError(
                "Erreur lors de l'analyse des domaines SERP",
                details={"project_id": project_id, "error": str(e)}
            )
    
    def suggest_competitor_name(self, domain: str, merchants: Set[str]) -> str:
        """
        Suggère un nom pour le concurrent basé sur le domaine et les marchands.
        
        Args:
            domain: Domaine du concurrent
            merchants: Set des noms de marchands
            
        Returns:
            Nom suggéré
        """
        # Si on a des noms de marchands, utiliser le plus fréquent
        if merchants:
            merchant_list = list(merchants)
            if len(merchant_list) == 1:
                return merchant_list[0]
            
            # Prendre le nom le plus court (souvent le plus générique)
            return min(merchant_list, key=len)
        
        # Sinon, générer un nom basé sur le domaine
        domain_parts = domain.split('.')
        if len(domain_parts) >= 2:
            name = domain_parts[0]
            # Capitaliser la première lettre
            return name.capitalize()
        
        return domain.capitalize()
    
    async def detect_new_competitors(
        self,
        project_id: str,
        min_appearances: int = 3,
        min_authority_score: float = 25.0,
        auto_create: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Détecte de nouveaux concurrents potentiels.
        
        Args:
            project_id: ID du projet
            min_appearances: Nombre minimum d'apparitions
            min_authority_score: Score minimum d'autorité
            auto_create: Si True, crée automatiquement les concurrents
            
        Returns:
            Liste des nouveaux concurrents détectés
        """
        logger.info(
            "Début de la détection de concurrents",
            project_id=project_id,
            min_appearances=min_appearances,
            min_authority_score=min_authority_score
        )
        
        try:
            # Récupérer les concurrents existants
            existing_domains = await self.get_existing_competitors(project_id)
            
            # Analyser les domaines SERP
            candidates = await self.analyze_serp_domains(
                project_id=project_id,
                min_appearances=min_appearances,
                min_authority_score=min_authority_score
            )
            
            # Filtrer les nouveaux concurrents
            new_competitors = []
            
            for candidate in candidates:
                normalized_domain = self.normalize_domain(candidate['domain'])
                
                if normalized_domain not in existing_domains:
                    new_competitors.append(candidate)
                    
                    # Créer automatiquement si demandé
                    if auto_create:
                        await self.create_competitor_from_candidate(
                            project_id=project_id,
                            candidate=candidate
                        )
            
            logger.info(
                "Détection de concurrents terminée",
                project_id=project_id,
                new_competitors=len(new_competitors),
                auto_created=len(new_competitors) if auto_create else 0
            )
            
            return new_competitors
            
        except Exception as e:
            logger.error(
                "Erreur lors de la détection de concurrents",
                project_id=project_id,
                error=str(e)
            )
            raise DatabaseError(
                "Erreur lors de la détection de concurrents",
                details={"project_id": project_id, "error": str(e)}
            )
    
    async def create_competitor_from_candidate(
        self,
        project_id: str,
        candidate: Dict[str, Any]
    ) -> Competitor:
        """
        Crée un concurrent à partir d'un candidat détecté.
        
        Args:
            project_id: ID du projet
            candidate: Données du candidat
            
        Returns:
            Concurrent créé
        """
        try:
            competitor = Competitor(
                project_id=project_id,
                name=candidate['suggested_name'],
                domain=candidate['domain'],
                brand_name=candidate['suggested_name'],
                is_main_brand=False
            )
            
            self.session.add(competitor)
            await self.session.flush()
            
            logger.info(
                "Concurrent créé automatiquement",
                project_id=project_id,
                competitor_name=competitor.name,
                domain=competitor.domain
            )
            
            return competitor
            
        except Exception as e:
            logger.error(
                "Erreur lors de la création du concurrent",
                project_id=project_id,
                candidate=candidate,
                error=str(e)
            )
            raise DatabaseError(
                "Erreur lors de la création du concurrent",
                details={"project_id": project_id, "error": str(e)}
            )
    
    async def update_competitor_associations(self, project_id: str) -> int:
        """
        Met à jour les associations entre résultats SERP et concurrents.
        
        Args:
            project_id: ID du projet
            
        Returns:
            Nombre d'associations mises à jour
        """
        try:
            # Récupérer tous les concurrents du projet
            competitors_stmt = select(Competitor).where(Competitor.project_id == project_id)
            competitors_result = await self.session.execute(competitors_stmt)
            competitors = competitors_result.scalars().all()
            
            # Créer un mapping domaine -> concurrent
            domain_to_competitor = {}
            for competitor in competitors:
                normalized_domain = self.normalize_domain(competitor.domain)
                domain_to_competitor[normalized_domain] = competitor
            
            # Récupérer les résultats SERP sans concurrent associé
            serp_stmt = select(SerpResult).where(
                and_(
                    SerpResult.project_id == project_id,
                    SerpResult.competitor_id.is_(None),
                    SerpResult.domain.is_not(None)
                )
            )
            serp_result = await self.session.execute(serp_stmt)
            serp_results = serp_result.scalars().all()
            
            updated_count = 0
            
            for serp_result in serp_results:
                normalized_domain = self.normalize_domain(serp_result.domain)
                
                if normalized_domain in domain_to_competitor:
                    competitor = domain_to_competitor[normalized_domain]
                    serp_result.competitor_id = competitor.id
                    updated_count += 1
            
            logger.info(
                "Associations concurrents mises à jour",
                project_id=project_id,
                updated_count=updated_count
            )
            
            return updated_count
            
        except Exception as e:
            logger.error(
                "Erreur lors de la mise à jour des associations",
                project_id=project_id,
                error=str(e)
            )
            raise DatabaseError(
                "Erreur lors de la mise à jour des associations",
                details={"project_id": project_id, "error": str(e)}
            ) 