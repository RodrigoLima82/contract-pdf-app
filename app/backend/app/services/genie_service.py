"""
Serviço de integração com Multi-Agent ou Genie
Prioridade: AGENT_ENDPOINT > GENIE_SPACE_ID

Se AGENT_ENDPOINT configurado: usa Multi-Agent Serving
Se não, usa GENIE_SPACE_ID para consultas
"""
import json
import logging
import os
import time
import asyncio
import requests
from typing import Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from base64 import b64encode

logger = logging.getLogger(__name__)

# Thread pool dedicado para chamadas HTTP síncronas
_executor = ThreadPoolExecutor(max_workers=20, thread_name_prefix="genie_")


class GenieService:
    """
    Serviço para integração com Multi-Agent Endpoint ou Genie Space
    
    Prioridade:
    1. AGENT_ENDPOINT - Se configurado, usa o Multi-Agent Serving
    2. GENIE_SPACE_ID - Se configurado, usa o Genie Space
    """
    
    # Cache de token (compartilhado entre instâncias)
    _cached_token: Optional[str] = None
    _token_expires_at: float = 0
    
    def __init__(self):
        self.agent_endpoint = os.environ.get("AGENT_ENDPOINT", "").strip()
        self.space_id = os.environ.get("GENIE_SPACE_ID", "").strip()
        
        if self.agent_endpoint:
            logger.info(f"✅ Multi-Agent Endpoint configurado: {self.agent_endpoint}")
        elif self.space_id:
            logger.info(f"✅ Genie Space configurado: {self.space_id}")
        else:
            logger.warning("⚠️ Nem AGENT_ENDPOINT nem GENIE_SPACE_ID configurado! Chat pode não funcionar.")
    
    def _get_token(self) -> str:
        """Obtém token de autenticação via OAuth M2M com cache"""
        # Verificar se o token em cache ainda é válido (com 5 min de margem)
        if GenieService._cached_token and time.time() < GenieService._token_expires_at - 300:
            logger.debug("🔑 Usando token em cache")
            return GenieService._cached_token
        
        logger.info("🔑 Obtendo novo token OAuth...")
        
        # Obter credenciais do ambiente
        host = os.environ.get("DATABRICKS_HOST", "").strip()
        client_id = os.environ.get("DATABRICKS_CLIENT_ID", "").strip()
        client_secret = os.environ.get("DATABRICKS_CLIENT_SECRET", "").strip()
        
        if not all([host, client_id, client_secret]):
            # Fallback: tentar usar token direto
            token = os.environ.get("DATABRICKS_TOKEN", "").strip()
            if token:
                return token
            raise ValueError("Missing OAuth credentials in environment")
        
        if not host.startswith("http"):
            host = f"https://{host}"
        
        # Obter token OAuth
        token_url = f"{host.rstrip('/')}/oidc/v1/token"
        credentials = f"{client_id}:{client_secret}"
        auth_header = f"Basic {b64encode(credentials.encode()).decode()}"
        
        response = requests.post(
            token_url,
            headers={
                "Authorization": auth_header,
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data="grant_type=client_credentials&scope=all-apis",
            timeout=30
        )
        
        if not response.ok:
            raise Exception(f"Failed to get OAuth token: {response.status_code} {response.text}")
        
        token_data = response.json()
        GenieService._cached_token = token_data.get("access_token")
        
        # Calcular expiração (default 1 hora = 3600s)
        expires_in = token_data.get("expires_in", 3600)
        GenieService._token_expires_at = time.time() + expires_in
        
        logger.info(f"🔑 Token obtido, expira em {expires_in}s")
        return GenieService._cached_token
    
    def _get_host(self) -> str:
        """Retorna o host do Databricks"""
        host = os.environ.get("DATABRICKS_HOST", "").strip()
        if not host.startswith("http"):
            host = f"https://{host}"
        return host.rstrip("/")
    
    def _clean_agent_response(self, text: str) -> str:
        """
        Limpeza mínima da resposta do agent (apenas casos extremos).
        O system prompt já instrui o agente a não retornar tabelas e dados brutos.
        """
        import re
        
        logger.info(f"🧹 Limpando resposta (tamanho original: {len(text)} chars)")
        
        # PRIORIDADE MÁXIMA: Remover todo o reasoning e pegar apenas a resposta estruturada
        # Procurar por títulos estruturados em negrito/markdown que indicam início da resposta real
        structured_headers = [
            r'##\s*Riscos?\s+(Financeiros?|Jurídicos?|Operacionais?)',  # ## Riscos Financeiros
            r'\*\*Tipo\s+de\s+Contrato:?\*\*',  # **Tipo de Contrato:**
            r'##\s*Tipo\s+de\s+Contrato',  # ## Tipo de Contrato
            r'##\s*Análise\s+de\s+(Risco|Contrato)',  # ## Análise de Risco
            r'##\s*Resumo\s+do\s+Contrato',  # ## Resumo do Contrato
        ]
        
        for header_pattern in structured_headers:
            match = re.search(header_pattern, text, re.IGNORECASE)
            if match:
                # Encontrou um cabeçalho estruturado - pegar tudo a partir dele
                start_pos = match.start()
                logger.warning(f"⚠️ Removendo {start_pos} chars de reasoning antes da resposta estruturada!")
                text = text[start_pos:]
                break
        
        # Se não encontrou cabeçalho estruturado, procurar por padrão "| Tipo de Contrato: |"
        # que indica fim do reasoning e início de tabela/resposta
        if '| Tipo de Contrato: |' in text:
            parts = text.split('| Tipo de Contrato: |', 1)
            if len(parts) > 1:
                # Pegar apenas a parte depois
                logger.warning("⚠️ Removendo reasoning antes de '| Tipo de Contrato: |'")
                # Verificar se a segunda parte começa com título estruturado
                remaining = parts[1].strip()
                # Procurar próximo título markdown
                next_title = re.search(r'(##\s*[^\n]+|Riscos?\s+Financeiros?)', remaining)
                if next_title:
                    text = remaining[next_title.start():]
                else:
                    text = remaining
        
        # Remover tags XML/HTML
        text = re.sub(r'<[^>]+>.*?</[^>]+>', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remover separadores de tabelas markdown no início (|---::|---, etc)
        text = re.sub(r'^\|[\-:]+\|[\-:]+.*?\n', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\|+[\s\-:]+\|+.*?\n', '', text, flags=re.MULTILINE)
        
        # PRIORIDADE 1: Remover tabelas SQL inline (coladas com o texto)
        # Exemplo: | 0 | 1 |Com base... ou | | total_contratos | | 0 | 20 |Com base...
        # Pattern: captura tudo após o último pipe seguido de uma letra maiúscula (início de frase)
        pipe_inline_match = re.search(r'^[\|\s\d\w_]+\|([A-Z][^|]+.*)$', text, flags=re.DOTALL)
        if pipe_inline_match:
            logger.warning("⚠️ Removendo tabela SQL inline colada no início!")
            text = pipe_inline_match.group(1).strip()
        
        # PRIORIDADE 2: Remover tabelas SQL completas e linhas com pipes
        if '|' in text:
            # Verificar se há dados SQL (linhas com múltiplos pipes)
            has_sql_data = bool(re.search(r'\|\s*\|\s*\w+\s*\|', text))
            
            if has_sql_data:
                logger.warning("⚠️ Agent retornou tabelas SQL apesar das instruções!")
                
                # Remover todas as linhas que começam com pipes e números/campos
                # Exemplo: | | total_contratos | | 0 | 20 |
                text = re.sub(r'\|\s*\|[^\n]*\|\s*\d+\s*\|[^\n]*\|', '', text)
                
                # Remover linhas de tabelas com nomes de campos
                text = re.sub(r'\|\s*\|[^\n]*(nome_contrato|summarize|observacoes|total_contratos)[^\n]*\|', '', text)
                
                # Remover qualquer linha que comece com | |
                text = re.sub(r'^\|\s*\|[^\n]*\n', '', text, flags=re.MULTILINE)
        
        # PRIORIDADE 3: Remover pipes no início da resposta (caso mais simples)
        # Exemplo: | | total_contratos | | 0 | 20 |
        # Remove tudo até encontrar texto real sem pipes
        if text.startswith('|'):
            logger.warning("⚠️ Resposta começa com pipes!")
            # Procurar onde termina a parte com pipes e começa o texto real
            match = re.search(r'\|+[^\|]*\|+([^|].+)', text)
            if match:
                text = match.group(1).strip()
        
        # Fallback: Remover frases introdutórias completas
        intro_patterns = [
            r'^.*(Encontrei|Vou|Deixe-me|Aguarde|Aqui está|Segue).*?(informações|dados|resumo|análise).*?:\s*',
            r'^.*(Vou consultar|Deixe-me buscar|Aguarde enquanto).*?\.\s*',
        ]
        
        for pattern in intro_patterns:
            if re.search(pattern, text, re.IGNORECASE | re.DOTALL):
                logger.warning("⚠️ Agent incluiu frase introdutória!")
                text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
        
        # Remover linhas que são só pipes e separadores
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            stripped = line.strip()
            # Pular linhas que são só pipes, hífens e dois pontos
            if stripped and not re.match(r'^[\|\-:=\s]+$', stripped):
                cleaned_lines.append(line)
        text = '\n'.join(cleaned_lines)
        
        # Limpar múltiplas linhas vazias
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Limpar espaços extras
        text = text.strip()
        
        logger.info(f"✅ Resposta limpa (tamanho final: {len(text)} chars)")
        
        return text
    
    def _ask_agent_sync(self, question: str, context: str = "", messages_history: list = None) -> Dict[str, Any]:
        """
        [SYNC] Envia pergunta para o Multi-Agent Serving Endpoint.
        """
        try:
            logger.info(f"🤖 [Thread] Enviando pergunta ao Multi-Agent: {question[:100]}...")
            
            host = self._get_host()
            url = f"{host}/serving-endpoints/{self.agent_endpoint}/invocations"
            
            # System prompt com contexto dos contratos
            system_content = f"""Você é um assistente jurídico especializado em análise de contratos.

Use as seguintes informações como fonte de dados para responder à pergunta do usuário:
{context[:3000] if context else "Sem contexto disponível."}

Regras IMPORTANTES:
- Sempre responda em Português
- Use os dados fornecidos sobre contratos para embasar suas respostas
- Seja claro, objetivo e profissional
- Destaque informações importantes como valores, prazos, partes envolvidas e cláusulas relevantes
- SEMPRE use quebras de linha duplas (\n\n) para separar blocos de informação
- Mantenha a formatação limpa e legível com espaçamento adequado

⚠️ FORMATO DA RESPOSTA - SIGA RIGOROSAMENTE:

NÃO INCLUA NA SUA RESPOSTA:
❌ Reasoning ou explicação do seu processo de pensamento
❌ Repetição do conteúdo do contrato fornecido no contexto
❌ Frases introdutórias ("Vou consultar...", "Deixe-me buscar...", "Aguarde...")
❌ Frases de confirmação ("Encontrei as informações...", "Aqui está um resumo...")
❌ Frases contextuais ("Com base nos dados...", "De acordo com...")
❌ Dados brutos de consultas SQL ou tabelas markdown (com pipes |)
❌ Campos de banco de dados (nome_contrato, summarize, observacoes, etc)

✅ FORMATAÇÃO DA RESPOSTA:
- Use SEMPRE quebras de linha duplas entre seções (linha em branco)
- Para listas de itens, use quebra de linha simples entre cada item
- Para títulos use "## Título" ou texto seguido de dois pontos
- Para sub-itens use "**Negrito:** descrição"
- Separe diferentes contratos/entidades com linha em branco

EXEMPLO CORRETO:
"Com base na consulta à base de dados, aqui estão os códigos e valores dos contratos:

Contrato 1:
Código: Contract No. PSA-2024-0001
Valor: R$ 174.000,00

Contrato 2:
Código: Contract No. PSA-2024-0002
Valor: R$ 203.000,00

Total dos contratos: R$ 377.000,00

Os dois contratos são da série PSA-2024, sendo contratos sequenciais numerados como 0001 e 0002."

EXEMPLO CORRETO PARA RISCOS:
"## Riscos Financeiros

**Limite orçamentário:** Valor máximo de US$ 174.000,00 que não pode ser excedido

**Risco de custos adicionais:** Em caso de rescisão por inadimplemento..."

EXEMPLO ERRADO (NÃO FAÇA):
"• Código: XXX • Valor: YYY"  ❌ (itens colados sem quebra de linha)
"Contrato 1: Código: XXX Valor: YYY Contrato 2: ..." ❌ (sem espaçamento)

Lembre-se: COMECE DIRETO COM O CONTEÚDO, USE QUEBRAS DE LINHA ADEQUADAS!"""

            # Montar payload com histórico de mensagens
            input_messages = [{"role": "system", "content": system_content}]
            
            # Se há histórico, incluir no payload
            if messages_history:
                # Adicionar histórico de mensagens (user/assistant)
                for msg in messages_history:
                    role = msg.get("role")
                    content = msg.get("content", "")
                    
                    # Incluir apenas mensagens de user e assistant
                    if role in ["user", "assistant"] and content:
                        input_messages.append({"role": role, "content": content})
                
                logger.info(f"📚 Enviando {len(messages_history)} mensagens de histórico")
            else:
                # Sem histórico, apenas a pergunta atual
                input_messages.append({"role": "user", "content": question})
            
            payload = {"input": input_messages}
            
            # Retry com até 3 tentativas
            max_retries = 3
            
            for attempt in range(1, max_retries + 1):
                token = self._get_token()
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                
                response = requests.post(url, headers=headers, json=payload, timeout=60)
                
                if response.ok:
                    break
                
                logger.warning(f"⚠️ [Thread] Tentativa {attempt}/{max_retries} falhou: {response.status_code}")
                
                if response.status_code in [403, 500, 502, 503, 504] and attempt < max_retries:
                    if response.status_code == 403:
                        GenieService._cached_token = None
                        GenieService._token_expires_at = 0
                    time.sleep(1 * attempt)
                    continue
                else:
                    break
            
            if not response.ok:
                logger.error(f"❌ Agent API error: {response.status_code} - {response.text[:200]}")
                if response.status_code == 403:
                    return {
                        "success": False,
                        "error": "Agent API 403 Forbidden",
                        "message": "Sem permissão para chamar o endpoint do agente. No workspace Databricks, em Serving > seu endpoint, adicione o Service Principal do app (ou o usuário/token em uso) com permissão 'Can Query'."
                    }
                return {
                    "success": False,
                    "error": f"Agent API error: {response.status_code}",
                    "message": f"Erro ao processar sua pergunta (código {response.status_code})."
                }
            
            result = response.json()
            
            # Extrair resposta do agent
            message_content = ""
            
            if "output" in result and isinstance(result["output"], list):
                for output_item in result["output"]:
                    if output_item.get("role") == "assistant":
                        content_list = output_item.get("content", [])
                        
                        # Filtrar apenas a resposta final (ignorar reasoning)
                        output_texts = []
                        for content_item in content_list:
                            # Pular itens de reasoning/thinking
                            if content_item.get("type") in ["reasoning", "thinking", "tool_calls", "tool_use"]:
                                continue
                            
                            # Pegar apenas output_text que é a resposta final
                            if content_item.get("type") == "output_text":
                                text = content_item.get("text", "")
                                if text:
                                    output_texts.append(text)
                        
                        # Se houver múltiplos output_text, pegar apenas o último (resposta final)
                        if output_texts:
                            message_content = output_texts[-1]
                        else:
                            # Fallback: concatenar todos
                            for content_item in content_list:
                                if content_item.get("type") == "output_text":
                                    message_content += content_item.get("text", "")
            
            if not message_content:
                if "choices" in result and len(result["choices"]) > 0:
                    message_content = result["choices"][0].get("message", {}).get("content", "")
                else:
                    message_content = str(result)
            
            # Log da resposta bruta para debug
            logger.info(f"📝 Resposta bruta (primeiros 300 chars): {message_content[:300]}...")
            logger.info(f"📝 Resposta bruta (últimos 200 chars): ...{message_content[-200:]}")
            
            # Limpar tags internas e formatação estranha
            message_content = self._clean_agent_response(message_content)
            
            logger.info(f"✅ [Thread] Multi-Agent respondeu com sucesso ({len(message_content)} chars)")
            
            return {
                "success": True,
                "message": message_content,
                "source": "multi-agent"
            }
            
        except Exception as e:
            logger.error(f"❌ [Thread] Erro ao chamar Multi-Agent: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Erro ao processar sua pergunta: {str(e)}"
            }
    
    def _ask_genie_sync(self, question: str, max_wait_seconds: int = 120) -> Dict[str, Any]:
        """
        [SYNC] Envia pergunta ao Genie Space.
        """
        try:
            logger.info(f"🔮 [Thread] Enviando pergunta ao Genie: {question[:100]}...")
            
            host = self._get_host()
            token = self._get_token()
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # 1. Iniciar conversa
            start_url = f"{host}/api/2.0/genie/spaces/{self.space_id}/start-conversation"
            start_response = requests.post(
                start_url, 
                headers=headers, 
                json={"content": question},
                timeout=60
            )
            
            if not start_response.ok:
                raise Exception(f"Genie start-conversation error: {start_response.status_code}")
            
            start_data = start_response.json()
            conversation_id = start_data.get("conversation_id")
            message_id = start_data.get("message_id")
            
            if not conversation_id or not message_id:
                raise Exception(f"Resposta inválida do Genie: {start_data}")
            
            logger.info(f"📝 [Thread] Conversa iniciada: {conversation_id}")
            
            # 2. Aguardar processamento
            start_time = time.time()
            result = None
            
            while time.time() - start_time < max_wait_seconds:
                status_url = f"{host}/api/2.0/genie/spaces/{self.space_id}/conversations/{conversation_id}/messages/{message_id}"
                status_response = requests.get(status_url, headers=headers, timeout=30)
                
                if not status_response.ok:
                    time.sleep(2)
                    continue
                
                message_data = status_response.json()
                status = message_data.get("status")
                
                if status == "COMPLETED":
                    result = message_data
                    break
                elif status in ["FAILED", "CANCELLED", "ERROR"]:
                    error_msg = message_data.get("error", {}).get("message", "Unknown error")
                    raise Exception(f"Genie falhou: {error_msg}")
                
                time.sleep(2)
            
            if not result:
                raise Exception(f"Timeout aguardando resposta do Genie")
            
            # 3. Extrair resposta
            response_text = ""
            attachments = result.get("attachments", [])
            
            for attachment in attachments:
                if "text" in attachment:
                    text_content = attachment.get("text", {})
                    content = text_content.get("content", "")
                    if content:
                        response_text += content + "\n"
                elif "query" in attachment:
                    query_content = attachment.get("query", {})
                    description = query_content.get("description", "")
                    row_count = query_content.get("query_result_metadata", {}).get("row_count", 0)
                    if description:
                        response_text += f"\n{description}\n"
                    if row_count > 0:
                        response_text += f"📈 Encontrados {row_count} resultado(s).\n"
            
            if not response_text:
                reply = result.get("reply", {})
                response_text = reply.get("content", "")
            
            final_message = response_text.strip() or "Não consegui processar sua pergunta."
            
            return {
                "success": True,
                "message": final_message,
                "source": "genie"
            }
            
        except Exception as e:
            logger.error(f"❌ [Thread] Erro ao consultar Genie: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Erro ao consultar dados: {str(e)}"
            }
    
    async def ask(self, question: str, context: str = "", max_wait_seconds: int = 120) -> Dict[str, Any]:
        """
        Envia pergunta para o Multi-Agent ou Genie (sem histórico).
        
        Prioridade:
        1. AGENT_ENDPOINT - Se configurado
        2. GENIE_SPACE_ID - Fallback
        
        Args:
            question: Pergunta em linguagem natural
            context: Contexto adicional (ex: resumos dos contratos)
            max_wait_seconds: Tempo máximo de espera
            
        Returns:
            Dict com a resposta
        """
        loop = asyncio.get_event_loop()
        
        # Prioridade 1: Multi-Agent Endpoint
        if self.agent_endpoint:
            return await loop.run_in_executor(
                _executor, 
                self._ask_agent_sync, 
                question,
                context,
                None  # sem histórico
            )
        
        # Prioridade 2: Genie Space
        if self.space_id:
            return await loop.run_in_executor(
                _executor, 
                self._ask_genie_sync, 
                question, 
                max_wait_seconds
            )
        
        # Nenhum configurado
        return {
            "success": False,
            "error": "Chat não configurado",
            "message": "⚠️ O Multi-Agent Endpoint ou Genie Space não foi configurado.\n\nConfigure --agent-endpoint ou --genie-space-id no setup.py."
        }
    
    async def ask_with_history(self, messages: list, context: str = "", max_wait_seconds: int = 120) -> Dict[str, Any]:
        """
        Envia pergunta para o Multi-Agent ou Genie COM histórico de mensagens.
        
        Args:
            messages: Lista de mensagens (histórico completo da conversa)
            context: Contexto adicional (ex: resumos dos contratos)
            max_wait_seconds: Tempo máximo de espera
            
        Returns:
            Dict com a resposta
        """
        loop = asyncio.get_event_loop()
        
        # Extrair última mensagem para fallback
        last_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_message = msg.get("content", "")
                break
        
        # Prioridade 1: Multi-Agent Endpoint (suporta histórico)
        if self.agent_endpoint:
            return await loop.run_in_executor(
                _executor, 
                self._ask_agent_sync, 
                last_message,
                context,
                messages  # passar histórico completo
            )
        
        # Prioridade 2: Genie Space (não suporta histórico diretamente)
        if self.space_id:
            return await loop.run_in_executor(
                _executor, 
                self._ask_genie_sync, 
                last_message, 
                max_wait_seconds
            )
        
        # Nenhum configurado
        return {
            "success": False,
            "error": "Chat não configurado",
            "message": "⚠️ O Multi-Agent Endpoint ou Genie Space não foi configurado.\n\nConfigure --agent-endpoint ou --genie-space-id no setup.py."
        }
    
    async def process_message_streaming(
        self,
        messages: list,
        session_id: Optional[str] = None
    ):
        """
        Processa mensagem e retorna resposta em formato streaming (SSE).
        
        Args:
            messages: Histórico de mensagens
            session_id: ID da sessão (opcional)
            
        Yields:
            Server-Sent Events no formato: data: {json}\n\n
        """
        import json as json_lib
        from ..services.unity_catalog_service import unity_catalog_service
        
        # Enviar evento de início
        yield f"data: {json_lib.dumps({'type': 'thinking-start', 'data': None})}\n\n"
        
        try:
            # Validar que há mensagens
            if not messages or len(messages) == 0:
                error_response = {
                    "type": "final-answer",
                    "data": {"final_answer": "⚠️ Mensagem vazia ou inválida."}
                }
                yield f"data: {json_lib.dumps(error_response)}\n\n"
                return
            
            # Extrair última mensagem do usuário (para log/validação)
            user_message = ""
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    user_message = msg.get("content", "")
                    break
            
            if not user_message:
                error_response = {
                    "type": "final-answer",
                    "data": {"final_answer": "⚠️ Mensagem vazia ou inválida."}
                }
                yield f"data: {json_lib.dumps(error_response)}\n\n"
                return
            
            logger.info(f"💬 Processando pergunta com {len(messages)} mensagens no histórico")
            
            # Obter contexto dos contratos
            context = ""
            try:
                df = unity_catalog_service.get_contract_extract()
                if not df.empty and 'summarize' in df.columns:
                    summaries = df['summarize'].dropna().tolist()
                    context = "\n\n".join(summaries[:5])
            except Exception as e:
                logger.warning(f"⚠️ Erro ao obter contexto: {e}")
            
            # Processar com o agente (passando histórico completo)
            result = await self.ask_with_history(messages, context=context)
            
            if result.get("success"):
                final_answer = result.get("message", "")
            else:
                final_answer = result.get("message", "Erro ao processar sua pergunta.")
            
            # Enviar resposta final
            response = {
                "type": "final-answer",
                "data": {"final_answer": final_answer}
            }
            yield f"data: {json_lib.dumps(response)}\n\n"
            
        except Exception as e:
            logger.error(f"❌ Erro no streaming: {e}")
            error_response = {
                "type": "final-answer",
                "data": {"final_answer": f"⚠️ Erro ao processar: {str(e)}"}
            }
            yield f"data: {json_lib.dumps(error_response)}\n\n"


# Instância singleton
genie_service = GenieService()

