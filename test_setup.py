#!/usr/bin/env python3
"""Script de test pour vérifier la configuration de Shopping Monitor."""

import asyncio
import sys
from pathlib import Path

# Ajouter le répertoire racine au path
sys.path.append(str(Path(__file__).parent))

try:
    from app.config import settings
    from app.database import init_db, close_db, AsyncSessionLocal
    from app.models import Project, Competitor, Keyword
    print("✅ Imports réussis")
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    sys.exit(1)


async def test_database_connection():
    """Test de connexion à la base de données."""
    try:
        print("\n🔍 Test de connexion à la base de données...")
        
        # Test de création de session
        async with AsyncSessionLocal() as session:
            print("✅ Session créée avec succès")
            
        print("✅ Connexion à la base de données réussie")
        return True
        
    except Exception as e:
        print(f"❌ Erreur de connexion à la base de données: {e}")
        return False


def test_configuration():
    """Test de configuration."""
    print("\n🔍 Test de configuration...")
    
    # Vérifier les settings critiques
    checks = [
        ("DATABASE_URL", settings.database_url),
        ("REDIS_URL", settings.redis_url),
        ("SECRET_KEY", settings.secret_key),
        ("ENVIRONMENT", settings.environment),
    ]
    
    all_good = True
    for name, value in checks:
        if value and value != "your-super-secret-key-change-this-in-production":
            print(f"✅ {name}: configuré")
        else:
            print(f"⚠️  {name}: non configuré ou valeur par défaut")
            if name in ["DATABASE_URL", "SECRET_KEY"]:
                all_good = False
    
    return all_good


def test_models():
    """Test des modèles."""
    print("\n🔍 Test des modèles...")
    
    try:
        # Test de création d'instances
        project = Project(
            name="Test Project",
            description="Projet de test"
        )
        print("✅ Modèle Project créé")
        
        competitor = Competitor(
            name="Test Competitor",
            domain="example.com",
            project_id=project.id
        )
        print("✅ Modèle Competitor créé")
        
        keyword = Keyword(
            keyword="test keyword",
            project_id=project.id
        )
        print("✅ Modèle Keyword créé")
        
        print("✅ Tous les modèles fonctionnent")
        return True
        
    except Exception as e:
        print(f"❌ Erreur avec les modèles: {e}")
        return False


async def main():
    """Fonction principale de test."""
    print("🚀 Test de configuration Shopping Monitor\n")
    
    # Tests
    config_ok = test_configuration()
    models_ok = test_models()
    db_ok = await test_database_connection()
    
    print("\n" + "="*50)
    print("📊 RÉSULTATS DES TESTS")
    print("="*50)
    
    results = [
        ("Configuration", config_ok),
        ("Modèles", models_ok),
        ("Base de données", db_ok),
    ]
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:20} : {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*50)
    if all_passed:
        print("🎉 Tous les tests sont passés ! Shopping Monitor est prêt.")
        print("\nPour démarrer l'application :")
        print("  uvicorn app.main:app --reload")
        print("  ou")
        print("  docker-compose up postgres redis")
    else:
        print("⚠️  Certains tests ont échoué. Vérifiez la configuration.")
        print("\nActions recommandées :")
        if not config_ok:
            print("  - Copiez env.example vers .env et configurez les variables")
        if not db_ok:
            print("  - Démarrez PostgreSQL : docker-compose up postgres")
            print("  - Vérifiez la chaîne de connexion DATABASE_URL")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 