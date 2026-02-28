"""
Serviço de acesso ao Unity Catalog
Execução de queries SQL e acesso a volumes
"""
import logging
import os
import pandas as pd
from typing import Optional, Dict, Any, List
from databricks.sdk import WorkspaceClient

logger = logging.getLogger(__name__)


class UnityCatalogService:
    """
    Serviço para acesso ao Unity Catalog via Databricks SDK
    """
    
    _workspace_client: Optional[WorkspaceClient] = None
    
    def __init__(self):
        self.env_mode = os.environ.get("ENV", "prod")
        self.catalog = os.environ.get("CATALOG", "")
        self.schema = os.environ.get("DATABASE", "")
        self.http_path = os.environ.get("DATABRICKS_HTTP_PATH", "")
        self.volume_path = os.environ.get("VOLUME_PATH", "")
    
    @property
    def warehouse_id(self) -> str:
        """ID do SQL Warehouse extraído do HTTP_PATH"""
        if self.http_path:
            return self.http_path.split("/")[-1]
        return ""
    
    @property
    def workspace_client(self) -> WorkspaceClient:
        """Lazy initialization do WorkspaceClient"""
        if UnityCatalogService._workspace_client is None:
            try:
                if self.env_mode == "local":
                    UnityCatalogService._workspace_client = WorkspaceClient(
                        host=os.environ.get("DATABRICKS_HOST"),
                        token=os.environ.get("DATABRICKS_TOKEN")
                    )
                    logger.info("🔧 WorkspaceClient inicializado em modo LOCAL")
                else:
                    # Suppress verbose logging in production
                    logging.getLogger("databricks.sdk").setLevel(logging.ERROR)
                    UnityCatalogService._workspace_client = WorkspaceClient()
                    logger.info("🚀 WorkspaceClient inicializado em modo PRODUCTION (OAuth M2M)")
            except Exception as e:
                logger.error(f"⚠️ Erro ao inicializar WorkspaceClient: {e}")
                raise
        return UnityCatalogService._workspace_client
    
    def execute_query(self, query: str) -> pd.DataFrame:
        """
        Executa query SQL no Unity Catalog
        
        Args:
            query: Query SQL a executar
            
        Returns:
            DataFrame com os resultados
        """
        try:
            response = self.workspace_client.statement_execution.execute_statement(
                warehouse_id=self.warehouse_id,
                statement=query,
                catalog=self.catalog,
                schema=self.schema
            )
            
            if response.result and response.result.data_array:
                columns = [col.name for col in response.manifest.schema.columns]
                data = response.result.data_array
                return pd.DataFrame(data, columns=columns)
            
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"❌ Erro ao executar query: {e}")
            return pd.DataFrame()
    
    def get_contract_track(self) -> pd.DataFrame:
        """Lista todos os PDFs rastreados"""
        query = f"""
            SELECT file_name, 
                   file_path,
                   type, 
                   FORMAT_NUMBER(ROUND(size / 1024, 2), 0) AS size,
                   CASE WHEN processed = 'S' THEN '✅' ELSE '❌' END AS processed,
                   COALESCE(DATE_FORMAT(upload_time, 'dd/MM/yyyy'), '-') AS upload_time,
                   COALESCE(DATE_FORMAT(processed_time, 'dd/MM/yyyy'), '-') AS processed_time
              FROM {self.catalog}.{self.schema}.contract_track
             ORDER BY upload_time DESC, processed_time DESC
        """
        return self.execute_query(query)
    
    def get_contract_extract(self, pdf_filter: Optional[str] = None) -> pd.DataFrame:
        """Lista contratos extraídos"""
        query = f"""
            SELECT path, 
                   REPLACE(path, 'dbfs:', '') as volume,
                   SUBSTRING_INDEX(path, '/', -1) as pdf,
                   tipo_contrato,
                   nome_contrato,
                   contratante,
                   contratado,
                   FORMAT_NUMBER(valor_total, 2) as valor_total,
                   moeda,
                   DATE_FORMAT(data_assinatura, 'dd/MM/yyyy') as data_assinatura,
                   DATE_FORMAT(data_inicio_vigencia, 'dd/MM/yyyy') as data_inicio_vigencia,
                   DATE_FORMAT(data_fim_vigencia, 'dd/MM/yyyy') as data_fim_vigencia,
                   prazo_vigencia,
                   objeto_contrato,
                   forma_pagamento,
                   condicoes_pagamento,
                   clausula_rescisao,
                   FORMAT_NUMBER(multa_rescisao, 2) as multa_rescisao,
                   garantias,
                   confidencialidade,
                   foro,
                   observacoes,
                   summarize
              FROM {self.catalog}.{self.schema}.contract_extract
             WHERE 1=1
        """
        
        if pdf_filter:
            # Escapar aspas simples para evitar SQL injection
            safe_filter = pdf_filter.replace("'", "''")
            query += f" AND path LIKE CONCAT('%', REPLACE(REPLACE('{safe_filter}', '%20', ' '),'+', ' '), '%')"
        
        return self.execute_query(query)

    def get_contract_templates(self) -> pd.DataFrame:
        """Lista todos os itens de templates (tabela única contract_template)"""
        query = f"""
            SELECT template_name, tipo_contrato_match, item_description, ord,
                   COALESCE(DATE_FORMAT(created_at, 'dd/MM/yyyy'), '-') AS created_at
              FROM {self.catalog}.{self.schema}.contract_template
             ORDER BY template_name, COALESCE(ord, 0)
        """
        return self.execute_query(query)

    def get_contract_template_items(self, template_name: Optional[str] = None) -> pd.DataFrame:
        """Lista itens dos templates. Se template_name informado, filtra por ele (mesma tabela contract_template)."""
        query = f"""
            SELECT template_name, tipo_contrato_match, item_description, ord,
                   COALESCE(DATE_FORMAT(created_at, 'dd/MM/yyyy'), '-') AS created_at
              FROM {self.catalog}.{self.schema}.contract_template
        """
        if template_name:
            query += f" WHERE template_name = '{template_name.replace(chr(39), chr(39)+chr(39))}'"
        query += " ORDER BY COALESCE(ord, 0), item_description"
        return self.execute_query(query)

    def get_contract_compliance(
        self, path_filter: Optional[str] = None, template_name: Optional[str] = None
    ) -> pd.DataFrame:
        """Lista resultados de compliance (contract_compliance). Filtros opcionais por path e/ou template."""
        query = f"""
            SELECT path,
                   REPLACE(path, 'dbfs:', '') AS volume,
                   SUBSTRING_INDEX(path, '/', -1) AS pdf,
                   template_name, item_description, status, evidence,
                   COALESCE(DATE_FORMAT(validated_at, 'dd/MM/yyyy HH:mm'), '-') AS validated_at,
                   auditor_status, auditor_notes,
                   COALESCE(DATE_FORMAT(audited_at, 'dd/MM/yyyy HH:mm'), '-') AS audited_at
              FROM {self.catalog}.{self.schema}.contract_compliance
             WHERE 1=1
        """
        if path_filter:
            safe = path_filter.replace("'", "''")
            query += f" AND path LIKE CONCAT('%', REPLACE(REPLACE('{safe}', '%20', ' '), '+', ' '), '%')"
        if template_name:
            safe = template_name.replace("'", "''")
            query += f" AND template_name = '{safe}'"
        query += " ORDER BY path, template_name, item_description"
        return self.execute_query(query)

    def update_compliance_audit(
        self,
        path: str,
        template_name: str,
        item_description: str,
        auditor_status: str,
        auditor_notes: Optional[str] = None,
    ) -> bool:
        """Atualiza o parecer do auditor para um item de compliance. path deve ser o path completo (ex: dbfs:/Volumes/...)."""
        try:
            path_safe = path.replace("'", "''")
            template_safe = template_name.replace("'", "''")
            desc_safe = item_description.replace("'", "''")
            notes_val = f"'{auditor_notes.replace(chr(39), chr(39)+chr(39))}'" if auditor_notes else "NULL"
            update_sql = f"""
                UPDATE {self.catalog}.{self.schema}.contract_compliance
                   SET auditor_status = '{auditor_status.replace("'", "''")}',
                       auditor_notes = {notes_val},
                       audited_at = current_timestamp()
                 WHERE path = '{path_safe}'
                   AND template_name = '{template_safe}'
                   AND item_description = '{desc_safe}'
            """
            self.execute_query(update_sql.strip())
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar auditoria de compliance: {e}")
            return False

    def upload_file(self, file_path: str, content: bytes) -> bool:
        """
        Faz upload de arquivo para o volume
        
        Args:
            file_path: Caminho completo no volume
            content: Bytes do arquivo
            
        Returns:
            True se sucesso
        """
        import io
        try:
            binary_data = io.BytesIO(content)
            self.workspace_client.files.upload(file_path, binary_data, overwrite=True)
            logger.info(f"✅ Arquivo uploaded: {file_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Erro no upload: {e}")
            return False
    
    def run_extract_job(self, pdf_path: str) -> Dict[str, Any]:
        """
        Executa job de extração para um PDF específico
        
        Args:
            pdf_path: Caminho do PDF
            
        Returns:
            Dict com run_id
        """
        try:
            job_id = os.environ.get("EXTRACT_JOB_ID", "")
            if not job_id:
                return {"error": "EXTRACT_JOB_ID não configurado"}
            
            run = self.workspace_client.jobs.run_now(
                job_id=job_id,
                notebook_params={
                    "catalog": self.catalog,
                    "database": self.schema,
                    "trackTableName": "contract_track",
                    "parsedTableName": "contract_parsed",
                    "extractTableName": "contract_extract",
                    "sourcePDFPath": pdf_path,
                    "limit": "100"
                }
            )
            return {"run_id": run.run_id}
        except Exception as e:
            logger.error(f"❌ Erro ao executar job: {e}")
            return {"error": str(e)}
    
    def get_pdf_content(self, pdf_path: str) -> Optional[bytes]:
        """
        Obtém conteúdo de um PDF do volume
        
        Args:
            pdf_path: Caminho do PDF no volume
            
        Returns:
            Bytes do arquivo ou None
        """
        try:
            import requests
            
            # Obter token para API
            if self.env_mode == "local":
                token = os.environ.get("DATABRICKS_TOKEN")
            else:
                # Em prod, extrair token do workspace_client
                try:
                    token = self.workspace_client.api_client.token()
                except:
                    token = None
            
            if not token:
                logger.error("Token não disponível para download de PDF")
                return None
            
            host = os.environ.get("DATABRICKS_HOST", "")
            if not host.startswith("http"):
                host = f"https://{host}"
            
            url = f"{host}/api/2.0/fs/files{pdf_path}"
            headers = {"Authorization": f"Bearer {token}"}
            
            response = requests.get(url, headers=headers, timeout=60)
            
            if response.ok:
                return response.content
            else:
                logger.error(f"Erro ao baixar PDF: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erro ao obter PDF: {e}")
            return None


# Instância singleton
unity_catalog_service = UnityCatalogService()

