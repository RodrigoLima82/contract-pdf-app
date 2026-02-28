"""
API endpoint para configuração do frontend
"""
import logging
from typing import Dict, Any

from fastapi import APIRouter

from ..config import settings

router = APIRouter(tags=["Config"])
logger = logging.getLogger(__name__)


@router.get("/api/config")
async def get_config() -> Dict[str, Any]:
    """
    Retorna configuração para o frontend
    Inclui dashboard_url, catalog e schema
    """
    return {
        "dashboard_url": settings.dashboard_url or "",
        "catalog": settings.catalog_name or "",
        "schema": settings.schema_name or ""
    }


@router.get("/api/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint"""
    import time
    return {
        "status": "healthy",
        "service": "contract-extract",
        "timestamp": int(time.time())
    }


@router.get("/api/status")
async def status() -> Dict[str, Any]:
    """Status do sistema"""
    from ..services.genie_service import genie_service
    
    return {
        "api": "online",
        "storage": "unity_catalog",
        "databricks": {
            "catalog": settings.catalog_name,
            "schema": settings.schema_name,
            "agent_endpoint": genie_service.agent_endpoint or "",
            "genie_space_id": genie_service.space_id or ""
        }
    }

