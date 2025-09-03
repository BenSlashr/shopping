"""Version simplifiée de l'application FastAPI pour les tests sans base de données."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog
import time

from app.config import settings
from app.core.exceptions import ShoppingMonitorException

# Configuration du logger
logger = structlog.get_logger()

# Création de l'application FastAPI
app = FastAPI(
    title="Shopping Monitor API - Test Mode",
    description="API de monitoring Google Shopping (mode test sans base de données)",
    version="1.0.0-test",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Routes de base
@app.get("/")
async def root():
    """Endpoint racine."""
    return {
        "message": "Shopping Monitor API - Test Mode",
        "version": "1.0.0-test",
        "environment": settings.environment,
        "docs": "/docs",
        "status": "running_without_database"
    }

@app.get("/health")
async def health_check():
    """Endpoint de vérification de santé."""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "timestamp": time.time(),
        "database": "disabled_for_testing"
    }

# Test des services sans base de données
@app.get("/test/dataforseo")
async def test_dataforseo():
    """Test du client DataForSEO."""
    try:
        from app.services.dataforseo_client import DataForSEOClient
        
        client = DataForSEOClient()
        connection_test = await client.test_connection()
        
        return {
            "message": "Test client DataForSEO",
            "client_initialized": True,
            "connection_test": connection_test
        }
    except Exception as e:
        return {
            "message": "Test client DataForSEO",
            "client_initialized": False,
            "error": str(e),
            "error_type": type(e).__name__
        }

@app.get("/test/url-deduplication")
async def test_url_deduplication():
    """Test du service de déduplication d'URLs."""
    try:
        from app.services.url_deduplication import URLDeduplicationService
        
        # Créer une session mock
        class MockSession:
            pass
        
        service = URLDeduplicationService(MockSession())
        
        # Test de normalisation
        test_urls = [
            "https://www.example.com/product?utm_source=google&id=123",
            "http://example.com/product/?id=123&ref=test",
            "https://example.com/product?id=123",
        ]
        
        results = []
        for url in test_urls:
            normalized = service.normalize_url(url)
            domain = service.extract_domain(url)
            results.append({
                "original": url,
                "normalized": normalized,
                "domain": domain
            })
        
        return {
            "message": "Test déduplication URLs",
            "service_initialized": True,
            "test_results": results
        }
    except Exception as e:
        return {
            "message": "Test déduplication URLs",
            "service_initialized": False,
            "error": str(e),
            "error_type": type(e).__name__
        }

@app.get("/test/competitor-detection")
async def test_competitor_detection():
    """Test du service de détection de concurrents."""
    try:
        from app.services.competitor_detection import CompetitorDetectionService
        
        # Créer une session mock
        class MockSession:
            pass
        
        service = CompetitorDetectionService(MockSession())
        
        # Tests
        test_results = {
            "domain_extraction": service.extract_domain_from_url("https://www.amazon.fr/product/123"),
            "domain_normalization": service.normalize_domain("www.shop.example.com"),
            "marketplace_detection": service.is_marketplace_domain("amazon.fr"),
            "authority_score": service.calculate_domain_authority_score(
                domain="amazon.fr",
                appearances=10,
                avg_position=2.5,
                price_competitiveness=0.7
            ),
            "name_suggestion": service.suggest_competitor_name("amazon.fr", {"Amazon", "Amazon.fr"})
        }
        
        return {
            "message": "Test détection concurrents",
            "service_initialized": True,
            "test_results": test_results
        }
    except Exception as e:
        return {
            "message": "Test détection concurrents",
            "service_initialized": False,
            "error": str(e),
            "error_type": type(e).__name__
        }

@app.get("/test/scraping-service")
async def test_scraping_service():
    """Test du service de scraping."""
    try:
        from app.services.scraping_service import ScrapingService
        
        # Créer une session mock
        class MockSession:
            pass
        
        service = ScrapingService(MockSession())
        
        # Test d'extraction de données produit
        test_serp_item = {
            "title": "Test Product",
            "description": "Test description",
            "price": {"current": 29.99, "currency": "EUR", "regular": 39.99},
            "merchant": {"name": "Test Store", "url": "https://teststore.com"},
            "rating": {"rating_value": 4.5, "reviews_count": 123},
            "url": "https://teststore.com/product/123"
        }
        
        product_data = service.extract_product_data(test_serp_item)
        domain = service.extract_domain_from_url("https://www.example.com/test")
        
        return {
            "message": "Test service scraping",
            "service_initialized": True,
            "test_results": {
                "product_data_extraction": product_data,
                "domain_extraction": domain
            }
        }
    except Exception as e:
        return {
            "message": "Test service scraping",
            "service_initialized": False,
            "error": str(e),
            "error_type": type(e).__name__
        }

@app.get("/test/all")
async def test_all_services():
    """Test de tous les services."""
    results = {}
    
    # Test DataForSEO
    dataforseo_result = await test_dataforseo()
    results["dataforseo"] = dataforseo_result["client_initialized"]
    
    # Test URL Deduplication
    url_result = await test_url_deduplication()
    results["url_deduplication"] = url_result["service_initialized"]
    
    # Test Competitor Detection
    competitor_result = await test_competitor_detection()
    results["competitor_detection"] = competitor_result["service_initialized"]
    
    # Test Scraping Service
    scraping_result = await test_scraping_service()
    results["scraping_service"] = scraping_result["service_initialized"]
    
    all_passed = all(results.values())
    
    return {
        "message": "Test de tous les services Phase 2",
        "all_tests_passed": all_passed,
        "individual_results": results,
        "summary": f"{sum(results.values())}/{len(results)} services fonctionnent"
    }

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main_test:app",
        host="0.0.0.0",
        port=8001,  # Port différent pour éviter les conflits
        reload=True
    ) 