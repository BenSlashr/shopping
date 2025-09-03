"""Schemas Pydantic pour les projets."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class ProjectBase(BaseModel):
    """Schema de base pour les projets."""
    
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Nom du projet"
    )
    description: Optional[str] = Field(
        None,
        max_length=2000,
        description="Description du projet"
    )
    is_active: bool = Field(
        default=True,
        description="Statut actif du projet"
    )


class ProjectCreate(ProjectBase):
    """Schema pour la création d'un projet."""
    pass


class ProjectUpdate(BaseModel):
    """Schema pour la mise à jour d'un projet."""
    
    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Nom du projet"
    )
    description: Optional[str] = Field(
        None,
        max_length=2000,
        description="Description du projet"
    )
    is_active: Optional[bool] = Field(
        None,
        description="Statut actif du projet"
    )


class ProjectResponse(ProjectBase):
    """Schema de réponse pour un projet."""
    
    id: UUID = Field(..., description="Identifiant unique du projet")
    created_at: datetime = Field(..., description="Date de création")
    updated_at: datetime = Field(..., description="Date de dernière mise à jour")
    
    # Propriétés calculées
    competitors_count: int = Field(
        default=0,
        description="Nombre de concurrents"
    )
    keywords_count: int = Field(
        default=0,
        description="Nombre de mots-clés actifs"
    )
    
    model_config = ConfigDict(from_attributes=True)


class ProjectListResponse(BaseModel):
    """Schema de réponse pour une liste de projets."""
    
    projects: List[ProjectResponse] = Field(
        default_factory=list,
        description="Liste des projets"
    )
    total: int = Field(
        ...,
        ge=0,
        description="Nombre total de projets"
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


class ProjectDashboard(BaseModel):
    """Schema pour le dashboard d'un projet."""
    
    project: ProjectResponse = Field(
        ...,
        description="Informations du projet"
    )
    
    # Métriques globales
    total_keywords: int = Field(
        ...,
        ge=0,
        description="Nombre total de mots-clés"
    )
    active_keywords: int = Field(
        ...,
        ge=0,
        description="Nombre de mots-clés actifs"
    )
    total_competitors: int = Field(
        ...,
        ge=0,
        description="Nombre total de concurrents"
    )
    
    # Métriques de performance
    average_position: Optional[float] = Field(
        None,
        ge=1.0,
        description="Position moyenne"
    )
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
    
    # Données temporelles
    last_scrape_date: Optional[datetime] = Field(
        None,
        description="Date du dernier scraping"
    )
    total_serp_results: int = Field(
        ...,
        ge=0,
        description="Nombre total de résultats SERP"
    )
    
    # Évolutions (comparaison avec période précédente)
    position_change: Optional[float] = Field(
        None,
        description="Changement de position moyenne"
    )
    visibility_change: Optional[float] = Field(
        None,
        description="Changement de visibilité"
    )
    share_of_voice_change: Optional[float] = Field(
        None,
        description="Changement de part de voix"
    ) 