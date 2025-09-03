"""Modèle Project pour la gestion des projets."""

import uuid
from datetime import datetime
from typing import List

from sqlalchemy import Column, String, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Project(Base):
    """Modèle pour les projets de monitoring."""
    
    __tablename__ = "projects"
    
    # Colonnes
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True
    )
    name = Column(
        String(255),
        nullable=False,
        index=True
    )
    description = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True
    )
    reference_site = Column(
        String(255),
        nullable=True,
        comment="Domaine de référence du site principal à surveiller (ex: monsite.com)"
    )
    
    # Relations
    competitors = relationship(
        "Competitor",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    keywords = relationship(
        "Keyword",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    serp_results = relationship(
        "SerpResult",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name='{self.name}', active={self.is_active})>"
    
    @property
    def competitors_count(self) -> int:
        """Nombre de concurrents dans le projet."""
        return len(self.competitors) if self.competitors else 0
    
    @property
    def keywords_count(self) -> int:
        """Nombre de mots-clés dans le projet."""
        return len([k for k in self.keywords if k.is_active]) if self.keywords else 0
    
    @property
    def main_brand(self):
        """Récupère la marque principale du projet."""
        if self.competitors:
            main_brands = [c for c in self.competitors if c.is_main_brand]
            return main_brands[0] if main_brands else None
        return None 