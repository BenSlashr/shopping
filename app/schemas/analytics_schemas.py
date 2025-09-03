"""Schemas Pydantic pour les analytics."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from decimal import Decimal

from pydantic import BaseModel, Field, ConfigDict


class SerpResultResponse(BaseModel):
    """Schema de réponse pour un résultat SERP."""
    
    id: UUID = Field(..., description="Identifiant unique du résultat")
    project_id: UUID = Field(..., description="Identifiant du projet")
    keyword_id: UUID = Field(..., description="Identifiant du mot-clé")
    competitor_id: Optional[UUID] = Field(None, description="Identifiant du concurrent")
    scraped_at: datetime = Field(..., description="Date de scraping")
    
    # Données ranking
    position: Optional[int] = Field(None, ge=1, description="Position dans les résultats")
    url: Optional[str] = Field(None, description="URL du produit")
    domain: Optional[str] = Field(None, description="Domaine")
    title: Optional[str] = Field(None, description="Titre du produit")
    description: Optional[str] = Field(None, description="Description")
    
    # Données produit
    price: Optional[Decimal] = Field(None, ge=0, description="Prix")
    currency: Optional[str] = Field(None, description="Devise")
    price_original: Optional[Decimal] = Field(None, ge=0, description="Prix original")
    discount_percentage: Optional[int] = Field(None, ge=0, le=100, description="Pourcentage de réduction")
    availability: Optional[str] = Field(None, description="Disponibilité")
    stock_status: Optional[str] = Field(None, description="Statut du stock")
    
    # Données marchand
    merchant_name: Optional[str] = Field(None, description="Nom du marchand")
    merchant_url: Optional[str] = Field(None, description="URL du marchand")
    
    # Données engagement
    rating: Optional[Decimal] = Field(None, ge=0, le=5, description="Note")
    reviews_count: Optional[int] = Field(None, ge=0, description="Nombre d'avis")
    
    # Données visuelles
    image_url: Optional[str] = Field(None, description="URL de l'image")
    additional_images: Optional[Dict[str, Any]] = Field(None, description="Images supplémentaires")
    
    # Propriétés calculées
    formatted_price: str = Field(..., description="Prix formaté")
    has_discount: bool = Field(..., description="A une réduction")
    calculated_discount_percentage: int = Field(..., description="Pourcentage de réduction calculé")
    rating_display: str = Field(..., description="Note formatée")
    is_available: bool = Field(..., description="Est disponible")
    
    model_config = ConfigDict(from_attributes=True)


class AnalyticsResponse(BaseModel):
    """Schema de réponse pour les analytics générales."""
    
    project_id: UUID = Field(..., description="Identifiant du projet")
    date_range: Dict[str, datetime] = Field(..., description="Plage de dates analysée")
    
    # Métriques globales
    total_keywords: int = Field(..., ge=0, description="Nombre total de mots-clés")
    active_keywords: int = Field(..., ge=0, description="Nombre de mots-clés actifs")
    total_competitors: int = Field(..., ge=0, description="Nombre total de concurrents")
    total_serp_results: int = Field(..., ge=0, description="Nombre total de résultats SERP")
    
    # Métriques de performance
    average_position: Optional[float] = Field(None, ge=1.0, description="Position moyenne")
    visibility_score: Optional[float] = Field(None, ge=0.0, le=100.0, description="Score de visibilité")
    share_of_voice: Optional[float] = Field(None, ge=0.0, le=100.0, description="Part de voix")
    
    # Métriques de prix
    average_price: Optional[float] = Field(None, ge=0.0, description="Prix moyen")
    min_price: Optional[float] = Field(None, ge=0.0, description="Prix minimum")
    max_price: Optional[float] = Field(None, ge=0.0, description="Prix maximum")
    price_competitiveness: Optional[float] = Field(
        None, ge=0.0, le=100.0, description="Compétitivité prix (0-100)"
    )
    
    # Évolutions (comparaison avec période précédente)
    position_change: Optional[float] = Field(None, description="Changement de position")
    visibility_change: Optional[float] = Field(None, description="Changement de visibilité")
    share_of_voice_change: Optional[float] = Field(None, description="Changement de part de voix")
    price_change: Optional[float] = Field(None, description="Changement de prix moyen")
    
    # Données temporelles
    last_update: datetime = Field(..., description="Dernière mise à jour")


class ShareOfVoiceResponse(BaseModel):
    """Schema de réponse pour la part de voix."""
    
    project_id: UUID = Field(..., description="Identifiant du projet")
    date_range: Dict[str, datetime] = Field(..., description="Plage de dates")
    
    # Part de voix par concurrent
    competitors_share: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Part de voix par concurrent"
    )
    
    # Évolution temporelle
    timeline: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Évolution de la part de voix dans le temps"
    )
    
    # Métriques globales
    total_appearances: int = Field(..., ge=0, description="Nombre total d'apparitions")
    main_brand_share: Optional[float] = Field(
        None, ge=0.0, le=100.0, description="Part de voix de la marque principale"
    )
    top_competitor_share: Optional[float] = Field(
        None, ge=0.0, le=100.0, description="Part de voix du principal concurrent"
    )
    
    # Insights
    dominant_competitor: Optional[str] = Field(None, description="Concurrent dominant")
    market_concentration: Optional[float] = Field(
        None, ge=0.0, le=100.0, description="Concentration du marché"
    )


class PositionMatrixResponse(BaseModel):
    """Schema de réponse pour la matrice des positions."""
    
    project_id: UUID = Field(..., description="Identifiant du projet")
    date_range: Dict[str, datetime] = Field(..., description="Plage de dates")
    
    # Matrice positions (keyword x competitor)
    matrix: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Matrice des positions"
    )
    
    # Statistiques par mot-clé
    keywords_stats: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Statistiques par mot-clé"
    )
    
    # Statistiques par concurrent
    competitors_stats: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Statistiques par concurrent"
    )
    
    # Métriques globales
    total_positions: int = Field(..., ge=0, description="Nombre total de positions")
    average_position: Optional[float] = Field(None, ge=1.0, description="Position moyenne")
    best_performing_keyword: Optional[str] = Field(None, description="Meilleur mot-clé")
    worst_performing_keyword: Optional[str] = Field(None, description="Pire mot-clé")


class OpportunityResponse(BaseModel):
    """Schema de réponse pour les opportunités."""
    
    project_id: UUID = Field(..., description="Identifiant du projet")
    analysis_date: datetime = Field(..., description="Date d'analyse")
    
    # Opportunités manquées
    missed_opportunities: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Opportunités manquées"
    )
    
    # Mots-clés avec potentiel
    potential_keywords: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Mots-clés avec potentiel"
    )
    
    # Gaps concurrentiels
    competitive_gaps: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Gaps concurrentiels"
    )
    
    # Opportunités de prix
    price_opportunities: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Opportunités de prix"
    )
    
    # Métriques d'opportunité
    total_opportunities: int = Field(..., ge=0, description="Nombre total d'opportunités")
    high_priority_count: int = Field(..., ge=0, description="Opportunités haute priorité")
    medium_priority_count: int = Field(..., ge=0, description="Opportunités moyenne priorité")
    low_priority_count: int = Field(..., ge=0, description="Opportunités basse priorité")
    
    # Potentiel estimé
    estimated_traffic_gain: Optional[int] = Field(
        None, ge=0, description="Gain de trafic estimé"
    )
    estimated_revenue_impact: Optional[float] = Field(
        None, ge=0.0, description="Impact revenus estimé"
    )


class TrendAnalysisResponse(BaseModel):
    """Schema de réponse pour l'analyse des tendances."""
    
    project_id: UUID = Field(..., description="Identifiant du projet")
    metric: str = Field(..., description="Métrique analysée")
    date_range: Dict[str, datetime] = Field(..., description="Plage de dates")
    
    # Données temporelles
    timeline: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Données temporelles"
    )
    
    # Analyse de tendance
    trend_direction: str = Field(..., description="Direction de la tendance (up/down/stable)")
    trend_strength: float = Field(..., ge=0.0, le=1.0, description="Force de la tendance")
    correlation_coefficient: Optional[float] = Field(
        None, ge=-1.0, le=1.0, description="Coefficient de corrélation"
    )
    
    # Prédictions
    predicted_values: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Valeurs prédites"
    )
    confidence_interval: Optional[Dict[str, float]] = Field(
        None, description="Intervalle de confiance"
    )
    
    # Insights
    key_insights: List[str] = Field(
        default_factory=list,
        description="Insights clés"
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Recommandations"
    )


class CompetitorComparisonResponse(BaseModel):
    """Schema de réponse pour la comparaison de concurrents."""
    
    project_id: UUID = Field(..., description="Identifiant du projet")
    competitors: List[UUID] = Field(..., description="Concurrents comparés")
    date_range: Dict[str, datetime] = Field(..., description="Plage de dates")
    
    # Comparaison des métriques
    metrics_comparison: Dict[str, List[Dict[str, Any]]] = Field(
        default_factory=dict,
        description="Comparaison des métriques"
    )
    
    # Analyse SWOT simplifiée
    competitive_analysis: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Analyse concurrentielle"
    )
    
    # Benchmarking
    market_leader: Optional[str] = Field(None, description="Leader du marché")
    performance_ranking: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Classement de performance"
    )
    
    # Recommandations stratégiques
    strategic_recommendations: List[str] = Field(
        default_factory=list,
        description="Recommandations stratégiques"
    ) 