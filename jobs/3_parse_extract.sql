-- Databricks notebook source
-- DBTITLE 1,Criar os parametros para o notebook
-- Create widgets
CREATE WIDGET TEXT catalog DEFAULT 'seu_catalog';
CREATE WIDGET TEXT database DEFAULT 'contract_pdf';
CREATE WIDGET TEXT trackTableName DEFAULT 'contract_track';
CREATE WIDGET TEXT parsedTableName DEFAULT 'contract_parsed';
CREATE WIDGET TEXT extractTableName DEFAULT 'contract_extract';
CREATE WIDGET TEXT templateTableName DEFAULT 'contract_template';
CREATE WIDGET TEXT complianceTableName DEFAULT 'contract_compliance';
CREATE WIDGET TEXT sourcePDFPath DEFAULT '/Volumes/seu_catalog/contract_pdf/files';
CREATE WIDGET TEXT limit DEFAULT '100';
CREATE WIDGET TEXT partitionCount DEFAULT '10';
CREATE WIDGET TEXT file_path DEFAULT '';

-- COMMAND ----------

-- DBTITLE 1,Set do catalog e schema
USE catalog IDENTIFIER(:catalog);
USE database IDENTIFIER(:database);

-- COMMAND ----------

-- DBTITLE 1,Criar tabela delta para armazenar o conteudo do contrato
-- Create parsed table 
CREATE TABLE IF NOT EXISTS IDENTIFIER(:parsedTableName) (
  path STRING,
  raw_parsed VARIANT,
  text STRING,
  summarize STRING,
  error_status STRING
);

-- COMMAND ----------

-- Create contract extraction table 
CREATE TABLE IF NOT EXISTS IDENTIFIER(:extractTableName) (
  path STRING,
  summarize STRING,
  tipo_contrato STRING,
  nome_contrato STRING,
  contratante STRING,
  contratado STRING,
  valor_total DOUBLE,
  moeda STRING,
  data_assinatura DATE,
  data_inicio_vigencia DATE,
  data_fim_vigencia DATE,
  prazo_vigencia STRING,
  objeto_contrato STRING,
  forma_pagamento STRING,
  condicoes_pagamento STRING,
  clausula_rescisao STRING,
  multa_rescisao DOUBLE,
  garantias STRING,
  confidencialidade STRING,
  foro STRING,
  observacoes STRING
);

-- COMMAND ----------

ALTER TABLE IDENTIFIER(:extractTableName) SET TBLPROPERTIES (delta.enableChangeDataFeed = true)

-- COMMAND ----------

-- DBTITLE 1,Funcao para realizar o resumo do contrato
CREATE OR REPLACE FUNCTION SUMMARIZE_CONTRACT_DATA(text STRING)
RETURNS STRING  
RETURN AI_QUERY(
            'databricks-gpt-5-2',
            CONCAT(
            'Você é um assistente de IA especialista em resumir informações de contratos. 
            Analise o documento e extraia as informações mais relevantes do contrato.
            
            Use esse template para dar a resposta ao usuário:
            
            **Tipo de Contrato:**
            **Nome/Identificação do Contrato:**
            **Partes Envolvidas:**
            - Contratante:
            - Contratado:
            
            **Valores e Condições Financeiras:**
            - Valor Total:
            - Moeda:
            - Forma de Pagamento:
            - Condições de Pagamento:
            
            **Datas e Prazos:**
            - Data de Assinatura:
            - Início da Vigência:
            - Fim da Vigência:
            - Prazo de Vigência:
            
            **Objeto do Contrato:**
            - Descrição detalhada do objeto/serviço contratado
            
            **Cláusulas Importantes:**
            - Rescisão: (condições e prazos)
            - Multas: (valores e condições)
            - Garantias: (se houver)
            - Confidencialidade: (se houver)
            
            **Aspectos Legais:**
            - Foro:
            
            **Observações Relevantes:**
            - Outras cláusulas ou informações importantes
            
            INSTRUÇÕES PARA INCLUIR PÁGINAS:
            Sempre inclua [página X] após cada informação importante.
            Exemplo: "Valor Total: R$ 500.000,00 [página 3]"
            
            Retorne em formato organizado e legível.

            TEXT: ', text
            )
        )

