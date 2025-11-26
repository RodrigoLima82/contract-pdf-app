from fastapi import FastAPI, File, UploadFile
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from pydantic import BaseModel
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole
from typing import Optional
import pandas as pd
import os, requests, re, io
import base64
import databricks.sql as dbsql

import mlflow
import mlflow.deployments

class ChatRequest(BaseModel):
    text: str
    chat_history: list

class ChatRequestAudio(BaseModel):
     audio: str
     chat_history: list


app = FastAPI()

# Configure CORS - allow localhost for development and Databricks Apps for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (includes localhost and Databricks Apps)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load all env variables
load_dotenv()
server_hostname = os.getenv("DATABRICKS_HOST")
http_path       = os.getenv("DATABRICKS_HTTP_PATH")
volume_path     = os.getenv("VOLUME_PATH")
llm_endpoint    = os.getenv("LLM_ENDPOINT")
audio_endpoint  = os.getenv("AUDIO_ENDPOINT")
agent_endpoint  = os.getenv("AGENT_ENDPOINT")
catalog         = os.getenv("CATALOG")
schema          = os.getenv("DATABASE")
extract_job_id  = os.getenv("EXTRACT_JOB_ID")
dashboard_id    = os.getenv("DASHBOARD_ID", "")

# Build dashboard URL using DATABRICKS_HOST (auto-injected by Databricks Apps) and DASHBOARD_ID
if dashboard_id and server_hostname:
    dashboard_url = f"{server_hostname}/dashboardsv3/{dashboard_id}/published"
else:
    dashboard_url = ""

# Lazy initialization of workspace_client to avoid unnecessary API calls during startup
workspace_client = None

def get_workspace_client():
    """Lazy initialization of workspace_client for Databricks Apps"""
    global workspace_client
    if workspace_client is None:
        try:
            # In Databricks Apps, WorkspaceClient uses OAuth M2M automatically
            # Suppress verbose logging to avoid permission checks on data-rooms
            import logging
            logging.getLogger("databricks.sdk").setLevel(logging.ERROR)
            
            workspace_client = WorkspaceClient()
            print(f"🚀 Initialized WorkspaceClient (OAuth M2M)")
        except Exception as e:
            print(f"⚠️ Warning during WorkspaceClient initialization: {e}")
            workspace_client = WorkspaceClient()
    return workspace_client

print(f"🚀 Running in Databricks Apps - OAuth M2M authentication")

# Detect the correct path for static files
import os
from pathlib import Path

# Try multiple possible locations for the frontend build
possible_paths = [
    Path(__file__).parent.parent / "frontend" / "build",  # Local/relative path
    Path("/app/python/source_code/frontend/build"),        # Databricks Apps deployed path
]

current_dir = None
static_dir = None

for path in possible_paths:
    if path.exists():
        current_dir = path.parent.parent
        static_dir = path
        break

if static_dir and static_dir.exists():
    # Mount static files (CSS, JS, images, etc.)
    static_subdir = static_dir / "static"
    if static_subdir.exists():
        app.mount("/static", StaticFiles(directory=str(static_subdir)), name="static")
        print(f"✅ Static files mounted from: {static_dir}")
else:
    print(f"⚠️ Frontend build directory not found")
    # Set a default for current_dir to avoid errors
    current_dir = Path(__file__).parent.parent

# Helper function to get SQL connection token (not needed - using WorkspaceClient SQL API)
def get_sql_token():
    """Get token for SQL Warehouse connection - using OAuth M2M via WorkspaceClient"""
    try:
        client = get_workspace_client()
        
        # Try multiple ways to get the token
        # Method 1: Try api_client.token()
        if hasattr(client.api_client, 'token'):
            token = client.api_client.token()
            if token:
                return token
        
        # Method 2: Try _token attribute
        if hasattr(client.api_client, '_token'):
            token = client.api_client._token
            token = token() if callable(token) else token
            if token:
                return token
        
        # Method 3: Try config.token
        if hasattr(client, 'config') and hasattr(client.config, 'token'):
            token = client.config.token
            if token:
                return token
        
        # Method 4: Try oauth_token from config
        if hasattr(client, 'config') and hasattr(client.config, 'oauth_token'):
            token = client.config.oauth_token
            if token:
                return token
        
        return None
        
    except Exception as e:
        print(f"❌ Erro ao obter token: {e}")
        return None

# Dicionário global para armazenar áudios temporários
temp_audio_storage = {}

