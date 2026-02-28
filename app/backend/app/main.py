"""
Contract Extract App - FastAPI Application
Sistema de extração e consulta de contratos PDF
"""
from contextlib import asynccontextmanager
from pathlib import Path
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .api import chat, documents, config_api

# Configuração de logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerenciar lifecycle da aplicação"""
    # Startup
    logger.info("🚀 Contract Extract API - Pronta para uso!")
    logger.info(f"📚 Docs: http://localhost:8000/docs")
    
    # Log configuração
    from .services.genie_service import genie_service
    if genie_service.agent_endpoint:
        logger.info(f"🤖 Multi-Agent: {genie_service.agent_endpoint}")
    elif genie_service.space_id:
        logger.info(f"🔮 Genie Space: {genie_service.space_id}")
    else:
        logger.warning("⚠️ Nenhum serviço de chat configurado")
    
    yield
    
    # Shutdown
    logger.info("👋 Encerrando aplicação...")


# Criar aplicação FastAPI
app = FastAPI(
    title="Contract Extract API",
    description="Sistema de extração e consulta de contratos PDF",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configurar CORS: em produção defina CORS_ORIGINS (evite * com allow_credentials)
_cors_origins = settings.cors_origins_list
if "*" in _cors_origins and len(_cors_origins) == 1:
    logger.warning("CORS allow_origins=['*'] com allow_credentials=True é inseguro em produção. Defina CORS_ORIGINS no ambiente.")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(chat.router)
app.include_router(documents.router)
app.include_router(config_api.router)


# Servir arquivos estáticos do frontend
# Tentar múltiplos caminhos possíveis
static_paths = [
    Path(__file__).parent.parent / "frontend" / "build",  # Relativo ao app/
    Path(__file__).parent.parent.parent / "frontend" / "build",  # Relativo ao backend/
    Path("frontend/build"),  # Relativo ao CWD
    Path("../frontend/build"),
]

static_dir = None
for path in static_paths:
    if path.exists() and path.is_dir():
        static_dir = path
        break

if static_dir:
    # Montar assets estáticos
    assets_dir = static_dir / "static"
    if assets_dir.exists():
        app.mount("/static", StaticFiles(directory=str(assets_dir)), name="static")
    
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Servir SPA - retorna index.html para rotas não-API"""
        # Se for uma rota da API, não interceptar
        if full_path.startswith("api") or full_path.startswith("docs") or full_path.startswith("redoc") or full_path.startswith("chat"):
            return JSONResponse({"error": "Not found"}, status_code=404)
        
        # Tentar servir arquivo estático se existir
        file_path = static_dir / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        
        # Caso contrário, retornar index.html (SPA)
        index_path = static_dir / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        
        return JSONResponse({"error": "Frontend not found"}, status_code=404)
    
    logger.info(f"✅ Frontend estático montado de: {static_dir}")
else:
    @app.get("/")
    async def root():
        """Endpoint raiz quando não há frontend"""
        return {
            "message": "Contract Extract API",
            "version": "1.0.0",
            "status": "running",
            "docs": "/docs"
        }
    
    logger.info("ℹ️ Frontend não encontrado - modo API only")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

