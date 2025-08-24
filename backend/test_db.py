import psycopg2
from urllib.parse import urlparse

def test_connection():
    try:
        # Dados de conexão do config_consolidated.py
        db_url = "postgresql://postgres:HXmzPSGlMEcjpzICIZphyTFuNLcGbAjL@postgres-admt.railway.internal:5432/railway"
        
        # Parse da URL de conexão
        result = urlparse(db_url)
        username = result.username
        password = result.password
        database = result.path[1:]
        hostname = result.hostname
        port = result.port
        
        # Estabelecer conexão
        conn = psycopg2.connect(
            dbname=database,
            user=username,
            password=password,
            host=hostname,
            port=port,
            connect_timeout=5
        )
        
        # Testar conexão
        cur = conn.cursor()
        cur.execute("SELECT version();")
        db_version = cur.fetchone()
        print(f"Conexão bem-sucedida!\nVersão do PostgreSQL: {db_version[0]}")
        
        # Listar tabelas
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cur.fetchall()
        print("\nTabelas no banco de dados:")
        for table in tables:
            print(f"- {table[0]}")
        
        # Fechar conexão
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {str(e)}")

if __name__ == "__main__":
    test_connection()
