"""
Configuration settings for the Alert Monitoring System
"""
from pydantic_settings import BaseSettings
from typing import Optional, List
import os
from pathlib import Path

class Settings(BaseSettings):
    """Application settings"""
    
    # App settings
    APP_NAME: str = "Alert Monitoring System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # API settings
    API_V1_PREFIX: str = "/api/v1"
    
    # Database settings
    CHROMADB_HOST: str = "localhost"
    CHROMADB_PORT: int = 8000
    CHROMADB_COLLECTION: str = "alerts"
    CHROMADB_PERSIST_DIRECTORY: str = "./data/chromadb"
    
    # Ollama settings
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"
    OLLAMA_TIMEOUT: int = 300
    
    # Alert processing settings
    SIMILARITY_THRESHOLD: float = 0.8
    MAX_GROUP_SIZE: int = 50
    RCA_MAX_TOKENS: int = 2000
    
    # Vector store settings
    EMBEDDING_DIMENSION: int = 768
    VECTOR_SEARCH_LIMIT: int = 10
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"
    
    # Data directories
    DATA_DIR: str = "./data"
    UPLOAD_DIR: str = "./data/uploads"
    
    # Security settings
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Alert monitoring systems
    MONITORING_SYSTEMS: List[str] = [
        "Prometheus",
        "Grafana",
        "Nagios",
        "Zabbix",
        "DataDog",
        "New Relic",
        "PagerDuty"
    ]
    
    # Alert severity levels
    SEVERITY_LEVELS: List[str] = [
        "Critical",
        "High", 
        "Medium",
        "Low",
        "Info"
    ]
    
    # RCA knowledge base
    RCA_KNOWLEDGE_BASE: str = """
    Common root causes for system alerts:
    
    1. Infrastructure Issues:
       - Server hardware failures
       - Network connectivity problems
       - Storage capacity issues
       - Memory/CPU resource exhaustion
    
    2. Application Issues:
       - Code bugs and logic errors
       - Memory leaks
       - Database connection failures
       - API timeouts and rate limiting
    
    3. Configuration Issues:
       - Incorrect service configurations
       - Environment variable mismatches
       - Certificate expirations
       - DNS resolution problems
    
    4. External Dependencies:
       - Third-party service outages
       - Database performance issues
       - Cache server problems
       - Load balancer misconfigurations
    
    5. Security Issues:
       - DDoS attacks
       - Authentication failures
       - SSL/TLS certificate issues
       - Firewall blocking legitimate traffic
    """
    
    class Config:
        env_file = ".env"
        case_sensitive = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create necessary directories
        os.makedirs(self.DATA_DIR, exist_ok=True)
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)
        os.makedirs(self.CHROMADB_PERSIST_DIRECTORY, exist_ok=True)
        os.makedirs(Path(self.LOG_FILE).parent, exist_ok=True)

# Create global settings instance
settings = Settings()

# Validate Ollama connection on import
def validate_ollama_connection():
    """Validate that Ollama is accessible"""
    import requests
    try:
        response = requests.get(f"{settings.OLLAMA_HOST}/api/tags", timeout=5)
        return response.status_code == 200
    except Exception:
        return False

# Environment-specific configurations
class DevelopmentSettings(Settings):
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"

class ProductionSettings(Settings):
    DEBUG: bool = False
    LOG_LEVEL: str = "WARNING"

class TestingSettings(Settings):
    DEBUG: bool = True
    CHROMADB_COLLECTION: str = "test_alerts"
    CHROMADB_PERSIST_DIRECTORY: str = "./data/test_chromadb"

def get_settings() -> Settings:
    """Factory function to get settings based on environment"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionSettings()
    elif env == "testing":
        return TestingSettings()
    else:
        return DevelopmentSettings()
