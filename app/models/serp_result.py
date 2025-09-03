"""Modèle SerpResult pour les résultats SERP DataForSEO."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Index, JSON
from sqlalchemy import DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# Modèle adapté pour SQLite

from app.database import Base


class SerpResult(Base):
    """Modèle pour les résultats SERP Google Shopping."""
    
    __tablename__ = "serp_results"
    
    # Colonnes principales
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
    keyword_id = Column(
        String(36),
        ForeignKey("keywords.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    competitor_id = Column(
        String(36),
        ForeignKey("competitors.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    scraped_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    
    # Données ranking DataForSEO
    position = Column(
        Integer,
        nullable=True,
        index=True
    )
    url = Column(
        Text,
        nullable=True
    )
    domain = Column(
        String(255),
        nullable=True,
        index=True
    )
    title = Column(
        Text,
        nullable=True
    )
    description = Column(
        Text,
        nullable=True
    )
    
    # Données produit
    price = Column(
        DECIMAL(10, 2),
        nullable=True,
        index=True
    )
    currency = Column(
        String(10),
        nullable=True
    )
    price_original = Column(
        DECIMAL(10, 2),
        nullable=True
    )
    discount_percentage = Column(
        Integer,
        nullable=True
    )
    availability = Column(
        String(50),
        nullable=True
    )
    stock_status = Column(
        String(50),
        nullable=True
    )
    
    # Données marchand
    merchant_name = Column(
        String(255),
        nullable=True,
        index=True
    )
    merchant_url = Column(
        Text,
        nullable=True
    )
    
    # Données engagement
    rating = Column(
        DECIMAL(3, 2),
        nullable=True
    )
    reviews_count = Column(
        Integer,
        nullable=True
    )
    
    # Données visuelles
    image_url = Column(
        Text,
        nullable=True
    )
    additional_images = Column(
        JSON,
        nullable=True
    )
    
    # Données brutes complètes DataForSEO
    raw_data = Column(
        JSON,
        nullable=True
    )
    
    # Relations
    project = relationship(
        "Project",
        back_populates="serp_results"
    )
    keyword = relationship(
        "Keyword",
        back_populates="serp_results"
    )
    competitor = relationship(
        "Competitor",
        back_populates="serp_results"
    )
    
    # Index composites pour performance
    __table_args__ = (
        Index(
            'idx_serp_project_keyword_scraped',
            'project_id', 'keyword_id', 'scraped_at'
        ),
        Index(
            'idx_serp_competitor_scraped',
            'competitor_id', 'scraped_at'
        ),
        Index(
            'idx_serp_position_scraped',
            'position', 'scraped_at'
        ),
        Index(
            'idx_serp_domain_scraped',
            'domain', 'scraped_at'
        ),
    )
    
    def __repr__(self) -> str:
        pos_info = f", pos={self.position}" if self.position else ""
        price_info = f", price={self.price}" if self.price else ""
        return f"<SerpResult(id={self.id}, domain='{self.domain}'{pos_info}{price_info})>"
    
    @property
    def formatted_price(self) -> str:
        """Prix formaté pour l'affichage."""
        if not self.price:
            return "N/A"
        
        currency_symbol = {
            'EUR': '€',
            'USD': '$',
            'GBP': '£'
        }.get(self.currency, self.currency or '')
        
        return f"{self.price:.2f} {currency_symbol}".strip()
    
    @property
    def has_discount(self) -> bool:
        """Vérifie si le produit a une réduction."""
        return (
            self.price_original is not None and 
            self.price is not None and 
            self.price < self.price_original
        )
    
    @property
    def calculated_discount_percentage(self) -> int:
        """Calcule le pourcentage de réduction si pas fourni."""
        if self.discount_percentage:
            return self.discount_percentage
        
        if self.has_discount:
            discount = ((self.price_original - self.price) / self.price_original) * 100
            return int(round(discount))
        
        return 0
    
    @property
    def rating_display(self) -> str:
        """Note formatée pour l'affichage."""
        if not self.rating:
            return "N/A"
        
        rating_str = f"{self.rating:.1f}"
        if self.reviews_count:
            return f"{rating_str} ({self.reviews_count} avis)"
        return rating_str
    
    @property
    def is_available(self) -> bool:
        """Vérifie si le produit est disponible."""
        if self.availability:
            return self.availability.lower() in ['in_stock', 'available', 'in stock']
        if self.stock_status:
            return self.stock_status.lower() in ['in_stock', 'available', 'in stock']
        return True  # Par défaut, considérer comme disponible 