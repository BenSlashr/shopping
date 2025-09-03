"""Endpoints API pour les analytics."""

from datetime import datetime, date, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.database import get_async_session
from app.services.analytics_service import AnalyticsService
from app.schemas.analytics import (
    ShareOfVoiceResponse,
    PositionMatrixResponse,
    OpportunitiesResponse,
    CompetitorComparison,
    TrendAnalysisResponse,
    DashboardResponse,
    AnalyticsRequest,
    TrendRequest,
    ComparisonRequest,
    PeriodType,
    MetricType
)

logger = structlog.get_logger()

router = APIRouter()


@router.get("/dashboard/{project_id}", response_model=DashboardResponse)
async def get_dashboard_metrics(
    project_id: str,
    db: AsyncSession = Depends(get_async_session)
):
    """Récupère les métriques du dashboard pour un projet."""
    logger.info("Endpoint Dashboard", project_id=project_id)
    
    try:
        analytics_service = AnalyticsService(db)
        result = await analytics_service.get_dashboard_metrics(project_id=project_id)
        return result
    except Exception as e:
        logger.error("Erreur récupération dashboard", error=str(e), project_id=project_id)
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération: {str(e)}")


@router.get("/share-of-voice/{project_id}", response_model=ShareOfVoiceResponse)
async def get_share_of_voice(
    project_id: str,
    period_start: Optional[datetime] = Query(None, description="Début de période (ISO format)"),
    period_end: Optional[datetime] = Query(None, description="Fin de période (ISO format)"),
    db: AsyncSession = Depends(get_async_session)
):
    """Calcule le Share of Voice pour un projet."""
    logger.info("Endpoint Share of Voice", project_id=project_id)
    
    try:
        analytics_service = AnalyticsService(db)
        result = await analytics_service.get_share_of_voice(
            project_id=project_id,
            period_start=period_start,
            period_end=period_end
        )
        return result
    except Exception as e:
        logger.error("Erreur calcul Share of Voice", error=str(e), project_id=project_id)
        raise HTTPException(status_code=500, detail=f"Erreur lors du calcul: {str(e)}")


@router.get("/position-matrix/{project_id}", response_model=PositionMatrixResponse)
async def get_position_matrix(
    project_id: str,
    period_start: Optional[datetime] = Query(None, description="Début de période (ISO format)"),
    period_end: Optional[datetime] = Query(None, description="Fin de période (ISO format)"),
    db: AsyncSession = Depends(get_async_session)
):
    """Calcule la matrice de positions pour un projet."""
    logger.info("Endpoint Position Matrix", project_id=project_id)
    
    try:
        analytics_service = AnalyticsService(db)
        result = await analytics_service.get_position_matrix(project_id=project_id)
        return result
    except Exception as e:
        logger.error("Erreur calcul Position Matrix", error=str(e), project_id=project_id)
        raise HTTPException(status_code=500, detail=f"Erreur lors du calcul: {str(e)}")


@router.get("/opportunities/{project_id}", response_model=OpportunitiesResponse)
async def get_opportunities(
    project_id: str,
    db: AsyncSession = Depends(get_async_session)
):
    """Récupère les opportunités pour un projet."""
    logger.info("Endpoint Opportunities", project_id=project_id)
    
    try:
        analytics_service = AnalyticsService(db)
        result = await analytics_service.get_opportunities(project_id=project_id)
        return result
    except Exception as e:
        logger.error("Erreur récupération opportunités", error=str(e), project_id=project_id)
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération: {str(e)}")


