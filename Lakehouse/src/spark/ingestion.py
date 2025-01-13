from pyspark.sql import SparkSession
from pyspark import SparkConf
import logging
import os
from trino import dbapi

# Load .env file using:
from dotenv import load_dotenv
load_dotenv()

# Configuração explícita do logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MinIODeltaTrino:
    def __init__(self):
        logging.info("Inicializando MinIODeltaTrino...")

        # Configurações do Spark para MinIO
        self.conf = (
            SparkConf()
            .set("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
            .set("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
            .set("spark.hadoop.fs.s3a.aws.credentials.provider", "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider")
            .set("spark.hadoop.fs.s3a.endpoint", os.getenv("MINIO_ENDPOINT"))
            .set("spark.hadoop.fs.s3a.access.key", os.getenv("MINIO_USER"))
            .set("spark.hadoop.fs.s3a.secret.key", os.getenv("MINIO_PASSWORD"))
            .set("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
            .set("spark.hadoop.fs.s3a.path.style.access", "true")
            .set("fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
            .set("spark.jars.packages", "io.delta:delta-core_2.12:2.4.0,org.apache.hadoop:hadoop-aws:3.3.4")
        )

        # Conexão com Trino
        self.trino_host = os.getenv("TRINO_HOST")
        self.trino_port = os.getenv("TRINO_PORT")
        self.trino_user = os.getenv("TRINO_USER")
        self.trino_catalog = os.getenv("TRINO_CATALOG_SILVER")
        self.trino_schema =  os.getenv("TRINO_SCHEMA_SILVER")

    def save_to_minio_and_trino(self, data, column_names, table_name, bucket_path):
        logging.info("Iniciando processo de salvar dados no MinIO e registrar no Trino.")

        # Criar SparkSession
        spark = SparkSession.builder.appName("MinIO Delta Save").config(conf=self.conf).getOrCreate()

        # Criar DataFrame
        df = spark.createDataFrame(data, column_names)

        # Salvar como Delta no MinIO
        logging.info(f"Salvando tabela Delta no MinIO em {bucket_path}...")
        df.write.format("delta").mode("overwrite").save(bucket_path)
        logging.info("Tabela salva no MinIO com sucesso!")

        # Verificar se a tabela já existe no Trino
        if self._table_exists(table_name):
            logging.info(f"A tabela {table_name} já existe no Trino. Nenhuma ação necessária.")
        else:
            # Registrar a tabela no Trino
            query = f"""
            CALL minio.system.register_table
                (
                    schema_name => '{self.trino_schema}',
                    table_name => '{table_name}',
                    table_location => '{bucket_path}'
                )
            """
            self._execute_trino_query(query)
            logging.info("Tabela registrada no Trino com sucesso!")

    def _table_exists(self, table_name):
        try:
            query = f"SHOW TABLES IN {self.trino_catalog}.{self.trino_schema} LIKE '{table_name}'"
            trino_conn = dbapi.connect(
                host=self.trino_host,
                port=self.trino_port,
                user=self.trino_user,
                catalog=self.trino_catalog,
                schema=self.trino_schema,
            )
            cursor = trino_conn.cursor()
            cursor.execute(query)
            result = cursor.fetchall()
            cursor.close()
            return len(result) > 0
        except Exception as e:
            logging.error(f"Erro ao verificar existência da tabela no Trino: {e}")
            raise

    def _execute_trino_query(self, query):
        try:
            logging.info(f"Executando query no Trino: {query}")
            trino_conn = dbapi.connect(
                host=self.trino_host,
                port=self.trino_port,
                user=self.trino_user,
                catalog=self.trino_catalog,
                schema=self.trino_schema,
            )
            cursor = trino_conn.cursor()
            cursor.execute(query)
            cursor.close()
        except Exception as e:
            logging.error(f"Erro ao executar query no Trino: {e}")
            raise

# Para rodar o script
if __name__ == "__main__":
    # Configurar dados de exemplo
    data = [
        ("Alice", 1),("Bob", 2), ("Charlie", 3),
        ("David", 4), ("Eve", 5), ("Frank", 6), ("Grace", 7)
    ]
    column_names = ["name", "value"]
    table_name = "users"
    bucket_path = "s3a://silver/delta_table"

    # Executar processo
    delta_trino = MinIODeltaTrino()
    delta_trino.save_to_minio_and_trino(data, column_names, table_name, bucket_path)


