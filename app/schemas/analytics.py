"""Schémas Pydantic pour les analytics."""

from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field


class PeriodType(str, Enum):
    """Types de périodes pour les analyses."""
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


class MetricType(str, Enum):
    """Types de métriques."""
    SHARE_OF_VOICE = "share_of_voice"
    AVERAGE_POSITION = "average_position"
    PRICE_COMPETITIVENESS = "price_competitiveness"
    VISIBILITY_SCORE = "visibility_score"


# Schémas pour Share of Voice
class ShareOfVoiceItem(BaseModel):
    """Item de Share of Voice par concurrent."""
    competitor_id: str
    competitor_name: str
    domain: str
    appearances: int = Field(description="Nombre d'apparitions dans les SERP")
    total_keywords: int = Field(description="Nombre total de mots-clés surveillés")
    share_percentage: float = Field(description="Pourcentage de Share of Voice")
    average_position: float = Field(description="Position moyenne")
    price_competitiveness: Optional[float] = Field(description="Compétitivité prix (0-1)")


class ShareOfVoiceResponse(BaseModel):
    """Réponse Share of Voice."""
    project_id: str
    period_start: datetime
    period_end: datetime
    total_appearances: int
    competitors: List[ShareOfVoiceItem]
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Schémas pour Position Matrix
class PositionMatrixItem(BaseModel):
    """Item de la matrice de positions."""
    keyword: str
    keyword_id: str
    search_volume: Optional[int]
    competitors: Dict[str, Optional[int]] = Field(
        description="Position par concurrent (domain -> position)"
    )
    best_position: Optional[int] = Field(description="Meilleure position trouvée")
    worst_position: Optional[int] = Field(description="Pire position trouvée")
    opportunity_score: float = Field(description="Score d'opportunité (0-1)")


class PositionMatrixResponse(BaseModel):
    """Réponse matrice de positions."""
    project_id: str
    period_start: datetime
    period_end: datetime
    keywords: List[PositionMatrixItem]
    competitor_domains: List[str] = Field(description="Liste des domaines concurrents")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Schémas pour les opportunités
class OpportunityType(str, Enum):
    """Types d'opportunités."""
    KEYWORD_GAP = "keyword_gap"
    PRICE_ADVANTAGE = "price_advantage"
    POSITION_IMPROVEMENT = "position_improvement"
    NEW_COMPETITOR = "new_competitor"


class OpportunityItem(BaseModel):
    """Item d'opportunité."""
    type: OpportunityType
    title: str
    description: str
    keyword_id: Optional[str]
    keyword: Optional[str]
    competitor_domain: Optional[str]
    current_position: Optional[int]
    target_position: Optional[int]
    potential_gain: float = Field(description="Gain potentiel (0-1)")
    priority: str = Field(description="Priorité: high, medium, low")
    action_items: List[str] = Field(description="Actions recommandées")


class OpportunitiesResponse(BaseModel):
    """Réponse opportunités."""
    project_id: str
    analysis_date: datetime
    total_opportunities: int
    high_priority: int
    medium_priority: int
    low_priority: int
    opportunities: List[OpportunityItem]
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Schémas pour comparaisons concurrents
class CompetitorMetrics(BaseModel):
    """Métriques d'un concurrent."""
    competitor_id: str
    competitor_name: str
    domain: str
    total_appearances: int
    unique_keywords: int
    average_position: float
    best_position: int
    worst_position: int
    share_of_voice: float
    price_competitiveness: Optional[float]
    visibility_score: float = Field(description="Score de visibilité (0-100)")


class CompetitorComparison(BaseModel):
    """Comparaison entre concurrents."""
    main_brand: CompetitorMetrics
    competitors: List[CompetitorMetrics]
    period_start: datetime
    period_end: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Schémas pour analyse de tendances
class TrendDataPoint(BaseModel):
    """Point de données pour les tendances."""
    date: date
    value: float
    change_percentage: Optional[float] = Field(description="Changement par rapport à la période précédente")


class KeywordTrend(BaseModel):
    """Tendance d'un mot-clé."""
    keyword_id: str
    keyword: str
    metric_type: MetricType
    data_points: List[TrendDataPoint]
    trend_direction: str = Field(description="up, down, stable")
    total_change: float = Field(description="Changement total sur la période")


class TrendAnalysisResponse(BaseModel):
    """Réponse analyse de tendances."""
    project_id: str
    period_start: date
    period_end: date
    period_type: PeriodType
    keywords_trends: List[KeywordTrend]
    
    class Config:
        json_encoders = {
            date: lambda v: v.isoformat(),
            datetime: lambda v: v.isoformat()
        }


# Schémas pour le dashboard
class DashboardMetrics(BaseModel):
    """Métriques principales du dashboard."""
    total_keywords: int
    total_competitors: int
    average_position: Optional[float]
    share_of_voice: Optional[float]
    total_opportunities: int
    visibility_score: Optional[float]
    last_scrape_date: Optional[datetime]
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DashboardResponse(BaseModel):
    """Réponse dashboard projet."""
    project_id: str
    project_name: str
    metrics: DashboardMetrics
    top_keywords: List[Dict[str, Any]] = Field(description="Top 5 mots-clés par performance")
    top_competitors: List[Dict[str, Any]] = Field(description="Top 5 concurrents par visibilité")
    recent_changes: List[Dict[str, Any]] = Field(description="Changements récents")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Schémas pour les requêtes
class AnalyticsRequest(BaseModel):
    """Requête analytics de base."""
    project_id: str
    period_start: Optional[datetime] = Field(default=None, description="Début de période (défaut: 30 jours)")
    period_end: Optional[datetime] = Field(default=None, description="Fin de période (défaut: maintenant)")


class TrendRequest(AnalyticsRequest):
    """Requête pour analyse de tendances."""
    period_type: PeriodType = Field(default=PeriodType.DAY)
    metric_type: MetricType = Field(default=MetricType.AVERAGE_POSITION)
    keyword_ids: Optional[List[str]] = Field(default=None, description="IDs des mots-clés spécifiques")


class ComparisonRequest(AnalyticsRequest):
    """Requête pour comparaison concurrents."""
    competitor_ids: Optional[List[str]] = Field(default=None, description="IDs des concurrents spécifiques")
    include_main_brand: bool = Field(default=True, description="Inclure la marque principale") 