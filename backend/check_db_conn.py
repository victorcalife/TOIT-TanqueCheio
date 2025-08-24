import psycopg2
import sys

def test_connection():
    print("Testando conexão com o banco de dados...")
    
    # Configurações de conexão
    conn_params = {
        'dbname': 'railway',
        'user': 'postgres',
        'password': 'HXmzPSGlMEcjpzICIZphyTFuNLcGbAjL',
        'host': 'postgres-admt.railway.internal',
        'port': 5432,
        'connect_timeout': 5
    }
    
    try:
        # Tentar conectar ao banco de dados
        print(f"Conectando ao banco de dados {conn_params['dbname']} em {conn_params['host']}:{conn_params['port']}...")
        conn = psycopg2.connect(**conn_params)
        
        # Criar cursor
        cursor = conn.cursor()
        
        # Testar conexão
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        
        if result[0] == 1:
            print("✅ Conexão bem-sucedida!")
        
        # Fechar conexão
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro ao conectar ao banco de dados: {e}")
        print(f"Tipo de erro: {type(e).__name__}")
        
        # Verificar se o erro é de autenticação
        if "password authentication failed" in str(e).lower():
            print("\n🔒 Erro de autenticação. Verifique as credenciais de acesso.")
        # Verificar se o erro é de conexão
        elif "could not connect" in str(e).lower():
            print("\n🔌 Erro de conexão. Verifique se o servidor PostgreSQL está em execução e acessível.")
        else:
            print("\n❌ Erro desconhecido ao conectar ao banco de dados.")

if __name__ == "__main__":
    test_connection()
