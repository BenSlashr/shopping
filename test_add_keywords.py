#!/usr/bin/env python3
"""Script pour ajouter des mots-clés de test dans la base de données."""

import asyncio
import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.append(str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select
from app.models.project import Project
from app.models.keyword import Keyword
from app.database import Base

# URL de la base de données
DATABASE_URL = "sqlite+aiosqlite:///./shopping_monitor.db"

async def add_test_keywords():
    """Ajouter des mots-clés de test pour le projet E-commerce Principal"""
    
    # Créer le moteur et la session
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as session:
        # Chercher le projet "E-commerce Principal"
        project_query = select(Project).where(Project.name == "E-commerce Principal")
        project_result = await session.execute(project_query)
        project = project_result.scalar_one_or_none()
        
        if not project:
            print("❌ Projet 'E-commerce Principal' non trouvé")
            print("Créons d'abord le projet...")
            
            # Créer le projet
            project = Project(
                name="E-commerce Principal",
                description="Monitoring du site e-commerce principal avec focus sur l'électronique",
                is_active=True
            )
            session.add(project)
            await session.commit()
            await session.refresh(project)
            print(f"✅ Projet créé avec l'ID: {project.id}")
        
        print(f"📊 Projet trouvé: {project.name} (ID: {project.id})")
        
        # Vérifier s'il y a déjà des mots-clés
        existing_keywords_query = select(Keyword).where(Keyword.project_id == project.id)
        existing_result = await session.execute(existing_keywords_query)
        existing_keywords = existing_result.scalars().all()
        
        if existing_keywords:
            print(f"🔍 {len(existing_keywords)} mots-clés existants trouvés:")
            for kw in existing_keywords:
                status = "✅ Actif" if kw.is_active else "❌ Inactif"
                print(f"  - {kw.keyword} ({kw.search_volume:,} vol.) {status}")
            return
        
        # Ajouter des mots-clés de test
        test_keywords = [
            {
                "keyword": "smartphone pas cher",
                "location": "France",
                "language": "fr",
                "search_volume": 12000,
                "is_active": True
            },
            {
                "keyword": "iPhone 15 Pro",
                "location": "France", 
                "language": "fr",
                "search_volume": 8500,
                "is_active": True
            },
            {
                "keyword": "casque bluetooth",
                "location": "France",
                "language": "fr", 
                "search_volume": 15000,
                "is_active": True
            },
            {
                "keyword": "tablette Samsung",
                "location": "France",
                "language": "fr",
                "search_volume": 6200,
                "is_active": True
            },
            {
                "keyword": "écouteurs sans fil",
                "location": "France",
                "language": "fr",
                "search_volume": 9800,
                "is_active": False
            },
            {
                "keyword": "ordinateur portable gaming",
                "location": "France",
                "language": "fr",
                "search_volume": 4500,
                "is_active": True
            },
            {
                "keyword": "montre connectée Apple",
                "location": "France",
                "language": "fr",
                "search_volume": 7300,
                "is_active": True
            },
            {
                "keyword": "chargeur iPhone",
                "location": "France",
                "language": "fr",
                "search_volume": 11200,
                "is_active": True
            }
        ]
        
        print(f"➕ Ajout de {len(test_keywords)} mots-clés de test...")
        
        for kw_data in test_keywords:
            keyword = Keyword(
                project_id=project.id,
                keyword=kw_data["keyword"],
                location=kw_data["location"],
                language=kw_data["language"],
                search_volume=kw_data["search_volume"],
                is_active=kw_data["is_active"]
            )
            session.add(keyword)
            status = "✅ Actif" if kw_data["is_active"] else "❌ Inactif"
            print(f"  + {kw_data['keyword']} ({kw_data['search_volume']:,} vol.) {status}")
        
        await session.commit()
        print("✅ Mots-clés ajoutés avec succès!")
        
        # Vérification finale
        final_query = select(Keyword).where(Keyword.project_id == project.id)
        final_result = await session.execute(final_query)
        final_keywords = final_result.scalars().all()
        
        active_count = sum(1 for kw in final_keywords if kw.is_active)
        total_volume = sum(kw.search_volume for kw in final_keywords)
        
        print(f"\n📈 Résumé:")
        print(f"  - Total mots-clés: {len(final_keywords)}")
        print(f"  - Actifs: {active_count}")
        print(f"  - Volume total: {total_volume:,}")
        print(f"  - Volume moyen: {total_volume // len(final_keywords):,}")

if __name__ == "__main__":
    asyncio.run(add_test_keywords()) 