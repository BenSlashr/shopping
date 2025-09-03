"""Modèle Competitor pour la gestion des concurrents."""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Competitor(Base):
    """Modèle pour les concurrents d'un projet."""
    
    __tablename__ = "competitors"
    
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
    name = Column(
        String(255),
        nullable=False
    )
    domain = Column(
        String(255),
        nullable=False,
        index=True
    )
    brand_name = Column(
        String(255),
        nullable=True
    )
    is_main_brand = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Relations
    project = relationship(
        "Project",
        back_populates="competitors"
    )
    serp_results = relationship(
        "SerpResult",
        back_populates="competitor",
        cascade="all, delete-orphan"
    )
    
    # Contraintes
    __table_args__ = (
        UniqueConstraint(
            'project_id', 'domain',
            name='uq_competitor_project_domain'
        ),
    )
    
    def __repr__(self) -> str:
        brand_info = f", main_brand={self.is_main_brand}" if self.is_main_brand else ""
        return f"<Competitor(id={self.id}, name='{self.name}', domain='{self.domain}'{brand_info})>"
    
    @property
    def display_name(self) -> str:
        """Nom d'affichage du concurrent."""
        return self.brand_name if self.brand_name else self.name
    
    @property
    def clean_domain(self) -> str:
        """Domaine nettoyé (sans www, http, etc.)."""
        domain = self.domain.lower()
        # Supprimer les préfixes communs
        prefixes = ['https://', 'http://', 'www.']
        for prefix in prefixes:
            if domain.startswith(prefix):
                domain = domain[len(prefix):]
        # Supprimer le slash final
        if domain.endswith('/'):
            domain = domain[:-1]
        return domain 