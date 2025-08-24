import psycopg2
from urllib.parse import urlparse
import ssl

def test_postgres_connection():
    print("Testando conexão com o banco de dados PostgreSQL com SSL...")
    
    # Dados de conexão
    db_url = "postgresql://postgres:HXmzPSGlMEcjpzICIZphyTFuNLcGbAjL@postgres-admt.railway.internal:5432/railway"
    
    try:
        # Parse da URL de conexão
        result = urlparse(db_url)
        username = result.username
        password = result.password
        database = result.path[1:]
        hostname = result.hostname
        port = result.port
        
        # Configuração SSL
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Estabelecer conexão
        print(f"Conectando ao banco de dados {database} em {hostname}:{port}...")
        conn = psycopg2.connect(
            dbname=database,
            user=username,
            password=password,
            host=hostname,
            port=port,
            connect_timeout=5,
            sslmode='require',
            sslrootcert=None,
            sslcert=None,
            sslkey=None,
            ssl={
                'sslmode': 'require',
                'sslrootcert': None,
                'sslcert': None,
                'sslkey': None
            }
        )
        
        # Testar conexão
        cur = conn.cursor()
        cur.execute("SELECT version();")
        db_version = cur.fetchone()
        print(f"✅ Conexão bem-sucedida!")
        print(f"📊 Versão do PostgreSQL: {db_version[0]}")
        
        # Listar tabelas
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cur.fetchall()
        print("\n📋 Tabelas no banco de dados:")
        for table in tables:
            print(f"- {table[0]}")
        
        # Fechar conexão
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro ao conectar ao banco de dados: {str(e)}")
        print("\nPossíveis causas e soluções:")
        print("1. Verifique se o servidor PostgreSQL está em execução")
        print("2. Verifique as credenciais de acesso")
        print("3. Verifique se o firewall permite conexões na porta 5432")
        print("4. Verifique se o usuário tem permissão para acessar o banco de dados")
        print("5. Verifique se o banco de dados 'railway' existe")
        print("6. Verifique a configuração SSL")

if __name__ == "__main__":
    test_postgres_connection()
