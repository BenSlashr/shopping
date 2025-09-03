"""Modèle Keyword pour la gestion des mots-clés."""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Keyword(Base):
    """Modèle pour les mots-clés d'un projet."""
    
    __tablename__ = "keywords"
    
    # Colonnes
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True
    )
    project_id = Column(
        String(36),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    keyword = Column(
        String(500),
        nullable=False,
        index=True
    )
    location = Column(
        String(50),
        default="France",
        nullable=False
    )
    language = Column(
        String(10),
        default="fr",
        nullable=False
    )
    search_volume = Column(
        Integer,
        nullable=True,
        index=True
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True
    )
    
    # Relations
    project = relationship(
        "Project",
        back_populates="keywords"
    )
    serp_results = relationship(
        "SerpResult",
        back_populates="keyword",
        cascade="all, delete-orphan"
    )
    
    # Contraintes
    __table_args__ = (
        UniqueConstraint(
            'project_id', 'keyword', 'location',
            name='uq_keyword_project_keyword_location'
        ),
    )
    
    def __repr__(self) -> str:
        volume_info = f", volume={self.search_volume}" if self.search_volume else ""
        return f"<Keyword(id={self.id}, keyword='{self.keyword}', location='{self.location}'{volume_info})>"
    
    @property
    def display_name(self) -> str:
        """Nom d'affichage du mot-clé avec localisation."""
        if self.location and self.location != "France":
            return f"{self.keyword} ({self.location})"
        return self.keyword
    
    @property
    def search_volume_display(self) -> str:
        """Volume de recherche formaté pour l'affichage."""
        if not self.search_volume:
            return "N/A"
        
        if self.search_volume >= 1000000:
            return f"{self.search_volume // 1000000}M"
        elif self.search_volume >= 1000:
            return f"{self.search_volume // 1000}K"
        else:
            return str(self.search_volume)
    
    @property
    def difficulty_level(self) -> str:
        """Niveau de difficulté basé sur le volume de recherche."""
        if not self.search_volume:
            return "unknown"
        
        if self.search_volume >= 10000:
            return "high"
        elif self.search_volume >= 1000:
            return "medium"
        else:
            return "low" 