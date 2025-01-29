from pyspark.sql import SparkSession
import logging
import os
from dotenv import load_dotenv

load_dotenv()

# Configuração do logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class MinIOIngestion:
    def __init__(self):
        logging.info("Inicializando MinIOIngestion...")

    def save_to_minio(self, data, column_names, bucket_path):
        logging.info("Iniciando processo de salvar dados no MinIO.")

        # Criar SparkSession
        spark = SparkSession.builder.appName("MinIO Delta Save").getOrCreate()

        # Criar DataFrame
        df = spark.createDataFrame(data, column_names)

        # Salvar como Delta no MinIO
        logging.info(f"Salvando tabela Delta no MinIO em {bucket_path}...")
        df.write.format("delta").mode("overwrite").save(bucket_path)
        logging.info("Tabela salva no MinIO com sucesso!")

# Para rodar o script
if __name__ == "__main__":
    # Configurar dados de exemplo
    data = [
        ("Alice", 1), ("Bob", 2), ("Charlie", 3),
        ("David", 4), ("Eve", 5), ("Frank", 6), ("Grace", 7)
    ]
    column_names = ["name", "value"]
    bucket_path = "s3a://silver/delta_table"

    # Executar processo de ingestão
    minio_ingestion = MinIOIngestion()
    minio_ingestion.save_to_minio(data, column_names, bucket_path)
