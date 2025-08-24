import psycopg2

def test_connection():
    print("Testando conexão com o banco de dados...")
    
    try:
        conn = psycopg2.connect(
            dbname='railway',
            user='postgres',
            password='HXmzPSGlMEcjpzICIZphyTFuNLcGbAjL',
            host='postgres-admt.railway.internal',
            port=5432,
            connect_timeout=5
        )
        
        print("✅ Conexão bem-sucedida!")
        
        # Testar consulta simples
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()
        print(f"Versão do PostgreSQL: {version[0]}")
        
        # Listar tabelas
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        print("\nTabelas no banco de dados:")
        for table in cur.fetchall():
            print(f"- {table[0]}")
            
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro ao conectar ao banco de dados: {e}")

if __name__ == "__main__":
    test_connection()
