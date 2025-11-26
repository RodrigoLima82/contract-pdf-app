# Databricks notebook source
dbutils.widgets.text("catalog", "", "")
dbutils.widgets.text("database", "", "")
dbutils.widgets.text("table", "", "")

# COMMAND ----------

catalog = dbutils.widgets.get("catalog")
database = dbutils.widgets.get("database")
table = dbutils.widgets.get("table")

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