import os
from typing import Dict, Any
from pydantic import BaseSettings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings(BaseSettings):
    # Application settings
    app_name: str = "Smart Semantic Pricing Engine"
    app_version: str = "1.0.0"
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Database settings
    database_url: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/donizo")
    database_pool_size: int = int(os.getenv("DATABASE_POOL_SIZE", "10"))
    database_max_overflow: int = int(os.getenv("DATABASE_MAX_OVERFLOW", "20"))
    
    # Vector database settings
    vector_dimensions: int = 768  # BGE-large-en-v1.5 dimensions
    similarity_threshold: float = 0.7
    max_search_results: int = 20
    
    # Embedding model settings
    embedding_model: str = "BAAI/bge-large-en-v1.5"
    embedding_device: str = os.getenv("EMBEDDING_DEVICE", "cpu")  # cpu or cuda
    embedding_batch_size: int = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))
    
    # Redis settings (for caching)
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    redis_ttl: int = int(os.getenv("REDIS_TTL", "3600"))  # 1 hour
    
    # Pricing configuration
    base_margin: float = 0.25  # 25% base margin
    vat_renovation: float = 0.10  # 10% VAT for renovation
    vat_new_build: float = 0.20  # 20% VAT for new build
    
    # Regional pricing multipliers
    regional_multipliers: Dict[str, float] = {
        "Île-de-France": 1.15,
        "Provence-Alpes-Côte d'Azur": 1.10,
        "Auvergne-Rhône-Alpes": 1.05,
        "Occitanie": 1.00,
        "Nouvelle-Aquitaine": 0.95,
        "Hauts-de-France": 0.90,
        "Grand Est": 0.95,
        "Bourgogne-Franche-Comté": 0.90,
        "Centre-Val de Loire": 0.95,
        "Normandie": 0.90,
        "Bretagne": 0.95,
        "Pays de la Loire": 0.95,
        "Corse": 1.20,
    }
    
    # Quality multipliers
    quality_multipliers: Dict[str, float] = {
        "premium": 1.1,
        "standard": 1.0,
        "economy": 0.9,
    }
    
    # Confidence scoring weights
    confidence_weights: Dict[str, float] = {
        "semantic_similarity": 0.40,
        "regional_match": 0.25,
        "price_range": 0.20,
        "vendor_reliability": 0.15,
    }
    
    # API rate limiting
    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "100"))
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # External APIs
    supplier_api_timeout: int = int(os.getenv("SUPPLIER_API_TIMEOUT", "10"))
    supplier_api_retries: int = int(os.getenv("SUPPLIER_API_RETRIES", "3"))
    
    # Performance settings
    max_concurrent_requests: int = int(os.getenv("MAX_CONCURRENT_REQUESTS", "100"))
    request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    
    # Feedback learning
    feedback_impact_threshold: float = 0.1
    feedback_retention_days: int = int(os.getenv("FEEDBACK_RETENTION_DAYS", "365"))
    
    # Task estimation defaults
    default_labor_rates: Dict[str, float] = {
        "tiling": 45.0,  # €/hour
        "painting": 35.0,
        "plumbing": 55.0,
        "electrical": 50.0,
        "carpentry": 40.0,
        "general": 40.0,
    }
    
    # Material categories for task identification
    material_categories: Dict[str, list] = {
        "tiles": ["tile", "carrelage", "ceramic", "porcelain", "mosaic"],
        "adhesives": ["glue", "adhesive", "mortar", "colle", "ciment"],
        "paints": ["paint", "peinture", "primer", "undercoat"],
        "plumbing": ["pipe", "fitting", "valve", "tuyau", "robinet"],
        "electrical": ["wire", "cable", "switch", "outlet", "fil", "prise"],
        "wood": ["wood", "timber", "board", "bois", "planche"],
    }
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()

# Helper functions
def get_database_url() -> str:
    """Get database URL with proper formatting"""
    return settings.database_url

def get_redis_url() -> str:
    """Get Redis URL for caching"""
    return settings.redis_url

def get_embedding_config() -> Dict[str, Any]:
    """Get embedding model configuration"""
    return {
        "model_name": settings.embedding_model,
        "device": settings.embedding_device,
        "batch_size": settings.embedding_batch_size,
        "dimensions": settings.vector_dimensions,
    }

def get_pricing_config() -> Dict[str, Any]:
    """Get pricing configuration"""
    return {
        "base_margin": settings.base_margin,
        "vat_renovation": settings.vat_renovation,
        "vat_new_build": settings.vat_new_build,
        "regional_multipliers": settings.regional_multipliers,
        "quality_multipliers": settings.quality_multipliers,
    }

def get_confidence_weights() -> Dict[str, float]:
    """Get confidence scoring weights"""
    return settings.confidence_weights.copy()

def get_labor_rates() -> Dict[str, float]:
    """Get default labor rates by task type"""
    return settings.default_labor_rates.copy()

def get_material_categories() -> Dict[str, list]:
    """Get material categories for task identification"""
    return settings.material_categories.copy()
