"""
API endpoints para Documentos (PDFs)
Upload, listagem e extração
"""
import os
import re
from typing import Optional, List, Dict, Any
import logging

from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import Response

from ..services.unity_catalog_service import unity_catalog_service
from ..config import settings

router = APIRouter(prefix="/api", tags=["Documents"])
logger = logging.getLogger(__name__)

# Nome de arquivo seguro: apenas basename, extensão .pdf, sem path traversal
ALLOWED_FILENAME_PATTERN = re.compile(r"^[a-zA-Z0-9_\-\.]+\.pdf$", re.IGNORECASE)


def _sanitize_upload_filename(name: Optional[str]) -> Optional[str]:
    """Retorna apenas o basename se for um nome de PDF válido; caso contrário None."""
    if not name or ".." in name or name.strip() != name:
        return None
    base = os.path.basename(name)
    if not ALLOWED_FILENAME_PATTERN.match(base):
        return None
    return base


def _sanitize_pdf_param(pdf: Optional[str]) -> Optional[str]:
    """Remove path traversal e caracteres perigosos do parâmetro pdf."""
    if not pdf or ".." in pdf or pdf.strip() != pdf:
        return None
    base = os.path.basename(pdf.strip())
    if not base or len(base) > 255:
        return None
    # Permite apenas caracteres seguros no nome do arquivo
    if re.search(r"[^\w\-\.]", base):
        return None
    return base


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload de arquivo PDF para o volume"""
    try:
        safe_filename = _sanitize_upload_filename(file.filename)
        if not safe_filename:
            raise HTTPException(
                status_code=400,
                detail="Nome de arquivo inválido. Use apenas .pdf e caracteres alfanuméricos, hífen ou underscore.",
            )
        file_bytes = file.file.read()
        volume_path = settings.volume_path
        file_path = f"{volume_path}/{safe_filename}"
        
        logger.info(f"📤 Uploading: {file_path}")
        
        success = unity_catalog_service.upload_file(file_path, file_bytes)
        
        if success:
            return {"filename": safe_filename}
        else:
            raise HTTPException(status_code=500, detail="Erro no upload")
            
    except Exception as e:
        logger.error(f"❌ Erro no upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/data")
async def get_extract_data() -> List[Dict[str, Any]]:
    """Lista todos os PDFs rastreados"""
    try:
        df = unity_catalog_service.get_contract_track()
        
        if df.empty:
            logger.info("📊 Nenhum dado encontrado")
            return []
        
        expected_cols = ["file_name", "type", "size", "processed", "file_path", "upload_time", "processed_time"]
        missing_cols = [col for col in expected_cols if col not in df.columns]
        
        if missing_cols:
            logger.warning(f"⚠️ Colunas faltando: {missing_cols}")
            return []
        
        result = df.loc[:, expected_cols].to_dict(orient='records')
        logger.info(f"✅ Retornando {len(result)} registros")
        return result
        
    except Exception as e:
        logger.error(f"❌ Erro em /api/data: {e}")
        return []


@router.get("/all_data")
async def get_extract_all_data(pdf: Optional[str] = "") -> List[Dict[str, Any]]:
    """Lista dados extraídos dos contratos"""
    try:
        df = unity_catalog_service.get_contract_extract(pdf)
        
        if df.empty:
            return []
        
        cols = [
            "tipo_contrato", "nome_contrato", "contratante", "contratado", 
            "valor_total", "moeda", "data_assinatura", "data_inicio_vigencia", 
            "data_fim_vigencia", "prazo_vigencia", "objeto_contrato", 
            "forma_pagamento", "condicoes_pagamento", "clausula_rescisao", 
            "multa_rescisao", "garantias", "confidencialidade", "foro", 
            "observacoes", "summarize"
        ]
        
        available_cols = [c for c in cols if c in df.columns]
        return df.loc[:, available_cols].to_dict(orient='records')
        
    except Exception as e:
        logger.error(f"❌ Erro em /api/all_data: {e}")
        return []


@router.get("/pdf")
async def get_pdf(pdf: Optional[str] = ""):
    """Retorna conteúdo de um PDF"""
    try:
        df = unity_catalog_service.get_contract_extract(pdf)
        
        if df.empty or 'volume' not in df.columns:
            raise HTTPException(status_code=404, detail="PDF não encontrado")
        
        volume_path = df['volume'].iloc[0]
        content = unity_catalog_service.get_pdf_content(volume_path)
        
        if content:
            return Response(content=content, media_type="application/pdf")
        else:
            raise HTTPException(status_code=404, detail="Erro ao baixar PDF")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro em /api/pdf: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summarize")
async def get_extract_summary(pdf: Optional[str] = "") -> str:
    """Retorna resumo de um contrato"""
    try:
        df = unity_catalog_service.get_contract_extract(pdf)
        
        if df.empty or 'summarize' not in df.columns:
            return ""
        
        return df['summarize'].iloc[0] or ""
        
    except Exception as e:
        logger.error(f"❌ Erro em /api/summarize: {e}")
        return ""


@router.get("/extract")
async def start_job(pdf: Optional[str] = "") -> Dict[str, Any]:
    """Inicia job de extração para um PDF"""
    try:
        volume_path = settings.volume_path
        if pdf:
            safe_pdf = _sanitize_pdf_param(pdf)
            if not safe_pdf:
                raise HTTPException(status_code=400, detail="Parâmetro pdf inválido.")
            full_path = f"{volume_path}/{safe_pdf}"
        else:
            full_path = volume_path
        result = unity_catalog_service.run_extract_job(full_path)
        return result
        
    except Exception as e:
        logger.error(f"❌ Erro em /api/extract: {e}")
        return {"error": str(e)}


# --- Templates e Compliance ---


@router.get("/templates")
async def get_templates() -> List[Dict[str, Any]]:
    """Lista templates de contrato (o que deve ser validado por tipo de contrato)"""
    try:
        df = unity_catalog_service.get_contract_templates()
        if df.empty:
            return []
        return df.to_dict(orient="records")
    except Exception as e:
        logger.error(f"❌ Erro em /api/templates: {e}")
        return []


@router.get("/templates/{template_name}/items")
async def get_template_items(template_name: str) -> List[Dict[str, Any]]:
    """Lista itens obrigatórios de um template (validados em cada contrato)"""
    try:
        df = unity_catalog_service.get_contract_template_items(template_name=template_name)
        if df.empty:
            return []
        return df.to_dict(orient="records")
    except Exception as e:
        logger.error(f"❌ Erro em /api/templates/.../items: {e}")
        return []


@router.get("/compliance")
async def get_compliance(pdf: Optional[str] = "", template: Optional[str] = "") -> List[Dict[str, Any]]:
    """Lista resultado de compliance: por contrato (pdf=) e/ou por template (template=). Status: Compliance ou Não Compliance."""
    try:
        df = unity_catalog_service.get_contract_compliance(
            path_filter=pdf or None,
            template_name=template or None,
        )
        if df.empty:
            return []
        return df.to_dict(orient="records")
    except Exception as e:
        logger.error(f"❌ Erro em /api/compliance: {e}")
        return []


@router.patch("/compliance/audit")
async def update_compliance_audit(body: Dict[str, Any]) -> Dict[str, Any]:
    """Atualiza o parecer do auditor para um item de compliance. Body: path, template_name, item_description, auditor_status ('Compliance'|'Não Compliance'), auditor_notes (opcional)."""
    try:
        path = body.get("path")
        template_name = body.get("template_name")
        item_description = body.get("item_description")
        auditor_status = body.get("auditor_status")
        if not path or not template_name or not item_description or not auditor_status:
            raise HTTPException(
                status_code=400,
                detail="path, template_name, item_description e auditor_status são obrigatórios",
            )
        if auditor_status not in ("Compliance", "Não Compliance"):
            raise HTTPException(status_code=400, detail="auditor_status deve ser 'Compliance' ou 'Não Compliance'")
        auditor_notes = body.get("auditor_notes")
        ok = unity_catalog_service.update_compliance_audit(
            path=path,
            template_name=template_name,
            item_description=item_description,
            auditor_status=auditor_status,
            auditor_notes=auditor_notes,
        )
        if not ok:
            raise HTTPException(status_code=500, detail="Erro ao salvar parecer do auditor")
        return {"ok": True, "auditor_status": auditor_status}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro em /api/compliance/audit: {e}")
        raise HTTPException(status_code=500, detail=str(e))

