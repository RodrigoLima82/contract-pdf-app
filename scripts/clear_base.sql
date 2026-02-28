-- Limpa toda a base de contratos para permitir novo upload e processamento.
-- NÃO remove: contract_template (templates são mantidos).
-- Execute no Databricks SQL ou notebook após ajustar catalog/database.
--
-- USE CATALOG seu_catalog;
-- USE DATABASE contract_pdf;

TRUNCATE TABLE contract_compliance;
TRUNCATE TABLE contract_extract;
TRUNCATE TABLE contract_parsed;
TRUNCATE TABLE contract_track;

-- Opcional: limpar também os arquivos do volume (execute no notebook Python se quiser):
-- dbutils.fs.rm("/Volumes/seu_catalog/contract_pdf/files/", recurse=True)
-- e depois recriar: CREATE VOLUME IF NOT EXISTS ... files
