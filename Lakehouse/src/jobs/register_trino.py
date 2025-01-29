import logging
import os
from trino import dbapi
from dotenv import load_dotenv

load_dotenv()

# Configuração do logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class TrinoTableRegistration:
    def __init__(self):
        logging.info("Inicializando TrinoTableRegistration...")

        # Conexão com Trino
        self.trino_host = "172.30.0.10"
        self.trino_port = os.getenv("TRINO_PORT")
        self.trino_user = os.getenv("TRINO_USER")
        self.trino_catalog = os.getenv("TRINO_CATALOG_SILVER")
        self.trino_schema = os.getenv("TRINO_SCHEMA_SILVER")

    def register_table(self, table_name, bucket_path):
        if self._table_exists(table_name):
            logging.info(f"A tabela {table_name} já existe no Trino. Nenhuma ação necessária.")
        else:
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
    table_name = "users"
    bucket_path = "s3a://silver/delta_table"

    # Executar registro no Trino
    trino_registration = TrinoTableRegistration()
    trino_registration.register_table(table_name, bucket_path)