-- COMMAND ----------

-- DBTITLE 1,Funcao para realizar a extracao de dados estruturados do contrato
CREATE OR REPLACE FUNCTION EXTRACT_CONTRACT_DATA(text STRING)
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
RETURN FROM_JSON(
  AI_QUERY(
    'databricks-gpt-5-2',
    CONCAT(
          'Você é um assistente de IA especialista em extrair informações estruturadas de contratos.

          Nunca trazer os caracteres ``` no resultado final.

          Extraia as seguintes informações do contrato:
            - tipo_contrato: use SOMENTE um destes valores exatos: "Prestação de Serviços", "Fornecimento", "Locação", "Compra e Venda", "Outros". Mapeie tipos similares para o mais próximo (ex: "Acordo de Prestação de Serviços Profissionais", "Professional Services Agreement" ou "Prestação de Serviços" -> sempre "Prestação de Serviços").
            - nome_contrato: apenas o número/código do contrato (ex: "Contract No. PSA-2025-0012"). NÃO inclua o tipo de acordo ou subtítulo (ex: omitir " - PROFESSIONAL SERVICES AGREEMENT" ou " - Acordo de Prestação de Serviços"). Se houver "Contract No. X" ou código como "PSA-2025-0012", use só essa parte.
            - contratante: nome completo da parte contratante (string)
            - contratado: nome completo da parte contratada (string)
            - valor_total: valor total do contrato em formato numérico (float)
            - moeda: moeda do contrato (ex: BRL, USD, EUR) (string)
            - data_assinatura: data de assinatura no formato YYYY-MM-DD (string)
            - data_inicio_vigencia: data de início da vigência no formato YYYY-MM-DD (string)
            - data_fim_vigencia: data de fim da vigência no formato YYYY-MM-DD (string)
            - prazo_vigencia: prazo de vigência descrito (ex: 12 meses, 2 anos) (string)
            - objeto_contrato: descrição resumida do objeto do contrato (string, máximo 500 caracteres)
            - forma_pagamento: forma de pagamento (ex: Boleto, Transferência, Cartão) (string)
            - condicoes_pagamento: condições de pagamento (ex: 30/60/90 dias, À vista) (string)
            - clausula_rescisao: resumo da cláusula de rescisão (string)
            - multa_rescisao: valor ou percentual da multa de rescisão (float)
            - garantias: descrição das garantias contratuais, se houver (string)
            - confidencialidade: informações sobre cláusula de confidencialidade (string)
            - foro: foro ou jurisdição competente (string)
            - observacoes: outras informações relevantes (string)

          IMPORTANTE:
          - Para valores monetários, extraia apenas o número (ex: 500000.00)
          - Para datas, use o formato YYYY-MM-DD (ex: 2024-01-15)
          - Se alguma informação não estiver disponível, use null
          - Para strings vazias, use null ao invés de ""
          
          Retorne SOMENTE um JSON válido. Nenhum outro texto fora o JSON. 
          
          Formato do JSON:
          {
            "tipo_contrato": <tipo do contrato>,
            "nome_contrato": <nome do contrato>,
            "contratante": <nome do contratante>,
            "contratado": <nome do contratado>,
            "valor_total": <valor numérico>,
            "moeda": <moeda>,
            "data_assinatura": <data YYYY-MM-DD>,
            "data_inicio_vigencia": <data YYYY-MM-DD>,
            "data_fim_vigencia": <data YYYY-MM-DD>,
            "prazo_vigencia": <prazo>,
            "objeto_contrato": <descrição do objeto>,
            "forma_pagamento": <forma de pagamento>,
            "condicoes_pagamento": <condições>,
            "clausula_rescisao": <resumo da cláusula>,
            "multa_rescisao": <valor da multa>,
            "garantias": <descrição das garantias>,
            "confidencialidade": <informações de confidencialidade>,
            "foro": <foro competente>,
            "observacoes": <observações relevantes>
          }

          extract_from: ', text
        )
  ),
  "STRUCT<tipo_contrato: STRING, nome_contrato: STRING, contratante: STRING, contratado: STRING, valor_total: DOUBLE, moeda: STRING, data_assinatura: STRING, data_inicio_vigencia: STRING, data_fim_vigencia: STRING, prazo_vigencia: STRING, objeto_contrato: STRING, forma_pagamento: STRING, condicoes_pagamento: STRING, clausula_rescisao: STRING, multa_rescisao: DOUBLE, garantias: STRING, confidencialidade: STRING, foro: STRING, observacoes: STRING>"
)

-- COMMAND ----------

-- DBTITLE 1,Funcao para validar compliance do item com o template
CREATE OR REPLACE FUNCTION CHECK_ITEM_COMPLIANCE(summarize STRING, item_description STRING)
RETURNS STRING
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
END;

-- COMMAND ----------

-- DBTITLE 1,Remover a variavel temporaria
DROP TEMPORARY VARIABLE IF EXISTS parse_extensions;

-- COMMAND ----------

-- DBTITLE 1,Criar variavel temporaria para tipos de documentos
DECLARE parse_extensions ARRAY<STRING> DEFAULT array('.pdf');

-- COMMAND ----------

-- DBTITLE 1,Rotina para o parse e resumo do pdf
-- Idempotência: remove dados anteriores deste(s) arquivo(s) para evitar duplicatas
DELETE FROM IDENTIFIER(:parsedTableName)
WHERE path LIKE CONCAT('%', :file_path, '%');

INSERT INTO IDENTIFIER(:parsedTableName)

-- Parse documents with ai_parse
-- Remove dbfs: prefix if present for READ_FILES compatibility
WITH all_files AS (
  SELECT
    path,
    content
  FROM
    READ_FILES(REPLACE(:file_path, 'dbfs:', ''), format => 'binaryFile')
  ORDER BY
    path ASC
  LIMIT INT(:limit)
),
repartitioned_files AS (
  SELECT *
  FROM all_files
  -- Force Spark to split into partitions
  DISTRIBUTE BY crc32(path) % INT(:partitionCount)
),
-- Parse the files using ai_parse document
parsed_documents AS (
  SELECT
    path,
    ai_parse_document(content) as parsed
  FROM
    repartitioned_files
  WHERE array_contains(parse_extensions, lower(regexp_extract(path, r'(\.[^.]+)$', 1)))
),
raw_documents AS (
  SELECT
    path,
    null as raw_parsed,
    decode(content, 'utf-8') as text,
    null as summarize,
    null as error_status
  FROM 
    repartitioned_files
  WHERE NOT array_contains(parse_extensions, lower(regexp_extract(path, r'(\.[^.]+)$', 1)))
),
-- Mark documents with ai_parse errors
error_documents AS (
  SELECT
    path,
    parsed as raw_parsed,
    null as text,
    null as summarize,
    try_cast(parsed:error_status AS STRING) AS error_status
  FROM
    parsed_documents
  WHERE try_cast(parsed:error_status AS STRING) IS NOT NULL
),
-- Extract content from ai_parse_document output for all successful parses
sorted_contents AS (
  SELECT
    path,
    element:content AS content
  FROM
    (
      SELECT
        path,
          posexplode(
            CASE
              WHEN try_cast(parsed:metadata:version AS STRING) = '1.0' 
              THEN try_cast(parsed:document:pages AS ARRAY<VARIANT>)
              ELSE try_cast(parsed:document:elements AS ARRAY<VARIANT>)
            END
          ) AS (idx, element)
      FROM
        parsed_documents
      WHERE try_cast(parsed:error_status AS STRING) IS NULL
    )
  ORDER BY
    idx
),
-- Concatenate so we have 1 row per document
concatenated AS (
    SELECT
        path,
        concat_ws('

', collect_list(content)) AS full_content
    FROM
        sorted_contents
    WHERE content IS NOT NULL
    GROUP BY
        path
),
-- Bring back the raw parsing since it could be useful for other downstream uses
with_raw AS (
    SELECT
        a.path,
        b.parsed as raw_parsed,
        a.full_content as text,
        SUMMARIZE_CONTRACT_DATA(b.parsed) as summarize,
        null as error_status
    FROM concatenated a
    JOIN parsed_documents b ON a.path = b.path
)
-- Recombine raw text documents with parsed documents
SELECT *  FROM with_raw
UNION ALL 
SELECT * FROM raw_documents
UNION ALL
SELECT * FROM error_documents

-- COMMAND ----------

-- DBTITLE 1,Extrair todas as informacoes necessarias do contrato
-- Idempotência: remove extração anterior deste(s) arquivo(s) para evitar duplicatas no compliance
DELETE FROM IDENTIFIER(:extractTableName)
WHERE path LIKE CONCAT('%', :file_path, '%');

INSERT INTO IDENTIFIER(:extractTableName)
SELECT t.path, t.summarize, t.extract_info.* 
  FROM (SELECT path, summarize, EXTRACT_CONTRACT_DATA(summarize) as extract_info
          FROM IDENTIFIER(:parsedTableName)
         WHERE path LIKE CONCAT('%', :file_path, '%')
  ) t

-- COMMAND ----------

-- DBTITLE 1,Normalizar tipo_contrato e nome_contrato
-- tipo_contrato: unificar variações (ex: "Acordo de Prestação de Serviços Profissionais" -> "Prestação de Serviços")
-- nome_contrato: manter só número/código (ex: remover " - PROFESSIONAL SERVICES AGREEMENT")
UPDATE IDENTIFIER(:extractTableName) e
SET
  tipo_contrato = CASE
    WHEN LOWER(TRIM(COALESCE(e.tipo_contrato, ''))) LIKE '%prestação%serviços%'
      OR LOWER(TRIM(COALESCE(e.tipo_contrato, ''))) LIKE '%acordo%prestação%'
      OR LOWER(TRIM(COALESCE(e.tipo_contrato, ''))) LIKE '%professional services%'
      OR LOWER(TRIM(COALESCE(e.tipo_contrato, ''))) LIKE '%prestação de serviços%'
     THEN 'Prestação de Serviços'
    WHEN LOWER(TRIM(COALESCE(e.tipo_contrato, ''))) LIKE '%fornecimento%' THEN 'Fornecimento'
    WHEN LOWER(TRIM(COALESCE(e.tipo_contrato, ''))) LIKE '%locação%'
      OR LOWER(TRIM(COALESCE(e.tipo_contrato, ''))) LIKE '%locacao%' THEN 'Locação'
    WHEN LOWER(TRIM(COALESCE(e.tipo_contrato, ''))) LIKE '%compra%e%venda%' THEN 'Compra e Venda'
    WHEN TRIM(COALESCE(e.tipo_contrato, '')) = '' THEN 'Outros'
    ELSE e.tipo_contrato
  END,
  nome_contrato = CASE
    WHEN e.nome_contrato LIKE '% - %'
     THEN TRIM(element_at(SPLIT(e.nome_contrato, ' - '), 1))
    ELSE e.nome_contrato
  END
WHERE e.path LIKE CONCAT('%', :file_path, '%');

-- COMMAND ----------

-- DBTITLE 1,Seleciona os dados extraidos
SELECT * FROM IDENTIFIER(:extractTableName) WHERE path LIKE CONCAT('%', :file_path, '%')

-- COMMAND ----------

-- DBTITLE 1,Atualiza a tabela de tracking de documentos
UPDATE IDENTIFIER(:trackTableName)
SET processed = 'S',
    processed_time = current_timestamp()
WHERE file_path LIKE CONCAT('%', :file_path, '%')

-- COMMAND ----------

-- DBTITLE 1,Validação de compliance com templates
-- Remove compliance anterior deste contrato (idempotência)
DELETE FROM IDENTIFIER(:complianceTableName)
WHERE path LIKE CONCAT('%', :file_path, '%');

-- Para cada linha do template (cada item) cujo tipo_contrato_match casa com o contrato, valida e grava Compliance ou Não Compliance
INSERT INTO IDENTIFIER(:complianceTableName) (path, template_name, item_description, status, evidence, validated_at)
SELECT
  e.path,
  t.template_name,
  t.item_description,
  CHECK_ITEM_COMPLIANCE(e.summarize, t.item_description) AS status,
  CAST(NULL AS STRING) AS evidence,
  current_timestamp() AS validated_at
FROM IDENTIFIER(:extractTableName) e
JOIN IDENTIFIER(:templateTableName) t ON e.tipo_contrato LIKE t.tipo_contrato_match
WHERE e.path LIKE CONCAT('%', :file_path, '%');

-- COMMAND ----------

