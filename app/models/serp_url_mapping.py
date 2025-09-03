"""Modèle pour le mapping entre résultats SERP et URLs uniques."""

from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class SerpUrlMapping(Base):
    """Mapping entre un résultat SERP et une URL unique."""
    
    __tablename__ = "serp_url_mapping"
    
    id = Column(String, primary_key=True, index=True)
    serp_result_id = Column(String, ForeignKey("serp_results.id"), nullable=False)
    unique_url_id = Column(String, ForeignKey("unique_urls.id"), nullable=False)
    position = Column(Integer, nullable=False)
    title = Column(Text)
    description = Column(Text)
    
    # Relations
    serp_result = relationship("SerpResult", back_populates="url_mappings")
    unique_url = relationship("UniqueUrl", back_populates="serp_mappings") 