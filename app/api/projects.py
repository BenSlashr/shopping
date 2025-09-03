"""Endpoints API pour les projets."""

from typing import List, Optional
from uuid import UUID
import structlog
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.models import Project, Competitor, Keyword
from app.schemas import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
    ProjectDashboard
)
from app.core.exceptions import NotFoundError, ConflictError

logger = structlog.get_logger()
router = APIRouter()


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Crée un nouveau projet.
    
    Args:
        project_data: Données du projet à créer
    """
    logger.info("Création d'un nouveau projet", name=project_data.name)
    
    try:
        # Vérifier l'unicité du nom (optionnel)
        existing_stmt = select(Project).where(Project.name == project_data.name)
        existing_result = await session.execute(existing_stmt)
        existing_project = existing_result.scalar_one_or_none()
        
        if existing_project:
            raise ConflictError(
                f"Un projet avec le nom '{project_data.name}' existe déjà",
                details={"name": project_data.name}
            )
        
        # Créer le nouveau projet
        project = Project(
            name=project_data.name,
            description=project_data.description,
            is_active=project_data.is_active
        )
        
        session.add(project)
        await session.commit()
        await session.refresh(project)
        
        logger.info(
            "Projet créé avec succès",
            project_id=str(project.id),
            name=project.name
        )
        
        return ProjectResponse.model_validate(project)
        
    except ConflictError:
        await session.rollback()
        raise
    except Exception as e:
        await session.rollback()
        logger.error("Erreur lors de la création du projet", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la création du projet"
        )


@router.get("/", response_model=ProjectListResponse)
async def list_projects(
    page: int = Query(1, ge=1, description="Numéro de page"),
    per_page: int = Query(20, ge=1, le=100, description="Éléments par page"),
    is_active: Optional[bool] = Query(None, description="Filtrer par statut actif"),
    search: Optional[str] = Query(None, description="Rechercher dans le nom ou description"),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Liste les projets avec pagination et filtres.
    
    Args:
        page: Numéro de page
        per_page: Nombre d'éléments par page
        is_active: Filtrer par statut actif
        search: Terme de recherche
    """
    try:
        # Construire la requête de base
        stmt = select(Project)
        
        # Appliquer les filtres
        if is_active is not None:
            stmt = stmt.where(Project.is_active == is_active)
        
        if search:
            search_term = f"%{search}%"
            stmt = stmt.where(
                (Project.name.ilike(search_term)) |
                (Project.description.ilike(search_term))
            )
        
        # Compter le total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_result = await session.execute(count_stmt)
        total = count_result.scalar()
        
        # Appliquer la pagination
        offset = (page - 1) * per_page
        stmt = stmt.order_by(Project.created_at.desc()).offset(offset).limit(per_page)
        
        # Exécuter la requête
        result = await session.execute(stmt)
        projects = result.scalars().all()
        
        # Calculer les métadonnées de pagination
        has_next = (offset + per_page) < total
        has_prev = page > 1
        
        logger.info(
            "Projets récupérés",
            total=total,
            page=page,
            per_page=per_page,
            returned=len(projects)
        )
        
        return ProjectListResponse(
            projects=[ProjectResponse.model_validate(p) for p in projects],
            total=total,
            page=page,
            per_page=per_page,
            has_next=has_next,
            has_prev=has_prev
        )
        
    except Exception as e:
        logger.error("Erreur lors de la récupération des projets", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des projets"
        )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Récupère un projet par son ID.
    
    Args:
        project_id: ID du projet
    """
    try:
        stmt = select(Project).where(Project.id == project_id)
        result = await session.execute(stmt)
        project = result.scalar_one_or_none()
        
        if not project:
            raise NotFoundError("Project", str(project_id))
        
        logger.debug("Projet récupéré", project_id=str(project_id))
        
        return ProjectResponse.model_validate(project)
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(
            "Erreur lors de la récupération du projet",
            project_id=str(project_id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération du projet"
        )


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    project_data: ProjectUpdate,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Met à jour un projet.
    
    Args:
        project_id: ID du projet
        project_data: Données de mise à jour
    """
    logger.info("Mise à jour du projet", project_id=str(project_id))
    
    try:
        # Récupérer le projet
        stmt = select(Project).where(Project.id == project_id)
        result = await session.execute(stmt)
        project = result.scalar_one_or_none()
        
        if not project:
            raise NotFoundError("Project", str(project_id))
        
        # Vérifier l'unicité du nom si modifié
        if project_data.name and project_data.name != project.name:
            existing_stmt = select(Project).where(
                (Project.name == project_data.name) & 
                (Project.id != project_id)
            )
            existing_result = await session.execute(existing_stmt)
            existing_project = existing_result.scalar_one_or_none()
            
            if existing_project:
                raise ConflictError(
                    f"Un projet avec le nom '{project_data.name}' existe déjà",
                    details={"name": project_data.name}
                )
        
        # Mettre à jour les champs modifiés
        update_data = project_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(project, field, value)
        
        await session.commit()
        await session.refresh(project)
        
        logger.info(
            "Projet mis à jour avec succès",
            project_id=str(project_id),
            updated_fields=list(update_data.keys())
        )
        
        return ProjectResponse.model_validate(project)
        
    except (NotFoundError, ConflictError):
        await session.rollback()
        raise
    except Exception as e:
        await session.rollback()
        logger.error(
            "Erreur lors de la mise à jour du projet",
            project_id=str(project_id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la mise à jour du projet"
        )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Supprime un projet et toutes ses données associées.
    
    Args:
        project_id: ID du projet à supprimer
    """
    logger.info("Suppression du projet", project_id=str(project_id))
    
    try:
        # Récupérer le projet
        stmt = select(Project).where(Project.id == project_id)
        result = await session.execute(stmt)
        project = result.scalar_one_or_none()
        
        if not project:
            raise NotFoundError("Project", str(project_id))
        
        # Supprimer le projet (cascade supprimera les données associées)
        await session.delete(project)
        await session.commit()
        
        logger.info(
            "Projet supprimé avec succès",
            project_id=str(project_id),
            name=project.name
        )
        
    except NotFoundError:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(
            "Erreur lors de la suppression du projet",
            project_id=str(project_id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la suppression du projet"
        )


@router.get("/{project_id}/dashboard", response_model=ProjectDashboard)
async def get_project_dashboard(
    project_id: UUID,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Récupère le dashboard d'un projet avec métriques.
    
    Args:
        project_id: ID du projet
    """
    try:
        from sqlalchemy import func
        from app.models import SerpResult
        
        # Récupérer le projet
        project_stmt = select(Project).where(Project.id == project_id)
        project_result = await session.execute(project_stmt)
        project = project_result.scalar_one_or_none()
        
        if not project:
            raise NotFoundError("Project", str(project_id))
        
        # Compter les concurrents
        competitors_stmt = select(func.count(Competitor.id)).where(
            Competitor.project_id == project_id
        )
        competitors_result = await session.execute(competitors_stmt)
        total_competitors = competitors_result.scalar() or 0
        
        # Compter les mots-clés
        keywords_stmt = select(func.count(Keyword.id)).where(
            Keyword.project_id == project_id
        )
        keywords_result = await session.execute(keywords_stmt)
        total_keywords = keywords_result.scalar() or 0
        
        active_keywords_stmt = select(func.count(Keyword.id)).where(
            (Keyword.project_id == project_id) & 
            (Keyword.is_active == True)
        )
        active_keywords_result = await session.execute(active_keywords_stmt)
        active_keywords = active_keywords_result.scalar() or 0
        
        # Métriques SERP
        serp_count_stmt = select(func.count(SerpResult.id)).where(
            SerpResult.project_id == project_id
        )
        serp_count_result = await session.execute(serp_count_stmt)
        total_serp_results = serp_count_result.scalar() or 0
        
        # Position moyenne (approximation simple)
        avg_position_stmt = select(func.avg(SerpResult.position)).where(
            (SerpResult.project_id == project_id) & 
            (SerpResult.position.is_not(None))
        )
        avg_position_result = await session.execute(avg_position_stmt)
        average_position = avg_position_result.scalar()
        
        # Dernière date de scraping
        last_scrape_stmt = select(func.max(SerpResult.scraped_at)).where(
            SerpResult.project_id == project_id
        )
        last_scrape_result = await session.execute(last_scrape_stmt)
        last_scrape_date = last_scrape_result.scalar()
        
        dashboard = ProjectDashboard(
            project=ProjectResponse.model_validate(project),
            total_keywords=total_keywords,
            active_keywords=active_keywords,
            total_competitors=total_competitors,
            average_position=float(average_position) if average_position else None,
            visibility_score=None,  # À calculer plus tard
            share_of_voice=None,    # À calculer plus tard
            last_scrape_date=last_scrape_date,
            total_serp_results=total_serp_results,
            position_change=None,   # À calculer plus tard
            visibility_change=None, # À calculer plus tard
            share_of_voice_change=None  # À calculer plus tard
        )
        
        logger.debug(
            "Dashboard récupéré",
            project_id=str(project_id),
            total_keywords=total_keywords,
            total_competitors=total_competitors
        )
        
        return dashboard
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(
            "Erreur lors de la récupération du dashboard",
            project_id=str(project_id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération du dashboard"
        )


@router.get("/{project_id}/keywords")
async def get_project_keywords(
    project_id: str,
    session: AsyncSession = Depends(get_async_session)
):
    """Récupérer tous les mots-clés d'un projet"""
    logger.info("Récupération des mots-clés du projet", project_id=project_id)
    
    # Vérifier que le projet existe
    project_query = select(Project).where(Project.id == project_id)
    project_result = await session.execute(project_query)
    project = project_result.scalar_one_or_none()
    
    if not project:
        logger.error("Projet non trouvé", project_id=project_id)
        raise HTTPException(status_code=404, detail=f"Projet {project_id} non trouvé")
    
    # Récupérer les mots-clés du projet
    keywords_query = select(Keyword).where(Keyword.project_id == project_id)
    keywords_result = await session.execute(keywords_query)
    keywords = keywords_result.scalars().all()
    
    logger.info("Mots-clés récupérés", project_id=project_id, count=len(keywords))
    
    return {
        "project_id": project_id,
        "keywords": [
            {
                "id": keyword.id,
                "keyword": keyword.keyword,
                "location": keyword.location,
                "language": keyword.language,
                "search_volume": keyword.search_volume,
                "is_active": keyword.is_active,
                "created_at": keyword.created_at.isoformat()
            }
            for keyword in keywords
        ]
    }


@router.post("/{project_id}/keywords")
async def add_project_keywords(
    project_id: str,
    keywords_data: dict,
    session: AsyncSession = Depends(get_async_session)
):
    """Ajouter des mots-clés en bulk à un projet"""
    logger.info("Ajout de mots-clés au projet", project_id=project_id)
    
    # Vérifier que le projet existe
    project_query = select(Project).where(Project.id == project_id)
    project_result = await session.execute(project_query)
    project = project_result.scalar_one_or_none()
    
    if not project:
        logger.error("Projet non trouvé", project_id=project_id)
        raise HTTPException(status_code=404, detail=f"Projet {project_id} non trouvé")
    
    try:
        # Récupérer les données des mots-clés
        keywords_list = keywords_data.get("keywords", [])
        if not keywords_list:
            raise HTTPException(status_code=400, detail="Aucun mot-clé fourni")
        
        # Créer les nouveaux mots-clés
        new_keywords = []
        for kw_data in keywords_list:
            keyword = Keyword(
                project_id=project_id,
                keyword=kw_data.get("keyword", "").strip(),
                location=kw_data.get("location", "France"),
                language=kw_data.get("language", "fr"),
                search_volume=kw_data.get("search_volume", 0),
                is_active=kw_data.get("is_active", True)
            )
            
            if not keyword.keyword:
                continue  # Ignorer les mots-clés vides
                
            new_keywords.append(keyword)
            session.add(keyword)
        
        if not new_keywords:
            raise HTTPException(status_code=400, detail="Aucun mot-clé valide fourni")
        
        # Sauvegarder en base
        await session.commit()
        
        # Rafraîchir les objets pour avoir les IDs
        for keyword in new_keywords:
            await session.refresh(keyword)
        
        logger.info("Mots-clés ajoutés avec succès", project_id=project_id, count=len(new_keywords))
        
        return {
            "project_id": project_id,
            "added_count": len(new_keywords),
            "keywords": [
                {
                    "id": keyword.id,
                    "keyword": keyword.keyword,
                    "location": keyword.location,
                    "language": keyword.language,
                    "search_volume": keyword.search_volume,
                    "is_active": keyword.is_active,
                    "created_at": keyword.created_at.isoformat()
                }
                for keyword in new_keywords
            ]
        }
        
    except HTTPException:
        await session.rollback()
        raise
    except Exception as e:
        await session.rollback()
        logger.error("Erreur lors de l'ajout des mots-clés", project_id=project_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de l'ajout des mots-clés"
        ) 

# Endpoints pour les concurrents d'un projet

@router.get("/{project_id}/competitors")
async def get_project_competitors(
    project_id: str,
    session: AsyncSession = Depends(get_async_session)
):
    """Récupérer tous les concurrents d'un projet"""
    logger.info("Récupération des concurrents du projet", project_id=project_id)

    # Vérifier que le projet existe
    project_query = select(Project).where(Project.id == project_id)
    project_result = await session.execute(project_query)
    project = project_result.scalar_one_or_none()

    if not project:
        logger.error("Projet non trouvé", project_id=project_id)
        raise HTTPException(status_code=404, detail=f"Projet {project_id} non trouvé")

    # Récupérer les concurrents du projet
    competitors_query = select(Competitor).where(Competitor.project_id == project_id)
    competitors_result = await session.execute(competitors_query)
    competitors = competitors_result.scalars().all()

    logger.info("Concurrents récupérés", project_id=project_id, count=len(competitors))

    return {
        "project_id": project_id,
        "competitors": [
            {
                "id": competitor.id,
                "name": competitor.name,
                "domain": competitor.domain,
                "brand_name": competitor.brand_name,
                "is_main_brand": competitor.is_main_brand,
                "created_at": competitor.created_at.isoformat()
            }
            for competitor in competitors
        ],
        "total": len(competitors)
    }


@router.post("/{project_id}/competitors")
async def add_project_competitor(
    project_id: str,
    competitor_data: dict,
    session: AsyncSession = Depends(get_async_session)
):
    """Ajouter un concurrent à un projet"""
    logger.info("Ajout d'un concurrent au projet", project_id=project_id)

    # Vérifier que le projet existe
    project_query = select(Project).where(Project.id == project_id)
    project_result = await session.execute(project_query)
    project = project_result.scalar_one_or_none()

    if not project:
        logger.error("Projet non trouvé", project_id=project_id)
        raise HTTPException(status_code=404, detail=f"Projet {project_id} non trouvé")

    try:
        # Vérifier si le concurrent existe déjà
        existing_query = select(Competitor).where(
            Competitor.project_id == project_id,
            Competitor.domain == competitor_data.get("domain", "").strip()
        )
        existing_result = await session.execute(existing_query)
        existing_competitor = existing_result.scalar_one_or_none()

        if existing_competitor:
            raise HTTPException(
                status_code=400, 
                detail=f"Un concurrent avec le domaine '{competitor_data.get('domain')}' existe déjà"
            )

        # Créer le nouveau concurrent
        competitor = Competitor(
            project_id=project_id,
            name=competitor_data.get("name", "").strip(),
            domain=competitor_data.get("domain", "").strip(),
            brand_name=competitor_data.get("brand_name", "").strip(),
            is_main_brand=competitor_data.get("is_main_brand", False)
        )

        if not competitor.name or not competitor.domain:
            raise HTTPException(status_code=400, detail="Le nom et le domaine sont obligatoires")

        session.add(competitor)
        await session.commit()
        await session.refresh(competitor)

        logger.info("Concurrent ajouté avec succès", project_id=project_id, competitor_id=competitor.id)

        return {
            "id": competitor.id,
            "name": competitor.name,
            "domain": competitor.domain,
            "brand_name": competitor.brand_name,
            "is_main_brand": competitor.is_main_brand,
            "created_at": competitor.created_at.isoformat()
        }

    except HTTPException:
        await session.rollback()
        raise
    except Exception as e:
        await session.rollback()
        logger.error("Erreur lors de l'ajout du concurrent", project_id=project_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de l'ajout du concurrent"
        )


@router.delete("/{project_id}/competitors/{competitor_id}")
async def delete_project_competitor(
    project_id: str,
    competitor_id: str,
    session: AsyncSession = Depends(get_async_session)
):
    """Supprimer un concurrent d'un projet"""
    logger.info("Suppression d'un concurrent", project_id=project_id, competitor_id=competitor_id)

    # Vérifier que le projet existe
    project_query = select(Project).where(Project.id == project_id)
    project_result = await session.execute(project_query)
    project = project_result.scalar_one_or_none()

    if not project:
        logger.error("Projet non trouvé", project_id=project_id)
        raise HTTPException(status_code=404, detail=f"Projet {project_id} non trouvé")

    # Vérifier que le concurrent existe
    competitor_query = select(Competitor).where(
        Competitor.id == competitor_id,
        Competitor.project_id == project_id
    )
    competitor_result = await session.execute(competitor_query)
    competitor = competitor_result.scalar_one_or_none()

    if not competitor:
        logger.error("Concurrent non trouvé", competitor_id=competitor_id)
        raise HTTPException(status_code=404, detail=f"Concurrent {competitor_id} non trouvé")

    try:
        await session.delete(competitor)
        await session.commit()

        logger.info("Concurrent supprimé avec succès", project_id=project_id, competitor_id=competitor_id)

        return {"message": "Concurrent supprimé avec succès"}

    except Exception as e:
        await session.rollback()
        logger.error("Erreur lors de la suppression du concurrent", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la suppression du concurrent"
        ) 