# =======================================================================
def transcribe_audio(audio_data, audio_id):
    """
    Nota: A transcrição de áudio requer que o endpoint Databricks consiga acessar
    o arquivo via URL pública. Em ambiente local (localhost), isso não é possível.
    
    Soluções:
    1. Deploy em produção com URL pública
    2. Usar ngrok/tunneling para expor localhost
    3. Upload para S3/Azure Blob e usar URL pública
    """
    # Limpar áudio do cache
    if audio_id in temp_audio_storage:
        del temp_audio_storage[audio_id]
    
    return "🎤 A transcrição de áudio não está disponível em ambiente local. O endpoint Databricks precisa de uma URL pública acessível. Por favor, use o chat de texto para fazer suas perguntas."

# =======================================================================
def get_direct_llm_answer(message, info):
    """Chama o agent endpoint usando MLflow deployments client"""
    # Converter info para string se for pandas Series
    info_str = str(info) if not isinstance(info, str) else info
    
    system_content = f"""Você é um assistente jurídico especializado em análise de contratos.

Use as seguintes informações como fonte de dados para responder à pergunta do usuário:
{info_str[:2000]}

Regras:
- Sempre responda em Português
- Use os dados fornecidos sobre contratos para embasar suas respostas
- Seja claro, objetivo e profissional
- Destaque informações importantes como valores, prazos, partes envolvidas e cláusulas relevantes
- Se os dados não forem suficientes para responder, mencione isso"""

    # Formato correto para agent endpoints (espera 'input' como array)
    client = mlflow.deployments.get_deploy_client("databricks")
    
    query = {
        "input": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": message}
        ]
    }
    
    try:
        response = client.predict(
            endpoint=agent_endpoint,
            inputs=query
        )
        
        print(f"🔍 Resposta do endpoint: {response}")
        
        # Extrair resposta do formato do agent endpoint
        if isinstance(response, dict):
            # Formato: response['output'][0]['content'][0]['text']
            output = response.get('output', [])
            if output and len(output) > 0:
                content = output[0].get('content', [])
                if content and len(content) > 0:
                    text = content[0].get('text', '')
                    if text:
                        return text
            
            # Fallback: tentar formato antigo com 'messages'
            messages = response.get('messages', [])
            for msg in messages:
                if msg.get('id', '').startswith('run--'):
                    return msg.get('content', '⚠️ Resposta vazia do modelo.')
            
            # Se não encontrar, tentar pegar a última mensagem do assistant
            for msg in reversed(messages):
                if msg.get('role') == 'assistant':
                    return msg.get('content', '⚠️ Resposta vazia do modelo.')
        
        return str(response)
    
    except Exception as e:
        print(f"❌ Erro ao chamar agent endpoint: {e}")
        return f"⚠️ Erro ao processar sua pergunta: {str(e)}"

# =======================================================================
def get_genie_answer(message):
    # Get token for SQL connection
    token = get_sql_token()
    
    if token:
        conn = dbsql.connect(
            server_hostname=server_hostname,
            http_path=http_path,
            access_token=token
        )
    else:
        conn = dbsql.connect(
            server_hostname=server_hostname,
            http_path=http_path
        )
    
    cursor = conn.cursor()
    query = f"""select {catalog}.{schema}.chat_genie("{message}", "no relevant history") as genie_result """
    cursor.execute(query)
    results = cursor.fetchall()

    columns = [desc[0] for desc in cursor.description]
    df = pd.DataFrame(results, columns=columns)
    data = df.to_dict(orient='records')[0]['genie_result']
    
    cursor.close()
    conn.close()   

    formatted = query_model_format(data)

    return formatted

# =======================================================================
def query_model_format(text_to_format):
    
    prompt = """
        Format the message in a clear and organized way. 
        Nerver answer with title or subtitle tag.
        The output need to be using 12 size font.
        Do not need to repeat the question on the answer.
        Always answer in Portuguese.       
       """

    messages = [
        {
            "role": "system",
            "content": prompt
        },
        { 
            "role": "user", 
            "content": text_to_format 
        }
    ]

    messages = [ChatMessage.from_dict(message) for message in messages]
    response = get_workspace_client().serving_endpoints.query(
        name=llm_endpoint,
        messages=messages,
        max_tokens=500
    )
    return response.choices[0].message.content   


# =======================================================================
def get_all_pdf_volume():
    print(f"🔑 Obtendo token SQL...")
    token = get_sql_token()
    print(f"🔑 Token obtido: {'✅ Sim' if token else '❌ Não'}")
    
    # Use WorkspaceClient SQL execution instead of databricks-sql-connector
    # This works better with OAuth M2M in Databricks Apps
    query = f"""SELECT file_name, 
                       file_path,
                       type, 
                       FORMAT_NUMBER(ROUND(size / 1024, 2), 0) AS size,
                       CASE WHEN processed = 'S' THEN '✅' ELSE '❌' END AS processed,
                       COALESCE(DATE_FORMAT(upload_time, 'dd/MM/yyyy'), '-') AS upload_time,
                       COALESCE(DATE_FORMAT(processed_time, 'dd/MM/yyyy'), '-') AS processed_time
                  FROM {catalog}.{schema}.contract_track
                 ORDER BY upload_time DESC, processed_time DESC"""
    
    print(f"📝 Executando query via WorkspaceClient SQL...")
    
    client = get_workspace_client()
    
    # Extract warehouse_id from http_path
    warehouse_id = http_path.split('/')[-1]
    print(f"🏭 Warehouse ID: {warehouse_id}")
    
    # Execute SQL statement
    from databricks.sdk.service.sql import StatementParameterListItem
    
    try:
        response = client.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=query,
            catalog=catalog,
            schema=schema
        )
        
        print(f"✅ Query executada com sucesso")
        
    except Exception as e:
        print(f"❌ Erro ao executar query: {e}")
        return pd.DataFrame()
    
    # Parse results
    if response.result and response.result.data_array:
        columns = [col.name for col in response.manifest.schema.columns]
        data = response.result.data_array
        df = pd.DataFrame(data, columns=columns)
        print(f"✅ Resultados: {len(df)} linhas")
    else:
        print("⚠️ Nenhum resultado retornado")
        df = pd.DataFrame()
    
    return df

# =======================================================================
def get_all_pdf_info(pdf: Optional[str] = ""):
    # Use WorkspaceClient SQL execution instead of databricks-sql-connector
    query = f"""SELECT path, 
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
                 FROM {catalog}.{schema}.contract_extract
                 WHERE 1=1"""
    
    if pdf != "":
        query += f" AND path LIKE CONCAT('%', REPLACE(REPLACE('{pdf}', '%20', ' '),'+', ' '), '%')"

    client = get_workspace_client()
    warehouse_id = http_path.split('/')[-1]
    
    response = client.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=query,
        catalog=catalog,
        schema=schema
    )
    
    # Parse results
    if response.result and response.result.data_array:
        columns = [col.name for col in response.manifest.schema.columns]
        data = response.result.data_array
        df = pd.DataFrame(data, columns=columns)
    else:
        df = pd.DataFrame()

    return df


# =======================================================================
# Health check endpoint
# =======================================================================
@app.get("/health")
@app.get("/api/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "app": "contract-extract",
        "catalog": catalog,
        "schema": schema
    }

# =======================================================================
# Root endpoint - serve React app
# =======================================================================
@app.get("/")
async def serve_frontend():
    """Serve the React frontend index.html"""
    if static_dir:
        index_path = static_dir / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
    
    return {"error": "Frontend not found", "static_dir": str(static_dir) if static_dir else "None"}

# =======================================================================
# =======================================================================
@app.post("/chat/")
async def chat_endpoint(chat_request: ChatRequest):
    message = chat_request.text
    chat_history = chat_request.chat_history
    
    #result = get_genie_answer(message) # Caso queira chamar o Genie API, descomentar
    pdf_info = get_all_pdf_info()
    
    # Preparar contexto: usar o DataFrame inteiro ou coluna específica se existir
    if not pdf_info.empty:
        if 'summarize' in pdf_info.columns:
            # Concatenar todos os resumos em um texto
            context = "\n\n".join(pdf_info['summarize'].dropna().tolist())
        else:
            # Usar o DataFrame inteiro convertido para string
            context = pdf_info.to_string(max_rows=20)
    else:
        context = "Nenhum contrato encontrado no banco de dados."
    
    # Usar diretamente o LLM endpoint ao invés de tentar o agent endpoint primeiro
    result = get_direct_llm_answer(message, context)
    chat_history.append([message, result])

    return {"response": result, "chat_history": chat_history}

# =======================================================================
@app.get("/api/config")
async def get_config():
    """Return frontend configuration including dashboard URL"""
    return {
        "dashboard_url": dashboard_url,
        "catalog": catalog,
        "schema": schema
    }

# =======================================================================
@app.get("/api/temp_audio/{audio_id}")
async def serve_temp_audio(audio_id: str):
    """Serve áudio temporário armazenado em memória"""
    if audio_id not in temp_audio_storage:
        return Response(status_code=404, content="Audio not found")
    
    audio_bytes = temp_audio_storage[audio_id]
    return Response(content=audio_bytes, media_type="audio/mpeg")

# =======================================================================
@app.post("/chat_audio/")
async def chat_audio_endpoint(chat_request: ChatRequestAudio):
    audio = chat_request.audio
    chat_history = chat_request.chat_history

    # Extrair base64 do áudio
    audio_data = audio.split(",")[-1]
    audio_bytes = base64.b64decode(audio_data)
    
    # Gerar ID único para o áudio
    import time
    import uuid
    audio_id = f"{int(time.time())}_{uuid.uuid4().hex[:8]}"
    
    # Armazenar áudio temporariamente
    temp_audio_storage[audio_id] = audio_bytes
    
    # Transcrever usando URL temporária
    transcription = transcribe_audio(audio_data, audio_id)

    return {"response": transcription, "chat_history": chat_history}


# =======================================================================
@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    
    # Read file into bytes
    file_bytes = file.file.read()
    binary_data = io.BytesIO(file_bytes)

    # Specify volume path and upload
    file_path = f"{volume_path}/{file.filename}"

    print(file_path)
    get_workspace_client().files.upload(file_path, binary_data, overwrite=True)

    return {"filename": file.filename}
    
# =======================================================================
@app.get("/api/data")
async def get_extract_data():
    try:
        print("📊 Chamando get_all_pdf_volume()...")
        response = get_all_pdf_volume()
        print(f"✅ Query retornou {len(response)} linhas")
        
        # Verificar se o DataFrame está vazio ou não tem colunas
        if response.empty:
            print("⚠️ Nenhum dado encontrado na tabela contract_track")
            return []
        
        # Verificar se as colunas esperadas existem
        expected_cols = ["file_name","type","size","processed","file_path","upload_time","processed_time"]
        missing_cols = [col for col in expected_cols if col not in response.columns]
        
        if missing_cols:
            print(f"⚠️ Colunas faltando: {missing_cols}")
            print(f"📋 Colunas disponíveis: {list(response.columns)}")
            return []
        
        df = response.loc[:, expected_cols]
        df_dict = df.to_dict(orient='records')
        print(f"✅ Retornando {len(df_dict)} registros")
        return df_dict
    except Exception as e:
        import traceback
        print(f"❌ ERRO em /api/data: {str(e)}")
        print(f"❌ Traceback completo:\n{traceback.format_exc()}")
        # Retorna array vazio ao invés de erro para não quebrar o frontend
        return []


# =======================================================================
@app.get("/api/all_data")
async def get_extract_all_data(pdf: Optional[str] = ""):
    try:
        response = get_all_pdf_info(pdf)
        df = response.loc[:, ["tipo_contrato", "nome_contrato", "contratante", "contratado", "valor_total", "moeda", 
                              "data_assinatura", "data_inicio_vigencia", "data_fim_vigencia", "prazo_vigencia", 
                              "objeto_contrato", "forma_pagamento", "condicoes_pagamento", "clausula_rescisao", 
                              "multa_rescisao", "garantias", "confidencialidade", "foro", "observacoes", "summarize"]]
        df_dict = df.to_dict(orient='records')
        return df_dict
    except Exception as e:
        print(f"❌ Erro em /api/all_data: {str(e)}")
        return []

# =======================================================================
@app.get("/api/pdf")
async def get_pdf(pdf: Optional[str] = ""):
    # Get token for API requests
    token = get_sql_token()
    if not token:
        return Response(content="Authentication token not available", status_code=401)
    
    headers = {"Authorization": "Bearer " + token}    

    response = get_all_pdf_info(pdf)
    df = response.loc[:, ["volume"]]
    df_dict = df.to_dict(orient='records')

    url = f"{server_hostname}/api/2.0/fs/files{df_dict[0]['volume']}"
    print(url)
    r = requests.get(url, headers=headers)

    if r.status_code == 200:
        return Response(r.content, media_type="application/pdf")
    else:
        return r.status_code
    

# =======================================================================
@app.get("/api/summarize")
async def get_extract_summary(pdf: Optional[str] = ""):
    response = get_all_pdf_info(pdf)
    df = response.loc[:, ["summarize"]]
    summarize_text = df["summarize"].iloc[0] if not df.empty else ""
    return summarize_text

# =======================================================================
@app.get("/api/extract")
def start_job(pdf: Optional[str] = ""):
    run = get_workspace_client().jobs.run_now(
        job_id=extract_job_id,
        notebook_params={
            "catalog": catalog,
            "database": schema,
            "trackTableName": "contract_track",
            "parsedTableName": "contract_parsed",
            "extractTableName": "contract_extract",
            "sourcePDFPath": volume_path+"/"+pdf,
            "limit": "100"
        }
    )
    return {"run_id": run.run_id}

# =======================================================================
# Catch-all route for React Router (SPA routing)
# =======================================================================
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """Serve index.html for all other routes (React Router SPA)"""
    # Don't intercept API routes
    if full_path.startswith("api/") or full_path.startswith("health"):
        return {"error": "Not found"}
    
    if static_dir:
        index_path = static_dir / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
    
    return {"error": "Frontend not found", "static_dir": str(static_dir) if static_dir else "None"}

# =======================================================================
print("🚀 FastAPI app initialized with static file serving")