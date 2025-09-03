"""Schemas Pydantic pour Shopping Monitor."""

from app.schemas.project_schemas import (
    ProjectBase,
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
    ProjectDashboard
)

from app.schemas.competitor_schemas import (
    CompetitorBase,
    CompetitorCreate,
    CompetitorUpdate,
    CompetitorResponse,
    CompetitorListResponse
)

from app.schemas.keyword_schemas import (
    KeywordBase,
    KeywordCreate,
    KeywordUpdate,
    KeywordResponse,
    KeywordListResponse
)

from app.schemas.analytics_schemas import (
    SerpResultResponse,
    AnalyticsResponse,
    ShareOfVoiceResponse,
    PositionMatrixResponse,
    OpportunityResponse
)

__all__ = [
    # Project schemas
    "ProjectBase",
    "ProjectCreate", 
    "ProjectUpdate",
    "ProjectResponse",
    "ProjectListResponse",
    "ProjectDashboard",
    
    # Competitor schemas
    "CompetitorBase",
    "CompetitorCreate",
    "CompetitorUpdate", 
    "CompetitorResponse",
    "CompetitorListResponse",
    
    # Keyword schemas
    "KeywordBase",
    "KeywordCreate",
    "KeywordUpdate",
    "KeywordResponse", 
    "KeywordListResponse",
    
    # Analytics schemas
    "SerpResultResponse",
    "AnalyticsResponse",
    "ShareOfVoiceResponse",
    "PositionMatrixResponse",
    "OpportunityResponse",
] 