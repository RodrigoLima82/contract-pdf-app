"""
API endpoints para Chat com Multi-Agent ou Genie
"""
from typing import List, Optional
from pydantic import BaseModel, Field
import logging
import json

from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import StreamingResponse

from ..services.genie_service import genie_service
from ..services.unity_catalog_service import unity_catalog_service

router = APIRouter(prefix="/chat", tags=["Chat"])
logger = logging.getLogger(__name__)


class ChatMessage(BaseModel):
    """Mensagem de chat"""
    role: str = Field(..., description="user ou assistant")
    content: str


@router.post("/")
async def chat_endpoint(
    messages: List[dict] = Body(..., description="Histórico de mensagens"),
    session_id: Optional[str] = Body(None, description="ID da sessão")
):
    """
    Endpoint de chat com streaming usando Server-Sent Events (SSE).
    
    Prioridade:
    1. Se AGENT_ENDPOINT configurado → usa Multi-Agent com contexto dos contratos
    2. Se GENIE_SPACE_ID configurado → usa Genie Space
    3. Se nenhum → retorna erro amigável
    
    Returns:
        StreamingResponse: Server-Sent Events stream com respostas do agente
    """
    return StreamingResponse(
        genie_service.process_message_streaming(messages=messages, session_id=session_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )

