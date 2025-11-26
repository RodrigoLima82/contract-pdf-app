# Databricks notebook source
# DBTITLE 1,criar widgets para volume_path
dbutils.widgets.text("catalog", "", "")
dbutils.widgets.text("database", "", "")
dbutils.widgets.text("volume_path", "", "")

# COMMAND ----------

catalog = dbutils.widgets.get("catalog")
database = dbutils.widgets.get("database")

# COMMAND ----------

spark.sql(f"USE CATALOG {catalog}")
spark.sql(f"USE {database}")

# COMMAND ----------

# DBTITLE 1,List pdf files in Volume
import os
from pyspark.sql.functions import substring_index
from pyspark.sql.types import StructType, StructField, StringType, LongType, TimestampType
import re
from datetime import datetime
import hashlib


# Directory path
directory_path = dbutils.widgets.get("volume_path")

# List files in directory
file_paths = [file.path for file in dbutils.fs.ls(directory_path)]

# Function to extract the file hash
def get_file_hash(file_path, chunk_size=4096):
    path = file_path.replace("dbfs:", "")
    hash_md5 = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

# Extract file names from paths
file_info = [
    (
        os.path.basename(file.path),
        os.path.splitext(os.path.basename(file.path))[1].lstrip('.').lower(),
        file.size,
        file.path,
        datetime.now(),
        None,
        get_file_hash(file.path)

    )
    for file in dbutils.fs.ls(directory_path)
]

schema = StructType([
    StructField("file_name", StringType(), True),
    StructField("type", StringType(), True),
    StructField("size", LongType(), True),
    StructField("file_path", StringType(), True),
    StructField("upload_time", TimestampType(), True),
    StructField("processed_time", TimestampType(), True),
    StructField("file_hash", StringType(), True)
])

df = spark.createDataFrame(file_info, schema)


# Show dataframe
df.show()

# COMMAND ----------

# DBTITLE 1,Create table to track which contract pdf files we've already processed
sql("""
CREATE TABLE IF NOT EXISTS contract_track (
  file_name STRING,
  type STRING,
  size BIGINT,
  processed STRING,
  file_path STRING,
  upload_time TIMESTAMP,
  processed_time TIMESTAMP,
  file_hash STRING
)
tblproperties (delta.enableChangeDataFeed = true)
""")

# COMMAND ----------

# DBTITLE 1,Update contract_track table so same files aren't processed again
df.createOrReplaceTempView("temp_table")

# Insert only the rows that do not exist in the target table
spark.sql("""
    INSERT INTO contract_track
    SELECT file_name, type, size, 'N', file_path, upload_time, processed_time, file_hash
      FROM temp_table
     WHERE NOT EXISTS (
         SELECT 1 FROM contract_track
          WHERE temp_table.file_name = contract_track.file_name
          OR temp_table.file_hash = contract_track.file_hash
    )
""")

# COMMAND ----------

sql("SELECT * FROM contract_track").display()