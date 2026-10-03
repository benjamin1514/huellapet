import os
import pymysql
import pymysql.cursors
from dotenv import load_dotenv

# Carga las variables de entorno desde el archivo .env
load_dotenv()

class MySQLConnection:
    def __init__(self, db):
        self.connection = pymysql.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=db,
            port=int(os.getenv("DB_PORT", 3306)),
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True
        )

    def query_db(self, query, data=None):
        with self.connection.cursor() as cursor:
            try:
                # Ejecuta la consulta pasando los parámetros de forma segura
                cursor.execute(query, data or {})
                
                query_type = query.strip().lower()
                if query_type.startswith("select"):
                    return cursor.fetchall()
                elif query_type.startswith("insert"):
                    return cursor.lastrowid
                else:
                    return True
            except Exception as e:
                print(f"Error en la consulta MySQL: {e}")
                return False

    def close(self):
        """Cierra la conexión explícitamente cuando ya no la necesites."""
        if self.connection and self.connection.open:
            self.connection.close()

def connectToMySQL(db):
    return MySQLConnection(db)