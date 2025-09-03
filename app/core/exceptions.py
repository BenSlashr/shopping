"""Exceptions personnalisées pour Shopping Monitor."""

from typing import Any, Dict, Optional


class ShoppingMonitorException(Exception):
    """Exception de base pour Shopping Monitor."""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_type: str = "ShoppingMonitorError",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_type = error_type
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(ShoppingMonitorException):
    """Erreur de validation des données."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=422,
            error_type="ValidationError",
            details=details
        )


class NotFoundError(ShoppingMonitorException):
    """Erreur ressource non trouvée."""
    
    def __init__(self, resource: str, identifier: str):
        message = f"{resource} avec l'identifiant '{identifier}' non trouvé"
        super().__init__(
            message=message,
            status_code=404,
            error_type="NotFoundError",
            details={"resource": resource, "identifier": identifier}
        )


class ConflictError(ShoppingMonitorException):
    """Erreur de conflit (ressource déjà existante)."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=409,
            error_type="ConflictError",
            details=details
        )


class DatabaseError(ShoppingMonitorException):
    """Erreur de base de données."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=500,
            error_type="DatabaseError",
            details=details
        )


class ExternalAPIError(ShoppingMonitorException):
    """Erreur d'API externe (DataForSEO, etc.)."""
    
    def __init__(
        self,
        service: str,
        message: str,
        status_code: int = 502,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=f"Erreur {service}: {message}",
            status_code=status_code,
            error_type="ExternalAPIError",
            details={**(details or {}), "service": service}
        )


class ScrapingError(ShoppingMonitorException):
    """Erreur de scraping."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=500,
            error_type="ScrapingError",
            details=details
        )


class RateLimitError(ShoppingMonitorException):
    """Erreur de limite de taux."""
    
    def __init__(self, service: str, retry_after: Optional[int] = None):
        message = f"Limite de taux atteinte pour {service}"
        details = {"service": service}
        
        if retry_after:
            message += f". Réessayer dans {retry_after} secondes"
            details["retry_after"] = retry_after
        
        super().__init__(
            message=message,
            status_code=429,
            error_type="RateLimitError",
            details=details
        )


class AuthenticationError(ShoppingMonitorException):
    """Erreur d'authentification."""
    
    def __init__(self, message: str = "Authentification requise"):
        super().__init__(
            message=message,
            status_code=401,
            error_type="AuthenticationError"
        )


class AuthorizationError(ShoppingMonitorException):
    """Erreur d'autorisation."""
    
    def __init__(self, message: str = "Accès non autorisé"):
        super().__init__(
            message=message,
            status_code=403,
            error_type="AuthorizationError"
        )


class ConfigurationError(ShoppingMonitorException):
    """Erreur de configuration."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=500,
            error_type="ConfigurationError",
            details=details
        ) 