"""Modèles UniqueUrl et SerpUrlMapping pour la déduplication des URLs."""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Index, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# Modèle adapté pour SQLite

from app.database import Base


class UniqueUrl(Base):
    """Modèle pour les URLs uniques (déduplication scraping)."""
    
    __tablename__ = "unique_urls"
    
    # Colonnes
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True
    )
    url = Column(
        Text,
        unique=True,
        nullable=False,
        index=True
    )
    domain = Column(
        String(255),
        nullable=True,
        index=True
    )
    last_scraped = Column(
        DateTime(timezone=True),
        nullable=True
    )
    product_data = Column(
        JSON,
        nullable=True,
        comment="Données scrapées (prix, images, etc.)"
    )
    scraping_status = Column(
        String(50),
        default="pending",
        nullable=False,
        index=True
    )
    
    # Relations
    serp_mappings = relationship(
        "SerpUrlMapping",
        back_populates="unique_url",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<UniqueUrl(id={self.id}, domain='{self.domain}', status='{self.scraping_status}')>"
    
    @property
    def clean_domain(self) -> str:
        """Domaine nettoyé (sans www, http, etc.)."""
        if not self.domain:
            return ""
        
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
    
    @property
    def is_scraped(self) -> bool:
        """Vérifie si l'URL a été scrapée."""
        return self.scraping_status == "completed" and self.product_data is not None
    
    @property
    def needs_scraping(self) -> bool:
        """Vérifie si l'URL a besoin d'être scrapée."""
        return self.scraping_status in ["pending", "failed"]
    
    def extract_domain_from_url(self):
        """Extrait le domaine de l'URL."""
        if not self.url:
            return
        
        try:
            from urllib.parse import urlparse
            parsed = urlparse(self.url)
            self.domain = parsed.netloc.lower()
        except Exception:
            # En cas d'erreur, essayer une extraction simple
            if '://' in self.url:
                self.domain = self.url.split('://')[1].split('/')[0].lower()


class SerpUrlMapping(Base):
    """Table de liaison entre SerpResult et UniqueUrl."""
    
    __tablename__ = "serp_url_mapping"
    
    # Colonnes (clés étrangères composites)
    serp_result_id = Column(
        String(36),
        ForeignKey("serp_results.id", ondelete="CASCADE"),
        primary_key=True
    )
    unique_url_id = Column(
        String(36),
        ForeignKey("unique_urls.id", ondelete="CASCADE"),
        primary_key=True
    )
    
    # Relations
    serp_result = relationship("SerpResult")
    unique_url = relationship(
        "UniqueUrl",
        back_populates="serp_mappings"
    )
    
    def __repr__(self) -> str:
        return f"<SerpUrlMapping(serp_result_id={self.serp_result_id}, unique_url_id={self.unique_url_id})>" 