"""API endpoints pour le scraping et l'analyse SERP."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import structlog

from app.database import get_async_session
from app.models.project import Project
from app.services.dataforseo_service import DataForSEOService

logger = structlog.get_logger()

router = APIRouter()

@router.post("/projects/{project_id}/analyze")
async def analyze_project_keywords(
    project_id: str,
    keyword_ids: Optional[List[str]] = Query(None),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Lancer l'analyse SERP pour un projet avec DataForSEO.
    
    Args:
        project_id: ID du projet à analyser
        keyword_ids: Liste optionnelle d'IDs de mots-clés spécifiques
        session: Session de base de données
    """
    logger.info("Demande d'analyse SERP", project_id=project_id)
    
    # Vérifier que le projet existe
    project_query = select(Project).where(Project.id == project_id)
    project_result = await session.execute(project_query)
    project = project_result.scalar_one_or_none()
    
    if not project:
        logger.error("Projet non trouvé", project_id=project_id)
        raise HTTPException(status_code=404, detail=f"Projet {project_id} non trouvé")
    
    try:
        # Créer le service DataForSEO
        dataforseo_service = DataForSEOService()
        
        # Lancer l'analyse directement (pour l'instant)
        result = await dataforseo_service.analyze_keywords_for_project(
            session=session,
            project_id=project_id,
            keyword_ids=keyword_ids
        )
        
        logger.info("Analyse SERP terminée", project_id=project_id, **result.get('stats', {}))
        
        return {
            "message": "Analyse SERP terminée avec succès",
            "project_id": project_id,
            "status": "completed",
            "result": result
        }
        
    except Exception as e:
        logger.error("Erreur lors de l'analyse", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'analyse SERP: {str(e)}"
        )


@router.get("/projects/{project_id}/analysis-status")
async def get_analysis_status(
    project_id: str,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Récupérer le statut de la dernière analyse pour un projet.
    """
    return {
        "project_id": project_id,
        "status": "completed",
        "last_analysis": None,
        "message": "Statut d'analyse non encore implémenté"
    }


@router.post("/test-dataforseo")
async def test_dataforseo_connection():
    """
    Tester la connexion à DataForSEO avec un mot-clé simple.
    """
    logger.info("Test de connexion DataForSEO")
    
    try:
        dataforseo_service = DataForSEOService()
        
        # Test avec un seul mot-clé
        test_keywords = ["smartphone"]
        
        result = await dataforseo_service.get_serp_results(test_keywords)
        
        # Vérifier la réponse
        if result.get('tasks') and len(result['tasks']) > 0:
            task = result['tasks'][0]
            status_code = task.get('status_code')
            
            return {
                "status": "success",
                "message": "Connexion DataForSEO réussie",
                "api_status_code": status_code,
                "results_count": len(task.get('result', [{}])[0].get('items', [])) if task.get('result') else 0,
                "raw_response": result
            }
        else:
            return {
                "status": "error",
                "message": "Réponse API vide",
                "raw_response": result
            }
            
    except Exception as e:
        logger.error("Erreur test DataForSEO", error=str(e))
        return {
            "status": "error",
            "message": f"Erreur de connexion: {str(e)}"
        } 


@router.post("/test-single-keyword")
async def test_single_keyword():
    """Test avec un seul mot-clé pour debug."""
    logger.info("Test avec un seul mot-clé")
    
    try:
        dataforseo_service = DataForSEOService()
        
        # Test avec "porte de garage" qui fonctionne avec curl
        result = await dataforseo_service.get_serp_results(["porte de garage"])
        
        # Analyser la réponse
        stats = {
            "tasks_count": len(result.get('tasks', [])),
            "successful_tasks": 0,
            "popular_products_found": 0
        }
        
        for task in result.get('tasks', []):
            if task.get('status_code') == 20000:
                stats['successful_tasks'] += 1
                
                for result_item in task.get('result', []):
                    for item in result_item.get('items', []):
                        if item.get('type') == 'popular_products':
                            stats['popular_products_found'] += len(item.get('items', []))
        
        return {
            "message": "Test terminé",
            "stats": stats,
            "raw_data": result
        }
        
    except Exception as e:
        logger.error("Erreur test", error=str(e))
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}") 