"""Schemas Pydantic pour les mots-clés."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, validator


class KeywordBase(BaseModel):
    """Schema de base pour les mots-clés."""
    
    keyword: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Mot-clé à monitorer"
    )
    location: str = Field(
        default="France",
        max_length=50,
        description="Localisation pour le scraping"
    )
    language: str = Field(
        default="fr",
        max_length=10,
        description="Langue pour le scraping"
    )
    search_volume: Optional[int] = Field(
        None,
        ge=0,
        description="Volume de recherche mensuel"
    )
    is_active: bool = Field(
        default=True,
        description="Statut actif du mot-clé"
    )
    
    @validator('keyword')
    def validate_keyword(cls, v):
        """Valide et nettoie le mot-clé."""
        if not v:
            raise ValueError('Le mot-clé ne peut pas être vide')
        
        # Nettoyer le mot-clé
        keyword = v.strip()
        
        if len(keyword) < 1:
            raise ValueError('Le mot-clé doit contenir au moins 1 caractère')
        
        return keyword
    
    @validator('language')
    def validate_language(cls, v):
        """Valide le code de langue."""
        valid_languages = ['fr', 'en', 'es', 'de', 'it', 'pt', 'nl']
        if v not in valid_languages:
            raise ValueError(f'Langue non supportée. Langues valides: {", ".join(valid_languages)}')
        return v


class KeywordCreate(KeywordBase):
    """Schema pour la création d'un mot-clé."""
    pass


class KeywordUpdate(BaseModel):
    """Schema pour la mise à jour d'un mot-clé."""
    
    keyword: Optional[str] = Field(
        None,
        min_length=1,
        max_length=500,
        description="Mot-clé à monitorer"
    )
    location: Optional[str] = Field(
        None,
        max_length=50,
        description="Localisation pour le scraping"
    )
    language: Optional[str] = Field(
        None,
        max_length=10,
        description="Langue pour le scraping"
    )
    search_volume: Optional[int] = Field(
        None,
        ge=0,
        description="Volume de recherche mensuel"
    )
    is_active: Optional[bool] = Field(
        None,
        description="Statut actif du mot-clé"
    )
    
    @validator('keyword')
    def validate_keyword(cls, v):
        """Valide et nettoie le mot-clé."""
        if v is None:
            return v
        
        if not v:
            raise ValueError('Le mot-clé ne peut pas être vide')
        
        # Nettoyer le mot-clé
        keyword = v.strip()
        
        if len(keyword) < 1:
            raise ValueError('Le mot-clé doit contenir au moins 1 caractère')
        
        return keyword
    
    @validator('language')
    def validate_language(cls, v):
        """Valide le code de langue."""
        if v is None:
            return v
        
        valid_languages = ['fr', 'en', 'es', 'de', 'it', 'pt', 'nl']
        if v not in valid_languages:
            raise ValueError(f'Langue non supportée. Langues valides: {", ".join(valid_languages)}')
        return v


class KeywordResponse(KeywordBase):
    """Schema de réponse pour un mot-clé."""
    
    id: UUID = Field(..., description="Identifiant unique du mot-clé")
    project_id: UUID = Field(..., description="Identifiant du projet")
    created_at: datetime = Field(..., description="Date de création")
    
    # Propriétés calculées
    display_name: str = Field(
        ...,
        description="Nom d'affichage du mot-clé"
    )
    search_volume_display: str = Field(
        ...,
        description="Volume de recherche formaté"
    )
    difficulty_level: str = Field(
        ...,
        description="Niveau de difficulté (low/medium/high/unknown)"
    )
    
    model_config = ConfigDict(from_attributes=True)


class KeywordListResponse(BaseModel):
    """Schema de réponse pour une liste de mots-clés."""
    
    keywords: List[KeywordResponse] = Field(
        default_factory=list,
        description="Liste des mots-clés"
    )
    total: int = Field(
        ...,
        ge=0,
        description="Nombre total de mots-clés"
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


class KeywordPerformance(BaseModel):
    """Schema pour les performances d'un mot-clé."""
    
    keyword: KeywordResponse = Field(
        ...,
        description="Informations du mot-clé"
    )
    
    # Métriques de performance
    total_results: int = Field(
        ...,
        ge=0,
        description="Nombre total de résultats"
    )
    competitors_count: int = Field(
        ...,
        ge=0,
        description="Nombre de concurrents présents"
    )
    
    # Position de la marque principale
    main_brand_position: Optional[int] = Field(
        None,
        ge=1,
        description="Position de la marque principale"
    )
    main_brand_present: bool = Field(
        ...,
        description="Présence de la marque principale"
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
    price_range: Optional[float] = Field(
        None,
        ge=0.0,
        description="Écart de prix (max - min)"
    )
    
    # Données temporelles
    last_scrape_date: Optional[datetime] = Field(
        None,
        description="Date du dernier scraping"
    )
    scrape_frequency: Optional[str] = Field(
        None,
        description="Fréquence de scraping"
    )
    
    # Évolutions
    position_trend: Optional[str] = Field(
        None,
        description="Tendance de position (up/down/stable/new)"
    )
    price_trend: Optional[str] = Field(
        None,
        description="Tendance de prix (up/down/stable)"
    )
    competition_level: Optional[str] = Field(
        None,
        description="Niveau de concurrence (low/medium/high)"
    )


class KeywordHistory(BaseModel):
    """Schema pour l'historique d'un mot-clé."""
    
    keyword_id: UUID = Field(..., description="Identifiant du mot-clé")
    date: datetime = Field(..., description="Date du point de données")
    
    # Données de position
    main_brand_position: Optional[int] = Field(
        None,
        ge=1,
        description="Position de la marque principale"
    )
    competitors_count: int = Field(
        ...,
        ge=0,
        description="Nombre de concurrents"
    )
    
    # Données de prix
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
    
    # Métriques calculées
    visibility_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Score de visibilité"
    )


class KeywordHistoryResponse(BaseModel):
    """Schema de réponse pour l'historique d'un mot-clé."""
    
    keyword: KeywordResponse = Field(
        ...,
        description="Informations du mot-clé"
    )
    history: List[KeywordHistory] = Field(
        default_factory=list,
        description="Historique des données"
    )
    date_range: dict = Field(
        ...,
        description="Plage de dates de l'historique"
    )
    total_points: int = Field(
        ...,
        ge=0,
        description="Nombre total de points de données"
    ) 