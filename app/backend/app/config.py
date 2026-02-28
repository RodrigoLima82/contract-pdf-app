"""
Configurações da aplicação
"""
import os
from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configurações da aplicação"""
    
    # Aplicação
    APP_NAME: str = "Contract Extract"
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,*"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Lista de origens CORS"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    # Databricks Workspace
    DATABRICKS_HOST: Optional[str] = None
    DATABRICKS_TOKEN: Optional[str] = None
    DATABRICKS_HTTP_PATH: Optional[str] = None
    
    @property
    def databricks_host(self) -> str:
        """URL do workspace Databricks"""
        host = self.DATABRICKS_HOST or os.environ.get("DATABRICKS_HOST", "")
        if host and not host.startswith("http"):
            host = f"https://{host}"
        return host
    
    @property
    def warehouse_id(self) -> str:
        """ID do SQL Warehouse extraído do HTTP_PATH"""
        http_path = self.DATABRICKS_HTTP_PATH or os.environ.get("DATABRICKS_HTTP_PATH", "")
        if http_path:
            return http_path.split("/")[-1]
        return ""
    
    # Unity Catalog
    CATALOG: Optional[str] = None
    DATABASE: Optional[str] = None  # Schema
    VOLUME_PATH: Optional[str] = None
    
    @property
    def catalog_name(self) -> str:
        return self.CATALOG or os.environ.get("CATALOG", "")
    
    @property
    def schema_name(self) -> str:
        return self.DATABASE or os.environ.get("DATABASE", "")
    
    @property
    def volume_path(self) -> str:
        return self.VOLUME_PATH or os.environ.get("VOLUME_PATH", "")
    
    # Secrets
    SECRET_SCOPE: Optional[str] = None
    SECRET_KEY: Optional[str] = None
    
    # Endpoints
    AGENT_ENDPOINT: Optional[str] = None
    GENIE_SPACE_ID: Optional[str] = None
    AUDIO_ENDPOINT: Optional[str] = None
    LLM_ENDPOINT: str = "databricks-gpt-5-2"
    
    @property
    def agent_endpoint(self) -> str:
        return self.AGENT_ENDPOINT or os.environ.get("AGENT_ENDPOINT", "")
    
    @property
    def genie_space_id(self) -> str:
        return self.GENIE_SPACE_ID or os.environ.get("GENIE_SPACE_ID", "")
    
    # Jobs
    EXTRACT_JOB_ID: Optional[str] = None
    
    @property
    def extract_job_id(self) -> str:
        return self.EXTRACT_JOB_ID or os.environ.get("EXTRACT_JOB_ID", "")
    
    # Dashboard
    DASHBOARD_URL: Optional[str] = None
    
    @property
    def dashboard_url(self) -> str:
        return self.DASHBOARD_URL or os.environ.get("DASHBOARD_URL", "")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


# Instância global de configurações
settings = Settings()

