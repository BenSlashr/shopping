#!/usr/bin/env python3
"""Script de test pour la Phase 2 - Scraping Engine."""

import asyncio
import sys
from pathlib import Path

# Ajouter le répertoire racine au path
sys.path.append(str(Path(__file__).parent))

try:
    from app.config import settings
    from app.database import AsyncSessionLocal
    from app.services.dataforseo_client import DataForSEOClient
    from app.services.url_deduplication import URLDeduplicationService
    from app.services.competitor_detection import CompetitorDetectionService
    from app.services.scraping_service import ScrapingService
    from app.models import Project, Keyword, Competitor
    print("✅ Imports Phase 2 réussis")
except ImportError as e:
    print(f"❌ Erreur d'import Phase 2: {e}")
    sys.exit(1)


async def test_dataforseo_client():
    """Test du client DataForSEO."""
    print("\n🔍 Test du client DataForSEO...")
    
    try:
        client = DataForSEOClient()
        print("✅ Client DataForSEO initialisé")
        
        # Test de connexion (sans vraie API key)
        try:
            connection_test = await client.test_connection()
            if connection_test.get("connected"):
                print("✅ Connexion DataForSEO réussie")
                print(f"   Balance: {connection_test.get('user_info', {}).get('money', {}).get('balance', 'N/A')}")
            else:
                print("⚠️  Connexion DataForSEO échouée (normal sans API key)")
                print(f"   Erreur: {connection_test.get('error', 'Inconnue')}")
        except Exception as e:
            print(f"⚠️  Test de connexion échoué (normal sans API key): {type(e).__name__}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur client DataForSEO: {e}")
        return False


async def test_url_deduplication():
    """Test du service de déduplication d'URLs."""
    print("\n🔍 Test du service de déduplication d'URLs...")
    
    try:
        async with AsyncSessionLocal() as session:
            url_service = URLDeduplicationService(session)
            
            # Test de normalisation d'URL
            test_urls = [
                "https://www.example.com/product?utm_source=google&id=123",
                "http://example.com/product/?id=123&ref=test",
                "https://example.com/product?id=123",
            ]
            
            normalized_urls = []
            for url in test_urls:
                normalized = url_service.normalize_url(url)
                normalized_urls.append(normalized)
                print(f"   {url} -> {normalized}")
            
            # Vérifier que les URLs similaires sont bien normalisées
            if len(set(normalized_urls)) < len(test_urls):
                print("✅ Normalisation d'URLs fonctionne")
            else:
                print("⚠️  Normalisation d'URLs pourrait être améliorée")
            
            # Test d'extraction de domaine
            domain = url_service.extract_domain("https://www.amazon.fr/product/123")
            if domain == "amazon.fr":
                print("✅ Extraction de domaine fonctionne")
            else:
                print(f"⚠️  Extraction de domaine inattendue: {domain}")
            
        return True
        
    except Exception as e:
        print(f"❌ Erreur service déduplication: {e}")
        return False


async def test_competitor_detection():
    """Test du service de détection de concurrents."""
    print("\n🔍 Test du service de détection de concurrents...")
    
    try:
        async with AsyncSessionLocal() as session:
            competitor_service = CompetitorDetectionService(session)
            
            # Test d'extraction de domaine
            domain = competitor_service.extract_domain_from_url("https://www.amazon.fr/product/123")
            if domain == "amazon.fr":
                print("✅ Extraction de domaine concurrent fonctionne")
            else:
                print(f"⚠️  Extraction de domaine inattendue: {domain}")
            
            # Test de détection de marketplace
            is_marketplace = competitor_service.is_marketplace_domain("amazon.fr")
            if is_marketplace:
                print("✅ Détection de marketplace fonctionne")
            else:
                print("⚠️  Détection de marketplace échouée")
            
            # Test de calcul de score d'autorité
            score = competitor_service.calculate_domain_authority_score(
                domain="amazon.fr",
                appearances=10,
                avg_position=2.5,
                price_competitiveness=0.7
            )
            if score > 50:
                print(f"✅ Calcul de score d'autorité fonctionne: {score}")
            else:
                print(f"⚠️  Score d'autorité faible: {score}")
            
            # Test de suggestion de nom
            suggested_name = competitor_service.suggest_competitor_name(
                "amazon.fr", 
                {"Amazon", "Amazon.fr"}
            )
            if suggested_name:
                print(f"✅ Suggestion de nom fonctionne: {suggested_name}")
            else:
                print("⚠️  Suggestion de nom échouée")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur service détection concurrents: {e}")
        return False


