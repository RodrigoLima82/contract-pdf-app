#!/usr/bin/env python3
"""
Contract Extract App - Script de Setup
======================================

Configura todo o ambiente necessário para o projeto em uma única execução.

Uso:
    python setup.py --profile <profile> --catalog <catalog> --warehouse-id <id> --env <env>

Exemplo:
    python setup.py --profile adb-workspace --catalog meu_catalog --warehouse-id abc123 --env prod
"""

import argparse
import subprocess
import sys
import json
import time
import uuid
from pathlib import Path



# Cores para output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_step(step: int, total: int, message: str):
    print(f"\n{Colors.BLUE}{Colors.BOLD}[{step}/{total}]{Colors.END} {message}")


def print_success(message: str):
    print(f"  {Colors.GREEN}✅ {message}{Colors.END}")


def print_warning(message: str):
    print(f"  {Colors.YELLOW}⚠️  {message}{Colors.END}")


def print_error(message: str):
    print(f"  {Colors.RED}❌ {message}{Colors.END}")


def print_info(message: str):
    print(f"  {Colors.CYAN}ℹ️  {message}{Colors.END}")


def run_command(cmd: list, cwd: str = None, check: bool = True) -> tuple:
    """Executa comando e retorna (sucesso, stdout, stderr)"""
    try:
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=check)
        return True, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr


def check_databricks_cli():
    """Verifica se Databricks CLI está instalado"""
    try:
        subprocess.run(["databricks", "--version"], capture_output=True, text=True)
        return True
    except FileNotFoundError:
        return False


def create_secrets_scope(profile: str, scope_name: str) -> bool:
    """Cria o scope de secrets se não existir"""
    success, stdout, stderr = run_command(
        ["databricks", "secrets", "list-scopes", "--profile", profile],
        check=False
    )
    
    if scope_name in stdout:
        print_info(f"Scope '{scope_name}' já existe")
        return True
    
    success, stdout, stderr = run_command(
        ["databricks", "secrets", "create-scope", scope_name, "--profile", profile],
        check=False
    )
    
    if success or "already exists" in stderr.lower():
        return True
    
    print_error(f"Erro ao criar scope: {stderr}")
    return False


