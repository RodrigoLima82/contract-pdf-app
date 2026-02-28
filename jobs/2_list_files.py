# Databricks notebook source
dbutils.widgets.text("catalog", "seu_catalog", "Catalog")
dbutils.widgets.text("database", "contract_pdf", "Database/Schema")
dbutils.widgets.text("table", "contract_track", "Table Name")

# COMMAND ----------

catalog = dbutils.widgets.get("catalog")
database = dbutils.widgets.get("database")
table = dbutils.widgets.get("table")

# Validar que os parâmetros não estão vazios
if not catalog or not database or not table:
    raise ValueError(f"Parâmetros obrigatórios não fornecidos: catalog={catalog}, database={database}, table={table}")

print(f"Catalog: {catalog}")
print(f"Database: {database}")
print(f"Table: {table}")

# COMMAND ----------

spark.sql(f"USE CATALOG {catalog}")
spark.sql(f"USE {database}")

# COMMAND ----------

# Consulta SQL para obter arquivos não processados
df = spark.sql(f"""
SELECT *
FROM {table}
WHERE processed = 'N'
""")

# Crie uma lista com os caminhos dos arquivos
files = [row['file_path'] for row in df.collect()]

# COMMAND ----------

files

# COMMAND ----------


# Guarde a lista como Task Value para uso
dbutils.jobs.taskValues.set(key="arrival_files", value=files)
print(f"{len(files)} arquivos de chegada encontrados.")