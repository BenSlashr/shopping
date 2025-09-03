"""Schemas Pydantic pour les concurrents."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, validator


class CompetitorBase(BaseModel):
    """Schema de base pour les concurrents."""
    
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Nom du concurrent"
    )
    domain: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Domaine du concurrent"
    )
    brand_name: Optional[str] = Field(
        None,
        max_length=255,
        description="Nom de marque du concurrent"
    )
    is_main_brand: bool = Field(
        default=False,
        description="Indique si c'est la marque principale"
    )
    
    @validator('domain')
    def validate_domain(cls, v):
        """Valide et nettoie le domaine."""
        if not v:
            raise ValueError('Le domaine ne peut pas être vide')
        
        # Nettoyer le domaine
        domain = v.lower().strip()
        
        # Supprimer les préfixes communs
        prefixes = ['https://', 'http://', 'www.']
        for prefix in prefixes:
            if domain.startswith(prefix):
                domain = domain[len(prefix):]
        
        # Supprimer le slash final
        if domain.endswith('/'):
            domain = domain[:-1]
        
        # Validation basique du format de domaine
        if not domain or '.' not in domain:
            raise ValueError('Format de domaine invalide')
        
        return domain


class CompetitorCreate(CompetitorBase):
    """Schema pour la création d'un concurrent."""
    pass


class CompetitorUpdate(BaseModel):
    """Schema pour la mise à jour d'un concurrent."""
    
    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Nom du concurrent"
    )
    domain: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Domaine du concurrent"
    )
    brand_name: Optional[str] = Field(
        None,
        max_length=255,
        description="Nom de marque du concurrent"
    )
    is_main_brand: Optional[bool] = Field(
        None,
        description="Indique si c'est la marque principale"
    )
    
    @validator('domain')
    def validate_domain(cls, v):
        """Valide et nettoie le domaine."""
        if v is None:
            return v
        
        if not v:
            raise ValueError('Le domaine ne peut pas être vide')
        
        # Nettoyer le domaine
        domain = v.lower().strip()
        
        # Supprimer les préfixes communs
        prefixes = ['https://', 'http://', 'www.']
        for prefix in prefixes:
            if domain.startswith(prefix):
                domain = domain[len(prefix):]
        
        # Supprimer le slash final
        if domain.endswith('/'):
            domain = domain[:-1]
        
        # Validation basique du format de domaine
        if not domain or '.' not in domain:
            raise ValueError('Format de domaine invalide')
        
        return domain


class CompetitorResponse(CompetitorBase):
    """Schema de réponse pour un concurrent."""
    
    id: UUID = Field(..., description="Identifiant unique du concurrent")
    project_id: UUID = Field(..., description="Identifiant du projet")
    created_at: datetime = Field(..., description="Date de création")
    
    # Propriétés calculées
    display_name: str = Field(
        ...,
        description="Nom d'affichage du concurrent"
    )
    clean_domain: str = Field(
        ...,
        description="Domaine nettoyé"
    )
    
    model_config = ConfigDict(from_attributes=True)


class CompetitorListResponse(BaseModel):
    """Schema de réponse pour une liste de concurrents."""
    
    competitors: List[CompetitorResponse] = Field(
        default_factory=list,
        description="Liste des concurrents"
    )
    total: int = Field(
        ...,
        ge=0,
        description="Nombre total de concurrents"
    )
    page: int = Field(
        ...,
        ge=1,
        description="Page courante"
    )
    per_page: int = Field(
        ...,
        ge=1,
        le=100,
        description="Nombre d'éléments par page"
    )
    has_next: bool = Field(
        ...,
        description="Indique s'il y a une page suivante"
    )
    has_prev: bool = Field(
        ...,
        description="Indique s'il y a une page précédente"
    )


class CompetitorPerformance(BaseModel):
    """Schema pour les performances d'un concurrent."""
    
    competitor: CompetitorResponse = Field(
        ...,
        description="Informations du concurrent"
    )
    
    # Métriques de performance
    total_appearances: int = Field(
        ...,
        ge=0,
        description="Nombre total d'apparitions"
    )
    average_position: Optional[float] = Field(
        None,
        ge=1.0,
        description="Position moyenne"
    )
    best_position: Optional[int] = Field(
        None,
        ge=1,
        description="Meilleure position"
    )
    worst_position: Optional[int] = Field(
        None,
        ge=1,
        description="Pire position"
    )
    
    # Métriques de prix
    average_price: Optional[float] = Field(
        None,
        ge=0.0,
        description="Prix moyen"
    )
    min_price: Optional[float] = Field(
        None,
        ge=0.0,
        description="Prix minimum"
    )
    max_price: Optional[float] = Field(
        None,
        ge=0.0,
        description="Prix maximum"
    )
    
    # Métriques d'engagement
    average_rating: Optional[float] = Field(
        None,
        ge=0.0,
        le=5.0,
        description="Note moyenne"
    )
    total_reviews: Optional[int] = Field(
        None,
        ge=0,
        description="Nombre total d'avis"
    )
    
    # Visibilité
    visibility_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Score de visibilité (0-100)"
    )
    share_of_voice: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Part de voix (0-100)"
    )
    
    # Évolutions
    position_trend: Optional[str] = Field(
        None,
        description="Tendance de position (up/down/stable)"
    )
    price_trend: Optional[str] = Field(
        None,
        description="Tendance de prix (up/down/stable)"
    ) 