def set_secret(profile: str, scope: str, key: str, value: str) -> bool:
    """Define um secret"""
    try:
        process = subprocess.Popen(
            ["databricks", "secrets", "put-secret", scope, key, "--profile", profile],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        process.communicate(input=value)
        return process.returncode == 0
    except Exception as e:
        print_error(f"Erro ao definir secret {key}: {e}")
        return False


def setup_secrets(profile: str, scope: str, config: dict) -> bool:
    """Configura todos os secrets necessários"""
    if not create_secrets_scope(profile, scope):
        return False
    
    print_success(f"Scope '{scope}' pronto")
    
    secrets_to_create = {
        "warehouse_id": config["warehouse_id"],
        "catalog_name": config["catalog"],
        "schema_name": config["schema"],
    }
    
    # Adicionar PAT se fornecido
    if config.get("pat"):
        secrets_to_create["genie_pat"] = config["pat"]
    
    for key, value in secrets_to_create.items():
        if value:
            if set_secret(profile, scope, key, value):
                display_value = value if key != "genie_pat" else "***"
                print_success(f"Secret '{key}' = {display_value}")
            else:
                print_warning(f"Não foi possível definir secret '{key}'")
    
    return True


def get_scope_name(env: str, prefix: str = "contract-extract") -> str:
    """Retorna o nome do scope de secrets para o ambiente"""
    return f"{prefix}-{env}"


def run_sql_statement(profile: str, warehouse_id: str, catalog: str, schema: str, sql: str) -> bool:
    """Executa statement SQL via Databricks CLI"""
    try:
        cmd = [
            "databricks", "api", "post", "/api/2.0/sql/statements",
            "--profile", profile,
            "--json", json.dumps({
                "warehouse_id": warehouse_id,
                "statement": sql,
                "catalog": catalog,
                "schema": schema,
                "wait_timeout": "30s"
            })
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        
        # Verificar resultado
        if "SUCCEEDED" in result.stdout or "succeeded" in result.stdout.lower():
            return True
        elif "already exists" in result.stdout.lower():
            return True
        elif "FAILED" in result.stdout or "error" in result.stdout.lower():
            return False
        
        return True
    except Exception as e:
        print_error(f"Erro ao executar SQL: {e}")
        return False


def create_tables(profile: str, warehouse_id: str, catalog: str, schema: str) -> bool:
    """Cria todas as tabelas necessárias no Unity Catalog"""
    
    # 1. Criar o schema
    print_info(f"Criando schema {catalog}.{schema}...")
    if run_sql_statement(profile, warehouse_id, catalog, "default", 
                         f"CREATE DATABASE IF NOT EXISTS {catalog}.{schema}"):
        print_success(f"Schema {catalog}.{schema} criado/existente")
    else:
        print_warning(f"Não foi possível verificar schema {catalog}.{schema}")
    
    # 2. Criar o Volume
    print_info(f"Criando volume {catalog}.{schema}.files...")
    if run_sql_statement(profile, warehouse_id, catalog, schema,
                         f"CREATE VOLUME IF NOT EXISTS {catalog}.{schema}.files"):
        print_success(f"Volume 'files' criado/existente")
    else:
        print_warning(f"Não foi possível criar volume 'files'")
    
    # 3. Criar cada tabela individualmente
    tables = {
        "contract_track": f"""
            CREATE TABLE IF NOT EXISTS {catalog}.{schema}.contract_track (
                file_name STRING,
                type STRING,
                size BIGINT,
                processed STRING COMMENT 'S=Sim, N=Não',
                file_path STRING,
                upload_time TIMESTAMP,
                processed_time TIMESTAMP,
                file_hash STRING
            )
            TBLPROPERTIES (delta.enableChangeDataFeed = true)
        """,
        "contract_parsed": f"""
            CREATE TABLE IF NOT EXISTS {catalog}.{schema}.contract_parsed (
                path STRING,
                raw_parsed STRING,
                text STRING,
                summarize STRING,
                error_status STRING
            )
        """,
        "contract_extract": f"""
            CREATE TABLE IF NOT EXISTS {catalog}.{schema}.contract_extract (
                path STRING,
                summarize STRING,
                tipo_contrato STRING,
                nome_contrato STRING,
                contratante STRING,
                contratado STRING,
                valor_total STRING,
                moeda STRING,
                data_assinatura STRING,
                data_inicio_vigencia STRING,
                data_fim_vigencia STRING,
                prazo_vigencia STRING,
                objeto_contrato STRING,
                forma_pagamento STRING,
                condicoes_pagamento STRING,
                clausula_rescisao STRING,
                multa_rescisao STRING,
                garantias STRING,
                confidencialidade STRING,
                foro STRING,
                observacoes STRING
            )
        """,
        "contract_template": f"""
            CREATE TABLE IF NOT EXISTS {catalog}.{schema}.contract_template (
                template_name STRING COMMENT 'Nome do template (ex: Prestação de Serviços)',
                tipo_contrato_match STRING COMMENT 'Valor ou padrão LIKE para casar com contract_extract.tipo_contrato',
                item_description STRING COMMENT 'Item obrigatório a ser validado no contrato',
                ord INT COMMENT 'Ordem de exibição',
                created_at TIMESTAMP
            )
        """,
        "contract_compliance": f"""
            CREATE TABLE IF NOT EXISTS {catalog}.{schema}.contract_compliance (
                path STRING COMMENT 'Caminho do contrato (contract_extract.path)',
                template_name STRING COMMENT 'Template aplicado',
                item_description STRING COMMENT 'Item validado',
                status STRING COMMENT 'Compliance ou Não Compliance (IA)',
                evidence STRING COMMENT 'Trecho do contrato que justifica (opcional)',
                validated_at TIMESTAMP,
                auditor_status STRING COMMENT 'Parecer do auditor: Compliance ou Não Compliance',
                auditor_notes STRING COMMENT 'Observações do auditor',
                audited_at TIMESTAMP COMMENT 'Data/hora da auditoria'
            )
        """,
    }
    
    for table_name, create_sql in tables.items():
        print_info(f"Criando tabela {table_name}...")
        if run_sql_statement(profile, warehouse_id, catalog, schema, create_sql.strip()):
            print_success(f"Tabela {table_name} criada/existente")
        else:
            print_warning(f"Não foi possível verificar tabela {table_name}")

    # Migração: adicionar colunas de auditoria em contract_compliance (se a tabela já existia)
    for col_def in [
        ("auditor_status", "STRING", "Parecer do auditor: Compliance ou Não Compliance"),
        ("auditor_notes", "STRING", "Observações do auditor"),
        ("audited_at", "TIMESTAMP", "Data/hora da auditoria"),
    ]:
        col_name, col_type, comment = col_def
        alter_sql = f"ALTER TABLE {catalog}.{schema}.contract_compliance ADD COLUMN {col_name} {col_type} COMMENT '{comment}'"
        if run_sql_statement(profile, warehouse_id, catalog, schema, alter_sql):
            print_success(f"Coluna contract_compliance.{col_name} adicionada/existente")
        # Se falhar (coluna já existe), ignora
    
    # 4. Criar SQL Functions para processamento de contratos
    print_info("Criando SQL Functions...")
    create_sql_functions(profile, warehouse_id, catalog, schema)
    
    return True


def create_sql_functions(profile: str, warehouse_id: str, catalog: str, schema: str) -> bool:
    """Cria as funções SQL necessárias para processamento de contratos"""
    
    functions = {
        "SUMMARIZE_CONTRACT_DATA": f"""
            CREATE OR REPLACE FUNCTION {catalog}.{schema}.SUMMARIZE_CONTRACT_DATA(content STRING)
            RETURNS STRING
            LANGUAGE SQL
            RETURN ai_query(
                'databricks-gpt-5-2',
                'Resuma este contrato em português em no máximo 3 frases. Foque nos pontos principais: partes envolvidas, objeto do contrato, valor e prazo. Contrato: ' || LEFT(content, 8000)
            )
        """,
        
        "EXTRACT_CONTRACT_DATA": f"""
            CREATE OR REPLACE FUNCTION {catalog}.{schema}.EXTRACT_CONTRACT_DATA(content STRING)
            RETURNS STRUCT<
                tipo_contrato: STRING,
                nome_contrato: STRING,
                contratante: STRING,
                contratado: STRING,
                valor_total: DOUBLE,
                moeda: STRING,
                data_assinatura: STRING,
                data_inicio_vigencia: STRING,
                data_fim_vigencia: STRING,
                prazo_vigencia: STRING,
                objeto_contrato: STRING,
                forma_pagamento: STRING,
                condicoes_pagamento: STRING,
                clausula_rescisao: STRING,
                multa_rescisao: DOUBLE,
                garantias: STRING,
                confidencialidade: STRING,
                foro: STRING,
                observacoes: STRING
            >
            LANGUAGE SQL
            RETURN SELECT FROM_JSON(
                ai_query(
                    'databricks-gpt-5-2',
                    'Extraia os seguintes campos deste contrato. Se não encontrar, use null.
Campos:
1. tipo_contrato: tipo do contrato (Prestação de Serviços, Fornecimento, Locação, etc)
2. nome_contrato: nome ou título do contrato
3. contratante: nome completo do CONTRATANTE (quem contrata)
4. contratado: nome completo do CONTRATADO (quem presta o serviço)
5. valor_total: valor total do contrato (apenas número, ex: 150000.00)
6. moeda: moeda (BRL, USD, EUR)
7. data_assinatura: data de assinatura (formato YYYY-MM-DD)
8. data_inicio_vigencia: data de início da vigência (formato YYYY-MM-DD)
9. data_fim_vigencia: data de fim da vigência (formato YYYY-MM-DD)
10. prazo_vigencia: prazo de vigência descrito (ex: 12 meses, 2 anos)
11. objeto_contrato: descrição resumida do objeto do contrato (máximo 500 caracteres)
12. forma_pagamento: forma de pagamento (Boleto, Transferência, etc)
13. condicoes_pagamento: condições de pagamento (30/60/90 dias, À vista, etc)
14. clausula_rescisao: resumo da cláusula de rescisão
15. multa_rescisao: valor ou percentual da multa (apenas número)
16. garantias: descrição das garantias contratuais
17. confidencialidade: informações sobre cláusula de confidencialidade
18. foro: foro ou jurisdição competente
19. observacoes: outras informações relevantes

Retorne APENAS JSON válido: {{"tipo_contrato":"","nome_contrato":"","contratante":"","contratado":"","valor_total":null,"moeda":"","data_assinatura":"","data_inicio_vigencia":"","data_fim_vigencia":"","prazo_vigencia":"","objeto_contrato":"","forma_pagamento":"","condicoes_pagamento":"","clausula_rescisao":"","multa_rescisao":null,"garantias":"","confidencialidade":"","foro":"","observacoes":""}}

Contrato: ' || LEFT(content, 10000)
                ),
                'STRUCT<tipo_contrato: STRING, nome_contrato: STRING, contratante: STRING, contratado: STRING, valor_total: DOUBLE, moeda: STRING, data_assinatura: STRING, data_inicio_vigencia: STRING, data_fim_vigencia: STRING, prazo_vigencia: STRING, objeto_contrato: STRING, forma_pagamento: STRING, condicoes_pagamento: STRING, clausula_rescisao: STRING, multa_rescisao: DOUBLE, garantias: STRING, confidencialidade: STRING, foro: STRING, observacoes: STRING>'
            )
        """,
        "CHECK_ITEM_COMPLIANCE": f"""
            CREATE OR REPLACE FUNCTION {catalog}.{schema}.CHECK_ITEM_COMPLIANCE(summarize STRING, item_description STRING)
            RETURNS STRING
            LANGUAGE SQL
            RETURN CASE
                WHEN LOWER(TRIM(ai_query(
                    'databricks-gpt-5-2',
                    CONCAT(
                        'O texto abaixo é um resumo de contrato. O contrato contém ou atende ao seguinte item obrigatório: ', COALESCE(item_description, ''),
                        '. Responda exatamente apenas uma destas palavras: Compliance ou Nao Compliance. Nenhum outro texto. Resumo: ',
                        LEFT(COALESCE(summarize, ''), 6000)
                    )
                ))) = 'compliance' THEN 'Compliance'
                ELSE 'Não Compliance'
            END
        """
    }
    
    for func_name, create_sql in functions.items():
        print_info(f"Criando função {func_name}...")
        if run_sql_statement(profile, warehouse_id, catalog, schema, create_sql.strip()):
            print_success(f"Função {func_name} criada/atualizada")
        else:
            print_warning(f"Não foi possível criar função {func_name}")


def get_app_service_principal(profile: str, app_name: str) -> str:
    """Obtém o client_id (UUID) do Service Principal do App"""
    try:
        cmd = ["databricks", "apps", "get", app_name, "--profile", profile]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            sp_client_id = data.get("service_principal_client_id", "")
            sp_name = data.get("service_principal_name", "")
            if sp_client_id:
                print_success(f"Service Principal encontrado: {sp_name} ({sp_client_id})")
                return sp_client_id
        
        print_warning(f"Não foi possível obter Service Principal do App")
        return ""
    except Exception as e:
        print_warning(f"Erro ao obter Service Principal: {e}")
        return ""


def grant_app_permissions(profile: str, warehouse_id: str, catalog: str, schema: str, sp_id: str, scope: str) -> bool:
    """Concede permissões para o Service Principal do App"""
    
    if not sp_id:
        print_warning("Service Principal não informado. Pulando grants.")
        return False
    
    # 1. Grants no Unity Catalog (via SQL)
    print_info("Concedendo permissões no Unity Catalog...")
    grants = [
        f"GRANT USE CATALOG ON CATALOG {catalog} TO `{sp_id}`",
        f"GRANT USE SCHEMA ON SCHEMA {catalog}.{schema} TO `{sp_id}`",
        f"GRANT SELECT, MODIFY ON SCHEMA {catalog}.{schema} TO `{sp_id}`",
        f"GRANT READ VOLUME, WRITE VOLUME ON VOLUME {catalog}.{schema}.files TO `{sp_id}`",
    ]
    
    for grant_sql in grants:
        print_info(f"  {grant_sql[:60]}...")
        if run_sql_statement(profile, warehouse_id, catalog, schema, grant_sql):
            print_success("OK")
        else:
            print_warning(f"Pode ter falhado")
    
    # 2. Permissão no SQL Warehouse (via API)
    print_info(f"Concedendo permissão CAN_USE no SQL Warehouse {warehouse_id}...")
    try:
        cmd = [
            "databricks", "api", "put", 
            f"/api/2.0/permissions/sql/warehouses/{warehouse_id}",
            "--profile", profile,
            "--json", json.dumps({
                "access_control_list": [
                    {
                        "service_principal_name": sp_id,
                        "permission_level": "CAN_USE"
                    }
                ]
            })
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print_success("Permissão no SQL Warehouse concedida")
        else:
            print_warning(f"Erro ao conceder permissão no warehouse: {result.stderr[:100]}")
    except Exception as e:
        print_warning(f"Erro ao configurar warehouse: {e}")
    
    # 3. Permissão nas Secrets (via CLI)
    print_info(f"Concedendo permissão READ no scope de secrets {scope}...")
    try:
        cmd = [
            "databricks", "secrets", "put-acl", 
            scope, sp_id, "READ",
            "--profile", profile
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print_success("Permissão nas secrets concedida")
        else:
            print_warning(f"Erro ao conceder permissão nas secrets: {result.stderr[:100]}")
    except Exception as e:
        print_warning(f"Erro ao configurar secrets: {e}")
    
    # 4. Permissão nos Jobs (via API)
    print_info("Concedendo permissão CAN_MANAGE_RUN nos jobs...")
    try:
        cmd = ["databricks", "jobs", "list", "--profile", profile, "--output", "json"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            jobs_data = json.loads(result.stdout)
            if isinstance(jobs_data, list):
                jobs = jobs_data
            else:
                jobs = jobs_data.get("jobs", [])
            
            contract_jobs = [j for j in jobs if isinstance(j, dict) and 
                           "contract" in j.get("settings", {}).get("name", "").lower()]
            
            for job in contract_jobs:
                job_id = job.get("job_id")
                job_name = job.get("settings", {}).get("name", "unknown")
                print_info(f"  Job: {job_name} ({job_id})")
                
                cmd = [
                    "databricks", "api", "patch",
                    f"/api/2.0/permissions/jobs/{job_id}",
                    "--profile", profile,
                    "--json", json.dumps({
                        "access_control_list": [
                            {
                                "service_principal_name": sp_id,
                                "permission_level": "CAN_MANAGE_RUN"
                            }
                        ]
                    })
                ]
                perm_result = subprocess.run(cmd, capture_output=True, text=True)
                if perm_result.returncode == 0:
                    print_success("OK")
                else:
                    print_warning(f"Falhou")
        else:
            print_warning("Não foi possível listar jobs")
    except Exception as e:
        print_warning(f"Erro ao configurar permissões dos jobs: {e}")
    
    return True


def generate_app_yaml(catalog: str, schema: str, warehouse_id: str, env: str,
                      agent_endpoint: str = "", audio_endpoint: str = "",
                      secret_scope: str = "", secret_key: str = "",
                      extract_job_id: str = "", dashboard_url: str = "") -> bool:
    """
    Gera o app.yaml a partir do template app.{env}.yaml ou app.{env}.example.yaml.
    Substitui placeholders pelos valores do setup (nada hardcoded).
    """
    project_root = Path(__file__).parent
    app_dir = project_root / "app"
    output_path = app_dir / "app.yaml"

    env_key = "prod" if env.lower() in ("prod", "production") else "dev"
    template_path = app_dir / f"app.{env_key}.yaml"
    if not template_path.exists():
        template_path = app_dir / f"app.{env_key}.example.yaml"
    if not template_path.exists():
        print_error(f"Template não encontrado: app.{env_key}.yaml ou app.{env_key}.example.yaml")
        return False

    content = template_path.read_text(encoding="utf-8")

    # Substituir placeholders (ordem: evitar que um valor contenha outro placeholder)
    replacements = [
        ("seu_catalog", catalog),
        ("contract_pdf", schema),
        ("YOUR_WAREHOUSE_ID", warehouse_id),
        ("seu_agent_endpoint", agent_endpoint or ""),
        ("seu_whisper_endpoint", audio_endpoint or ""),
        ("JOB_ID_PLACEHOLDER", extract_job_id or ""),
        ("DASHBOARD_URL_PLACEHOLDER", dashboard_url or ""),
        ("SECRET_KEY_PLACEHOLDER", secret_key or "genie_pat"),
        ("contract-extract-dev", secret_scope or f"contract-extract-{env_key}"),
        ("contract-extract-prod", secret_scope or f"contract-extract-{env_key}"),
    ]
    for placeholder, value in replacements:
        content = content.replace(placeholder, value)

    app_dir.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")

    print_success("app.yaml gerado a partir do template")
    print_info(f"  Template: {template_path.name} | Catalog: {catalog}, Schema: {schema}, Env: {env_key}")
    return True


def find_existing_genie_space(profile: str, space_title: str) -> str:
    """
    Busca um Genie Space existente pelo título usando Databricks CLI.
    Retorna o space_id se encontrado, string vazia caso contrário.
    """
    try:
        result = subprocess.run(
            ["databricks", "api", "get", "/api/2.0/genie/spaces", "--profile", profile],
            capture_output=True, text=True
        )
        
        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                spaces = data.get("spaces", [])
                for space in spaces:
                    title = space.get("title", "") or space.get("name", "")
                    if space_title.lower() in title.lower():
                        space_id = space.get("space_id") or space.get("id", "")
                        if space_id:
                            print_success(f"Genie Space encontrado: {space_id}")
                            return space_id
            except:
                pass
    except Exception as e:
        print_warning(f"Erro ao buscar Genie Spaces: {e}")
    
    return ""


def create_genie_space(profile: str, warehouse_id: str, catalog: str, schema: str, env: str) -> str:
    """
    Cria um Genie Space via Databricks CLI (usa autenticação automática).
    Retorna o space_id se criado com sucesso, string vazia caso contrário.
    """
    # Obter email do usuário para o parent_path
    result = subprocess.run(
        ["databricks", "current-user", "me", "--profile", profile],
        capture_output=True, text=True
    )
    
    try:
        user_data = json.loads(result.stdout)
        user_email = user_data.get("userName", "")
    except:
        print_warning("Erro ao obter usuário atual")
        return ""
    
    # Configuração do Space
    space_title = f"Contract Extract - {env.upper()}"
    space_description = f"Consulta de Contratos - Tabela: {catalog}.{schema}.contract_extract"
    parent_path = f"/Workspace/Users/{user_email}"
    
    # Verificar se já existe um Space com este nome
    print_info(f"Verificando se Genie Space '{space_title}' já existe...")
    existing_id = find_existing_genie_space(profile, space_title)
    if existing_id:
        print_info(f"Usando Genie Space existente: {existing_id}")
        return existing_id
    
    # Definição do Space com a tabela contract_extract
    serialized_space = json.dumps({
        "version": 1,
        "tables": [
            {
                "table_name": f"{catalog}.{schema}.contract_extract",
                "description": "Tabela principal de contratos extraídos com campos: tipo_contrato, nome_contrato, contratante, contratado, valor_total, moeda, data_assinatura, data_inicio_vigencia, data_fim_vigencia, prazo_vigencia, objeto_contrato, forma_pagamento, condicoes_pagamento, clausula_rescisao, multa_rescisao, garantias, confidencialidade, foro, observacoes, summarize"
            }
        ],
        "curated_questions": [
            "Quantos contratos temos na base?",
            "Quais contratos vencem este ano?",
            "Liste os contratos por valor total",
            "Quais são os maiores contratos?",
            "Mostre contratos do contratante X"
        ],
        "general_instructions": "Você é um assistente especializado em análise de contratos. Responda sempre em português brasileiro. Use a tabela contract_extract para consultas sobre contratos. Os campos da tabela estão em português: tipo_contrato, nome_contrato, contratante, contratado, valor_total, moeda, data_assinatura, data_inicio_vigencia, data_fim_vigencia, etc."
    })
    
    # Payload da API
    payload = {
        "warehouse_id": warehouse_id,
        "parent_path": parent_path,
        "title": space_title,
        "description": space_description,
        "serialized_space": serialized_space
    }
    
    # Criar o Space via CLI
    try:
        print_info(f"Criando Genie Space: '{space_title}'...")
        
        result = subprocess.run(
            ["databricks", "api", "post", "/api/2.0/genie/spaces", 
             "--json", json.dumps(payload),
             "--profile", profile],
            capture_output=True, text=True
        )
        
        if result.returncode == 0:
            try:
                response_data = json.loads(result.stdout)
                space_id = response_data.get("space_id") or response_data.get("id") or response_data.get("genie_space_id", "")
                if space_id:
                    print_success(f"Genie Space criado: {space_id}")
                    
                    # Adicionar tabela ao Genie Space
                    add_table_to_genie_space(profile, space_id, catalog, schema)
                    
                    # Atualizar instruções
                    update_genie_instructions(profile, space_id)
                    
                    return space_id
                else:
                    print_warning(f"Space criado mas sem ID no retorno: {result.stdout[:200]}")
                    return ""
            except:
                print_warning(f"Erro ao parsear resposta: {result.stdout[:200]}")
                return ""
        else:
            error_msg = result.stderr or result.stdout
            if "already exists" in error_msg.lower() or "409" in error_msg:
                print_info("Genie Space já existe, buscando ID...")
                existing_id = find_existing_genie_space(profile, space_title)
                if existing_id:
                    return existing_id
            print_warning(f"Erro ao criar Genie Space: {error_msg[:200]}")
            return ""
            
    except Exception as e:
        print_warning(f"Erro ao criar Genie Space: {e}")
        return ""


def add_table_to_genie_space(profile: str, space_id: str, catalog: str, schema: str):
    """Adiciona tabela contract_extract ao Genie Space via PATCH"""
    table_name = f"{catalog}.{schema}.contract_extract"
    print_info(f"Adicionando tabela '{table_name}' ao Genie Space...")
    
    try:
        result = subprocess.run(
            ["databricks", "api", "get", 
             f"/api/2.0/genie/spaces/{space_id}?include_serialized_space=true",
             "--profile", profile],
            capture_output=True, text=True
        )
        
        if result.returncode != 0:
            print_warning(f"Erro ao ler Genie Space: {result.stderr or result.stdout}")
            return False
        
        space = json.loads(result.stdout)
        serialized = json.loads(space["serialized_space"]) if space.get("serialized_space") else {"version": 1}
        serialized.setdefault("data_sources", {}).setdefault("tables", [])
        
        tables = serialized["data_sources"]["tables"]
        if table_name not in {t.get("identifier", "") for t in tables}:
            tables.append({"identifier": table_name})
        
        patch_payload = {"serialized_space": json.dumps(serialized)}
        result = subprocess.run(
            ["databricks", "api", "patch", f"/api/2.0/genie/spaces/{space_id}",
             "--json", json.dumps(patch_payload), "--profile", profile],
            capture_output=True, text=True
        )
        
        if result.returncode == 0:
            print_success(f"Tabela adicionada ao Genie Space")
            return True
        else:
            print_warning(f"Erro ao adicionar tabela: {result.stderr or result.stdout}")
            return False
    except Exception as e:
        print_warning(f"Erro ao adicionar tabela: {e}")
        return False


def update_genie_instructions(profile: str, space_id: str):
    """Atualiza descrição e sample questions do Genie Space via PATCH"""
    print_info("Configurando Genie Space...")
    
    description = "Assistente para consultas sobre contratos. Consulte contratos por contratante, contratado, valor_total, data_fim_vigencia e tipo_contrato."
    
    sample_questions = [
        {"id": uuid.uuid4().hex, "question": ["Quantos contratos temos na base?"]},
        {"id": uuid.uuid4().hex, "question": ["Quais contratos vencem este ano (data_fim_vigencia)?"]},
        {"id": uuid.uuid4().hex, "question": ["Liste os 10 maiores contratos por valor_total"]},
        {"id": uuid.uuid4().hex, "question": ["Quais contratantes têm mais contratos?"]},
        {"id": uuid.uuid4().hex, "question": ["Mostre contratos do tipo Prestação de Serviços"]}
    ]
    
    try:
        patch_desc = {"description": description}
        result = subprocess.run(
            ["databricks", "api", "patch", f"/api/2.0/genie/spaces/{space_id}",
             "--json", json.dumps(patch_desc), "--profile", profile],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print_warning(f"Erro ao atualizar description: {result.stderr or result.stdout}")
        
        result = subprocess.run(
            ["databricks", "api", "get", 
             f"/api/2.0/genie/spaces/{space_id}?include_serialized_space=true",
             "--profile", profile],
            capture_output=True, text=True
        )
        
        if result.returncode != 0:
            print_warning(f"Erro ao ler Genie Space")
            return False
        
        space = json.loads(result.stdout)
        serialized = json.loads(space["serialized_space"]) if space.get("serialized_space") else {"version": 1}
        
        serialized.setdefault("config", {})
        serialized["config"]["sample_questions"] = sample_questions
        
        patch_payload = {"serialized_space": json.dumps(serialized)}
        result = subprocess.run(
            ["databricks", "api", "patch", f"/api/2.0/genie/spaces/{space_id}",
             "--json", json.dumps(patch_payload), "--profile", profile],
            capture_output=True, text=True
        )
        
        if result.returncode == 0:
            print_success("Instruções e perguntas configuradas")
            return True
        else:
            print_warning(f"Erro ao configurar perguntas: {result.stderr or result.stdout}")
            return False
    except Exception as e:
        print_warning(f"Erro ao configurar instruções: {e}")
        return False


def build_frontend() -> bool:
    """Faz build do frontend React"""
    frontend_path = Path(__file__).parent / "app" / "frontend"
    
    if not (frontend_path / "package.json").exists():
        print_warning("package.json não encontrado no frontend")
        return False
    
    print_info("Executando npm run build...")
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=frontend_path,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print_success("Frontend build concluído")
        return True
    else:
        print_error(f"Erro no build do frontend: {result.stderr[:200]}")
        return False


def deploy_bundle(profile: str, target: str, catalog: str, schema: str, 
                  warehouse_id: str, agent_endpoint: str = "", audio_endpoint: str = "",
                  secret_scope: str = "", secret_key: str = "") -> bool:
    """Faz deploy do Bundle Databricks (jobs + app + dashboard)"""
    project_root = Path(__file__).parent
    
    # Garantir que o diretório do Terraform exista (evita erro "chmod ... no such file or directory")
    terraform_bin_dir = project_root / ".databricks" / "bundle" / target / "bin"
    try:
        terraform_bin_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print_warning(f"Não foi possível criar {terraform_bin_dir}: {e}")
    
    # Se target prod e o binário do Terraform não existir, copiar de dev (evita novo download)
    terraform_prod = terraform_bin_dir / "terraform"
    if target == "prod" and not terraform_prod.exists():
        terraform_dev = project_root / ".databricks" / "bundle" / "dev" / "bin" / "terraform"
        if terraform_dev.exists():
            import shutil
            try:
                shutil.copy2(terraform_dev, terraform_prod)
                terraform_prod.chmod(0o755)
                print_info("Terraform reutilizado de dev (evitando novo download)")
            except Exception as e:
                print_warning(f"Não foi possível copiar Terraform de dev: {e}")
    
    cmd = [
        "databricks", "bundle", "deploy",
        "--target", target,
        "--profile", profile,
        "--force-lock",
        "--force",  # Sobrescrever recursos modificados remotamente
        "--auto-approve",  # Permitir ações destrutivas sem prompt
        "--var", f"catalog_name={catalog}",
        "--var", f"schema_name={schema}",
        "--var", f"warehouse_id={warehouse_id}",
    ]
    
    if agent_endpoint:
        cmd.extend(["--var", f"agent_endpoint={agent_endpoint}"])
    if audio_endpoint:
        cmd.extend(["--var", f"audio_endpoint={audio_endpoint}"])
    if secret_scope:
        cmd.extend(["--var", f"secret_scope={secret_scope}"])
    if secret_key:
        cmd.extend(["--var", f"secret_key={secret_key}"])
    
    result = subprocess.run(cmd, cwd=str(project_root), capture_output=True, text=True)
    
    if result.returncode != 0:
        print_error(f"Erro no deploy: {result.stderr}")
        print_info(f"Output: {result.stdout}")
        return False
    
    print(result.stdout)
    return True


def get_job_id(profile: str, job_name_pattern: str) -> str:
    """Busca o ID de um job pelo nome"""
    try:
        cmd = ["databricks", "jobs", "list", "--profile", profile, "--output", "json"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            jobs_data = json.loads(result.stdout)
            if isinstance(jobs_data, list):
                jobs = jobs_data
            else:
                jobs = jobs_data.get("jobs", [])
            
            for job in jobs:
                job_name = job.get("settings", {}).get("name", "")
                if job_name_pattern.lower() in job_name.lower():
                    return str(job.get("job_id", ""))
        
        return ""
    except Exception as e:
        print_warning(f"Erro ao buscar job: {e}")
        return ""


def get_dashboard_url(profile: str, dashboard_name_pattern: str) -> str:
    """Busca a URL de um dashboard Lakeview pelo nome"""
    try:
        # Obter host do workspace
        cmd = ["databricks", "auth", "describe", "--profile", profile]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        host = ""
        for line in result.stdout.split("\n"):
            if "Host:" in line:
                host = line.split("Host:")[1].strip().rstrip("/")
                break
        
        if not host:
            return ""
        
        # Listar Lakeview dashboards (API nova)
        cmd = ["databricks", "api", "get", "/api/2.0/lakeview/dashboards", "--profile", profile]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            dashboards = data.get("dashboards", [])
            
            for dash in dashboards:
                # Lakeview usa display_name
                dash_name = dash.get("display_name", "") or dash.get("name", "")
                if dashboard_name_pattern.lower() in dash_name.lower():
                    dash_id = dash.get("dashboard_id", "") or dash.get("id", "")
                    if dash_id:
                        # URL de embed para Lakeview dashboard
                        return f"{host}/embed/dashboardsv3/{dash_id}"
        
        # Fallback: tentar API antiga de SQL dashboards
        cmd = ["databricks", "api", "get", "/api/2.0/preview/sql/dashboards", "--profile", profile]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            dashboards = data.get("results", [])
            
            for dash in dashboards:
                dash_name = dash.get("name", "")
                if dashboard_name_pattern.lower() in dash_name.lower():
                    dash_id = dash.get("id", "")
                    if dash_id:
                        return f"{host}/embed/dashboards/{dash_id}"
        
        return ""
    except Exception as e:
        print_warning(f"Erro ao buscar dashboard: {e}")
        return ""


def create_lakeview_dashboard(profile: str, warehouse_id: str, catalog: str, schema: str, env: str) -> str:
    """Cria ou atualiza o dashboard Lakeview com os valores corretos de catalog/schema"""
    
    # Ler o template do dashboard
    dashboard_path = Path(__file__).parent / "dashboard" / "dashboard_contract.lvdash.json"
    if not dashboard_path.exists():
        print_warning(f"Template do dashboard não encontrado: {dashboard_path}")
        return ""
    
    try:
        with open(dashboard_path, "r") as f:
            dashboard_content = f.read()
        
        # Substituir as variáveis pelo valor real
        dashboard_content = dashboard_content.replace("${var.catalog_name}", catalog)
        dashboard_content = dashboard_content.replace("${var.schema_name}", schema)
        
        # Parsear para validar JSON
        dashboard_json = json.loads(dashboard_content)
        
        # Nome do dashboard
        dashboard_display_name = f"Contract Dashboard - {env.upper()}"
        
        # Obter host do workspace
        cmd = ["databricks", "auth", "describe", "--profile", profile]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        host = ""
        for line in result.stdout.split("\n"):
            if "Host:" in line:
                host = line.split("Host:")[1].strip().rstrip("/")
                break
        
        if not host:
            print_warning("Não foi possível obter o host do workspace")
            return ""
        
        # Obter email do usuário para o parent_path
        user_result = subprocess.run(
            ["databricks", "current-user", "me", "--profile", profile],
            capture_output=True, text=True
        )
        user_email = ""
        if user_result.returncode == 0:
            try:
                user_data = json.loads(user_result.stdout)
                user_email = user_data.get("userName", "")
            except:
                pass
        
        if not user_email:
            print_warning("Não foi possível obter o email do usuário")
            return ""
        
        # Verificar se o dashboard já existe
        existing_dashboard_id = None
        cmd = ["databricks", "api", "get", "/api/2.0/lakeview/dashboards", "--profile", profile]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            dashboards = data.get("dashboards", [])
            
            for dash in dashboards:
                dash_name = dash.get("display_name", "")
                if dashboard_display_name.lower() in dash_name.lower() or "contract" in dash_name.lower():
                    existing_dashboard_id = dash.get("dashboard_id", "")
                    print_info(f"Dashboard existente encontrado: {dash_name} ({existing_dashboard_id})")
                    break
        
        # Serializar o conteúdo do dashboard
        serialized_dashboard = json.dumps(dashboard_json)
        
        if existing_dashboard_id:
            # Atualizar dashboard existente
            update_payload = {
                "display_name": dashboard_display_name,
                "warehouse_id": warehouse_id,
                "serialized_dashboard": serialized_dashboard
            }
            
            cmd = [
                "databricks", "api", "patch",
                f"/api/2.0/lakeview/dashboards/{existing_dashboard_id}",
                "--json", json.dumps(update_payload),
                "--profile", profile
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print_success(f"Dashboard atualizado: {dashboard_display_name}")
                return f"{host}/embed/dashboardsv3/{existing_dashboard_id}"
            else:
                print_warning(f"Erro ao atualizar dashboard: {result.stderr[:150]}")
        
        # Criar novo dashboard
        create_payload = {
            "display_name": dashboard_display_name,
            "warehouse_id": warehouse_id,
            "serialized_dashboard": serialized_dashboard,
            "parent_path": f"/Workspace/Users/{user_email}"  # Pasta do usuário
        }
        
        cmd = [
            "databricks", "api", "post",
            "/api/2.0/lakeview/dashboards",
            "--json", json.dumps(create_payload),
            "--profile", profile
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            response = json.loads(result.stdout)
            dashboard_id = response.get("dashboard_id", "")
            if dashboard_id:
                print_success(f"Dashboard criado: {dashboard_display_name}")
                dashboard_url = f"{host}/embed/dashboardsv3/{dashboard_id}"
                
                # Publicar o dashboard
                publish_payload = {
                    "embed_credentials": True,
                    "warehouse_id": warehouse_id
                }
                publish_cmd = [
                    "databricks", "api", "post",
                    f"/api/2.0/lakeview/dashboards/{dashboard_id}/published",
                    "--json", json.dumps(publish_payload),
                    "--profile", profile
                ]
                subprocess.run(publish_cmd, capture_output=True, text=True)
                print_success("Dashboard publicado")
                
                return dashboard_url
        else:
            print_warning(f"Erro ao criar dashboard: {result.stderr[:200]}")
        
        return ""
        
    except json.JSONDecodeError as e:
        print_error(f"Erro ao parsear JSON do dashboard: {e}")
        return ""
    except Exception as e:
        print_error(f"Erro ao criar dashboard: {e}")
        return ""


def wait_for_app_compute(profile: str, app_name: str, target_state: str = "RUNNING", max_wait: int = 300) -> bool:
    """Aguarda o compute do app atingir o estado desejado"""
    start_time = time.time()
    check_interval = 10
    
    while time.time() - start_time < max_wait:
        result = subprocess.run(
            ["databricks", "apps", "get", app_name, "--profile", profile],
            capture_output=True, text=True
        )
        
        if result.returncode == 0:
            try:
                app_data = json.loads(result.stdout)
                compute_state = app_data.get("compute_status", {}).get("state", "")
                
                if compute_state == target_state:
                    return True
                elif compute_state in ["FAILED", "ERROR"]:
                    print_warning(f"Compute em estado de erro: {compute_state}")
                    return False
                
                print_info(f"  Compute state: {compute_state}... aguardando {target_state}")
            except:
                pass
        
        time.sleep(check_interval)
    
    print_warning(f"Timeout aguardando compute atingir {target_state}")
    return False


def upload_sample_pdfs(profile: str, catalog: str, schema: str) -> bool:
    """Faz upload dos PDFs de exemplo para o Volume"""
    project_root = Path(__file__).parent
    pdfs_dir = project_root / "pdfs"
    
    if not pdfs_dir.exists():
        print_warning(f"Diretório de PDFs não encontrado: {pdfs_dir}")
        return False
    
    pdf_files = list(pdfs_dir.glob("*.pdf"))
    if not pdf_files:
        print_warning("Nenhum PDF encontrado no diretório pdfs/")
        return False
    
    volume_path = f"/Volumes/{catalog}/{schema}/files"
    
    for pdf_file in pdf_files[:5]:  # Upload apenas os 5 primeiros para teste
        print_info(f"  Uploading {pdf_file.name}...")
        cmd = [
            "databricks", "fs", "cp",
            str(pdf_file),
            f"dbfs:{volume_path}/{pdf_file.name}",
            "--profile", profile,
            "--overwrite"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print_success(f"  {pdf_file.name} uploaded")
        else:
            print_warning(f"  Falha ao fazer upload de {pdf_file.name}")
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Contract Extract App - Setup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
    # Ambiente de desenvolvimento
    python setup.py --profile adb-workspace --catalog dev_catalog --warehouse-id abc123 --env dev

    # Ambiente de produção
    python setup.py --profile adb-workspace --catalog prod_catalog --warehouse-id xyz789 --env prod

    # Com endpoint de agente para chat
    python setup.py --profile adb-workspace --catalog prod_catalog --warehouse-id xyz789 --env prod \\
        --agent-endpoint mas-abc123-endpoint

O script irá:
  1. Criar secrets no Databricks (scope: contract-extract-{env})
  2. Criar schema e volume no Unity Catalog
  3. Criar tabelas (contract_track, contract_parsed, contract_extract, contract_template, contract_compliance)
  4. Criar funções SQL (extração com IA e validação de compliance)
  5. Fazer deploy do Bundle (app + jobs + dashboard)
  6. Conceder permissões ao Service Principal do App
        """
    )
    
    parser.add_argument("--profile", "-p", required=True, help="Profile do Databricks CLI")
    parser.add_argument("--catalog", "-c", required=True, help="Nome do Unity Catalog")
    parser.add_argument("--schema", "-s", default="contract_pdf", help="Schema (default: contract_pdf)")
    parser.add_argument("--warehouse-id", "-w", required=True, help="ID do SQL Warehouse")
    parser.add_argument("--env", "-e", default="dev", choices=["dev", "staging", "prod"], 
                       help="Ambiente (default: dev)")
    parser.add_argument("--app-name", "-a", default="contract-extract",
                       help="Nome base do app (default: contract-extract)")
    parser.add_argument("--scope-prefix", default="contract-extract",
                       help="Prefixo do scope de secrets (default: contract-extract)")
    parser.add_argument("--agent-endpoint", default="mas-f2118e18-endpoint", help="Endpoint do Multi-Agent para chat")
    parser.add_argument("--audio-endpoint", default="seu_whisper_endpoint", help="Endpoint do Whisper para transcrição")
    parser.add_argument("--secret-scope", default="", help="Scope com PAT para Genie")
    parser.add_argument("--secret-key", default="", help="Key do PAT no scope")
    parser.add_argument("--target", "-t", help="Target do deploy (default: mesmo que --env)")
    parser.add_argument("--skip-secrets", action="store_true", help="Pular criação de secrets")
    parser.add_argument("--skip-tables", action="store_true", help="Pular criação de tabelas")
    parser.add_argument("--skip-deploy", action="store_true", help="Pular deploy do bundle")
    parser.add_argument("--skip-permissions", action="store_true", help="Pular configuração de permissões")
    parser.add_argument("--upload-samples", action="store_true", help="Fazer upload dos PDFs de exemplo")
    parser.add_argument("--create-genie", action="store_true", help="Criar Genie Space para consultas")
    
    args = parser.parse_args()
    
    # Target defaults to env
    target = args.target or args.env
    scope = f"{args.scope_prefix}-{args.env}"
    app_name = f"{args.app_name}-{target}"
    
    total_steps = 8
    current_step = 0
    
    # Variáveis para armazenar resultados do deploy
    job_id = ""
    dashboard_url = ""
    
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}  Contract Extract App - Setup ({args.env.upper()}){Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"\n  Environment: {Colors.CYAN}{args.env}{Colors.END}")
    print(f"  Profile:     {args.profile}")
    print(f"  Catalog:     {args.catalog}")
    print(f"  Schema:      {args.schema}")
    print(f"  Warehouse:   {args.warehouse_id}")
    print(f"  Scope:       {Colors.CYAN}{scope}{Colors.END}")
    print(f"  App Name:    {Colors.CYAN}{app_name}{Colors.END}")
    
    # Step 1: Verificar CLI
    current_step += 1
    print_step(current_step, total_steps, "Verificando Databricks CLI...")
    if not check_databricks_cli():
        print_error("Databricks CLI não encontrado! Instale com: pip install databricks-cli")
        sys.exit(1)
    print_success("Databricks CLI encontrado")
    
    # Step 2: Configurar Secrets
    current_step += 1
    print_step(current_step, total_steps, f"Configurando Databricks Secrets ({scope})...")
    if args.skip_secrets:
        print_warning("Pulando (--skip-secrets)")
    else:
        config = {
            "warehouse_id": args.warehouse_id, 
            "catalog": args.catalog, 
            "schema": args.schema,
        }
        setup_secrets(args.profile, scope, config)
    
    # Step 3: Criar tabelas
    current_step += 1
    print_step(current_step, total_steps, "Criando tabelas no Unity Catalog...")
    if args.skip_tables:
        print_warning("Pulando (--skip-tables)")
    else:
        create_tables(args.profile, args.warehouse_id, args.catalog, args.schema)
    
    # Step 4: Preparar e criar App (antes do bundle deploy)
    current_step += 1
    print_step(current_step, total_steps, f"Preparando App ({app_name})...")
    if args.skip_deploy:
        print_warning("Pulando (--skip-deploy)")
    else:
        # Gerar app.yaml primeiro
        generate_app_yaml(
            args.catalog, args.schema, args.warehouse_id, args.env,
            args.agent_endpoint, args.audio_endpoint,
            args.secret_scope or scope, args.secret_key or "genie_pat",
            "", ""  # job_id e dashboard_url serão preenchidos depois
        )
        
        # Criar o app se não existir (necessário antes do bundle deploy)
        print_info(f"Verificando/criando app '{app_name}'...")
        result = subprocess.run(
            ["databricks", "apps", "get", app_name, "--profile", args.profile],
            capture_output=True, text=True
        )
        if result.returncode != 0 or "does not exist" in result.stderr:
            print_info(f"Criando app '{app_name}'...")
            create_result = subprocess.run(
                ["databricks", "apps", "create", app_name, "--profile", args.profile],
                capture_output=True, text=True
            )
            if create_result.returncode == 0:
                print_success(f"App '{app_name}' criado")
                time.sleep(5)
            else:
                print_warning(f"Não foi possível criar app: {create_result.stderr[:100]}")
        else:
            print_success(f"App '{app_name}' já existe")
    
    # Step 5: Build Frontend e Deploy Bundle
    current_step += 1
    print_step(current_step, total_steps, f"Build do Frontend e Deploy do Bundle (target: {target})...")
    if args.skip_deploy:
        print_warning("Pulando (--skip-deploy)")
    else:
        # Build do frontend primeiro
        print_info("Fazendo build do frontend React...")
        if not build_frontend():
            print_warning("Build do frontend falhou, continuando com versão existente...")
        
        # Deploy do bundle (sincroniza arquivos para o workspace)
        if deploy_bundle(args.profile, target, args.catalog, args.schema, args.warehouse_id,
                        args.agent_endpoint, args.audio_endpoint,
                        args.secret_scope or scope, args.secret_key or "genie_pat"):
            print_success("Bundle deployado (arquivos sincronizados)")
            
            # Buscar job_id após deploy
            print_info("Buscando ID do job...")
            job_id = get_job_id(args.profile, "contracts-extract")
            
            # Criar dashboard Lakeview dinamicamente (com catalog/schema corretos)
            print_info("Criando/atualizando dashboard Lakeview...")
            dashboard_url = create_lakeview_dashboard(args.profile, args.warehouse_id, args.catalog, args.schema, args.env)
            
            if job_id:
                print_success(f"Job ID: {job_id}")
            if dashboard_url:
                print_success(f"Dashboard URL: {dashboard_url}")
            
            # Atualizar app.yaml com os IDs e re-deploy bundle
            if job_id or dashboard_url:
                generate_app_yaml(
                    args.catalog, args.schema, args.warehouse_id, args.env,
                    args.agent_endpoint, args.audio_endpoint,
                    args.secret_scope or scope, args.secret_key or "genie_pat",
                    job_id, dashboard_url
                )
                print_info("Re-sincronizando bundle com job_id e dashboard_url...")
                deploy_bundle(args.profile, target, args.catalog, args.schema, args.warehouse_id,
                             args.agent_endpoint, args.audio_endpoint,
                             args.secret_scope or scope, args.secret_key or "genie_pat")
            
            # Deploy do App (separado do bundle)
            # Obter o source code path
            user_result = subprocess.run(
                ["databricks", "current-user", "me", "--profile", args.profile],
                capture_output=True, text=True
            )
            if user_result.returncode == 0:
                try:
                    user_data = json.loads(user_result.stdout)
                    user_email = user_data.get("userName", "")
                    bundle_name = "contract-extract-app"
                    source_code_path = f"/Workspace/Users/{user_email}/.bundle/{bundle_name}/{target}/files/app"
                    
                    print_info(f"Fazendo deploy do app '{app_name}'...")
                    print_info(f"  Source: {source_code_path}")
                    
                    # Deploy do app
                    deploy_result = subprocess.run(
                        ["databricks", "apps", "deploy", app_name, 
                         "--source-code-path", source_code_path,
                         "--profile", args.profile],
                        capture_output=True, text=True
                    )
                    
                    if deploy_result.returncode == 0:
                        print_success(f"App '{app_name}' deployado!")
                    else:
                        print_warning(f"Deploy do app: {deploy_result.stderr[:150]}")
                except Exception as e:
                    print_warning(f"Erro ao fazer deploy do app: {e}")
        else:
            print_warning("Bundle deploy pode ter falhado")
    
    # Step 6: Conceder permissões ao App
    current_step += 1
    print_step(current_step, total_steps, f"Concedendo permissões ao App...")
    if args.skip_permissions or args.skip_deploy:
        print_warning("Pulando (--skip-permissions ou --skip-deploy)")
    else:
        sp_id = get_app_service_principal(args.profile, app_name)
        if sp_id:
            grant_app_permissions(args.profile, args.warehouse_id, args.catalog, args.schema, sp_id, scope)
        else:
            print_warning("Não foi possível obter o Service Principal. Configure manualmente as permissões.")
    
    # Step 7: Criar Genie Space (opcional)
    current_step += 1
    print_step(current_step, total_steps, "Criando Genie Space...")
    genie_space_id = ""
    if args.create_genie:
        genie_space_id = create_genie_space(args.profile, args.warehouse_id, args.catalog, args.schema, args.env)
        if genie_space_id:
            print_success(f"Genie Space pronto: {genie_space_id}")
    else:
        print_info("Pulando (use --create-genie para criar)")
    
    # Step 8: Upload de PDFs de exemplo (opcional)
    current_step += 1
    print_step(current_step, total_steps, "Upload de PDFs de exemplo...")
    if args.upload_samples:
        upload_sample_pdfs(args.profile, args.catalog, args.schema)
    else:
        print_info("Pulando (use --upload-samples para fazer upload)")
    
    # Final
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.GREEN}{Colors.BOLD}  ✅ Setup concluído! ({args.env.upper()}){Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"""
  Recursos criados:
    - Schema: {args.catalog}.{args.schema}
    - Volume: {args.catalog}.{args.schema}.files
    - Tabelas:
      • {args.catalog}.{args.schema}.contract_track
      • {args.catalog}.{args.schema}.contract_parsed
      • {args.catalog}.{args.schema}.contract_extract
      • {args.catalog}.{args.schema}.contract_template
      • {args.catalog}.{args.schema}.contract_compliance
    - Funções SQL:
      • SUMMARIZE_CONTRACT_DATA
      • EXTRACT_CONTRACT_DATA
      • CHECK_ITEM_COMPLIANCE
    - Dashboard: {dashboard_url if dashboard_url else 'Não criado'}
    - Genie Space: {genie_space_id if genie_space_id else 'Não criado (use --create-genie)'}

  Próximos passos:
    1. Acesse o App em: Compute → Apps → {app_name}
    2. Faça upload de contratos PDF
    3. Aguarde o processamento automático (trigger por arquivo)
    4. Visualize os dados extraídos no Dashboard
    {f'5. Consulte via Genie em: Data Intelligence → Genie → Contract Extract - {args.env.upper()}' if genie_space_id else ''}

  Para redeploy do app (após alterar código): ./deploy.sh [dev|prod]

  Para criar o Genie Space (consultas em linguagem natural):
    python setup.py --profile {args.profile} --catalog {args.catalog} \\
        --warehouse-id {args.warehouse_id} --env {args.env} \\
        --skip-secrets --skip-tables --skip-deploy --create-genie

  Para fazer upload de PDFs de exemplo:
    python setup.py --profile {args.profile} --catalog {args.catalog} \\
        --warehouse-id {args.warehouse_id} --env {args.env} \\
        --skip-secrets --skip-tables --skip-deploy --upload-samples
    """)


if __name__ == "__main__":
    main()