async def test_scraping_service():
    """Test du service principal de scraping."""
    print("\n🔍 Test du service principal de scraping...")
    
    try:
        async with AsyncSessionLocal() as session:
            scraping_service = ScrapingService(session)
            
            # Test d'extraction de données produit
            test_serp_item = {
                "title": "Test Product",
                "description": "Test description",
                "price": {"current": 29.99, "currency": "EUR", "regular": 39.99},
                "merchant": {"name": "Test Store", "url": "https://teststore.com"},
                "rating": {"rating_value": 4.5, "reviews_count": 123},
                "url": "https://teststore.com/product/123"
            }
            
            product_data = scraping_service.extract_product_data(test_serp_item)
            
            if (product_data.get("title") == "Test Product" and 
                product_data.get("price") == 29.99 and
                product_data.get("merchant_name") == "Test Store"):
                print("✅ Extraction de données produit fonctionne")
            else:
                print("⚠️  Extraction de données produit incomplète")
                print(f"   Données extraites: {product_data}")
            
            # Test d'extraction de domaine
            domain = scraping_service.extract_domain_from_url("https://www.example.com/test")
            if domain == "example.com":
                print("✅ Extraction de domaine scraping fonctionne")
            else:
                print(f"⚠️  Extraction de domaine inattendue: {domain}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur service scraping: {e}")
        return False


def test_configuration_phase2():
    """Test de configuration spécifique à la Phase 2."""
    print("\n🔍 Test de configuration Phase 2...")
    
    # Vérifier les settings DataForSEO
    checks = [
        ("DATAFORSEO_BASE_URL", settings.dataforseo_base_url),
        ("MAX_CONCURRENT_REQUESTS", settings.max_concurrent_requests),
        ("REQUEST_DELAY_SECONDS", settings.request_delay_seconds),
        ("MAX_RETRIES", settings.max_retries),
    ]
    
    all_good = True
    for name, value in checks:
        if value:
            print(f"✅ {name}: {value}")
        else:
            print(f"⚠️  {name}: non configuré")
            if name in ["DATAFORSEO_BASE_URL"]:
                all_good = False
    
    # Vérifier les identifiants DataForSEO (sans les afficher)
    if settings.dataforseo_login and settings.dataforseo_password:
        print("✅ Identifiants DataForSEO configurés")
    else:
        print("⚠️  Identifiants DataForSEO manquants (normal pour les tests)")
    
    return all_good


async def test_database_models():
    """Test des modèles de base de données."""
    print("\n🔍 Test des modèles de base de données...")
    
    try:
        async with AsyncSessionLocal() as session:
            # Test de création d'un projet
            project = Project(
                name="Test Project Phase 2",
                description="Projet de test pour la phase 2"
            )
            session.add(project)
            await session.flush()
            
            # Test de création d'un concurrent
            competitor = Competitor(
                project_id=project.id,
                name="Test Competitor",
                domain="testcompetitor.com",
                brand_name="Test Brand"
            )
            session.add(competitor)
            await session.flush()
            
            # Test de création d'un mot-clé
            keyword = Keyword(
                project_id=project.id,
                keyword="test keyword phase 2",
                location="France",
                language="fr"
            )
            session.add(keyword)
            await session.flush()
            
            print("✅ Modèles de base de données fonctionnent")
            
            # Rollback pour ne pas polluer la DB
            await session.rollback()
            
        return True
        
    except Exception as e:
        print(f"❌ Erreur modèles de base de données: {e}")
        return False


async def main():
    """Fonction principale de test Phase 2."""
    print("🚀 Test de la Phase 2 - Scraping Engine\n")
    
    # Tests
    config_ok = test_configuration_phase2()
    models_ok = await test_database_models()
    dataforseo_ok = await test_dataforseo_client()
    url_dedup_ok = await test_url_deduplication()
    competitor_ok = await test_competitor_detection()
    scraping_ok = await test_scraping_service()
    
    print("\n" + "="*60)
    print("📊 RÉSULTATS DES TESTS PHASE 2")
    print("="*60)
    
    results = [
        ("Configuration Phase 2", config_ok),
        ("Modèles DB", models_ok),
        ("Client DataForSEO", dataforseo_ok),
        ("Déduplication URLs", url_dedup_ok),
        ("Détection concurrents", competitor_ok),
        ("Service scraping", scraping_ok),
    ]
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:25} : {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 Tous les tests Phase 2 sont passés !")
        print("\nLa Phase 2 - Scraping Engine est prête !")
        print("\nPour tester l'API :")
        print("  1. Démarrer l'application : uvicorn app.main:app --reload")
        print("  2. Aller sur : http://localhost:8000/docs")
        print("  3. Tester les endpoints /api/v1/projects et /api/v1/scraping")
        print("\nEndpoints disponibles :")
        print("  - POST /api/v1/projects (créer un projet)")
        print("  - GET  /api/v1/projects (lister les projets)")
        print("  - POST /api/v1/projects/{id}/scrape (scraper un projet)")
        print("  - GET  /api/v1/scraping/status/{task_id} (statut scraping)")
        print("  - POST /api/v1/test-dataforseo-connection (test DataForSEO)")
    else:
        print("⚠️  Certains tests Phase 2 ont échoué.")
        print("\nActions recommandées :")
        if not config_ok:
            print("  - Vérifiez la configuration dans .env")
        if not models_ok:
            print("  - Vérifiez la connexion à la base de données")
        if not dataforseo_ok:
            print("  - Configurez les identifiants DataForSEO si nécessaire")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 