@router.get("/keywords-positions/{project_id}")
async def get_keywords_positions(
    project_id: str,
    session: AsyncSession = Depends(get_async_session)
):
    """Récupérer les positions détaillées de tous les mots-clés pour un projet."""
    try:
        service = AnalyticsService(session)
        result = await service.get_keywords_positions(project_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erreur lors de la récupération des positions", error=str(e))
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération: {str(e)}")


@router.get("/competitors/{project_id}", response_model=CompetitorComparison)
async def get_competitor_comparison(
    project_id: str,
    period_start: Optional[datetime] = Query(None, description="Début de période (ISO format)"),
    period_end: Optional[datetime] = Query(None, description="Fin de période (ISO format)"),
    competitor_ids: Optional[List[str]] = Query(None, description="IDs des concurrents spécifiques"),
    db: AsyncSession = Depends(get_async_session)
):
    """Compare les concurrents pour un projet."""
    logger.info("Endpoint Competitor Comparison", project_id=project_id)
    
    try:
        analytics_service = AnalyticsService(db)
        # TODO: Implémenter get_competitor_comparison
        raise HTTPException(status_code=501, detail="Fonctionnalité à venir")
    except Exception as e:
        logger.error("Erreur comparaison concurrents", error=str(e), project_id=project_id)
        raise HTTPException(status_code=500, detail=f"Erreur lors de la comparaison: {str(e)}")


@router.get("/trends/{project_id}", response_model=TrendAnalysisResponse)
async def get_trend_analysis(
    project_id: str,
    period_start: Optional[date] = Query(None, description="Début de période (YYYY-MM-DD)"),
    period_end: Optional[date] = Query(None, description="Fin de période (YYYY-MM-DD)"),
    period_type: PeriodType = Query(PeriodType.DAY, description="Type de période"),
    metric_type: MetricType = Query(MetricType.AVERAGE_POSITION, description="Type de métrique"),
    keyword_ids: Optional[List[str]] = Query(None, description="IDs des mots-clés spécifiques"),
    db: AsyncSession = Depends(get_async_session)
):
    """Analyse les tendances pour un projet."""
    logger.info("Endpoint Trend Analysis", project_id=project_id)
    
    try:
        analytics_service = AnalyticsService(db)
        # TODO: Implémenter get_trend_analysis
        raise HTTPException(status_code=501, detail="Fonctionnalité à venir")
    except Exception as e:
        logger.error("Erreur analyse tendances", error=str(e), project_id=project_id)
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse: {str(e)}")


# Endpoints pour les requêtes POST avec body JSON
@router.post("/share-of-voice/", response_model=ShareOfVoiceResponse)
async def calculate_share_of_voice_post(
    request: AnalyticsRequest,
    db: AsyncSession = Depends(get_async_session)
):
    """Calcule le Share of Voice avec requête POST."""
    logger.info("Endpoint Share of Voice POST", project_id=request.project_id)
    
    try:
        analytics_service = AnalyticsService(db)
        result = await analytics_service.get_share_of_voice(
            project_id=request.project_id,
            period_start=request.period_start,
            period_end=request.period_end
        )
        return result
    except Exception as e:
        logger.error("Erreur calcul Share of Voice POST", error=str(e), project_id=request.project_id)
        raise HTTPException(status_code=500, detail=f"Erreur lors du calcul: {str(e)}")


@router.post("/trends/", response_model=TrendAnalysisResponse)
async def analyze_trends_post(
    request: TrendRequest,
    db: AsyncSession = Depends(get_async_session)
):
    """Analyse les tendances avec requête POST."""
    logger.info("Endpoint Trend Analysis POST", project_id=request.project_id)
    
    try:
        analytics_service = AnalyticsService(db)
        # TODO: Implémenter get_trend_analysis
        raise HTTPException(status_code=501, detail="Fonctionnalité à venir")
    except Exception as e:
        logger.error("Erreur analyse tendances POST", error=str(e), project_id=request.project_id)
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse: {str(e)}")


@router.post("/competitors/", response_model=CompetitorComparison)
async def compare_competitors_post(
    request: ComparisonRequest,
    db: AsyncSession = Depends(get_async_session)
):
    """Compare les concurrents avec requête POST."""
    logger.info("Endpoint Competitor Comparison POST", project_id=request.project_id)
    
    try:
        analytics_service = AnalyticsService(db)
        # TODO: Implémenter get_competitor_comparison
        raise HTTPException(status_code=501, detail="Fonctionnalité à venir")
    except Exception as e:
        logger.error("Erreur comparaison concurrents POST", error=str(e), project_id=request.project_id)
        raise HTTPException(status_code=500, detail=f"Erreur lors de la comparaison: {str(e)}")


# Endpoints utilitaires
@router.get("/health")
async def health_check():
    """Vérification de santé du service analytics."""
    return {
        "status": "healthy",
        "service": "analytics",
        "timestamp": datetime.utcnow().isoformat()
    } 