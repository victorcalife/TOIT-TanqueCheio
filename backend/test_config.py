import os
import sys

# Adicionar o diretório src ao caminho de importação
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config_consolidated import Config, ProductionConfig

def print_config():
    print("Verificando configurações do banco de dados...\n")
    
    # Criar instância da configuração
    config = ProductionConfig()
    
    # Imprimir configurações importantes
    print(f"SQLALCHEMY_DATABASE_URI: {config.SQLALCHEMY_DATABASE_URI}")
    print(f"SQLALCHEMY_ENGINE_OPTIONS: {config.SQLALCHEMY_ENGINE_OPTIONS}")
    
    # Verificar se o banco de dados está acessível
    try:
        import psycopg2
        from urllib.parse import urlparse
        
        # Parse da URL de conexão
        result = urlparse(config.SQLALCHEMY_DATABASE_URI)
        
        # Tentar conectar ao banco de dados
        print("\nTentando conectar ao banco de dados...")
        conn = psycopg2.connect(
            dbname=result.path[1:],
            user=result.username,
            password=result.password,
            host=result.hostname,
            port=result.port,
            connect_timeout=5
        )
        
        # Testar conexão
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()
        print(f"✅ Conexão bem-sucedida!")
        print(f"📊 Versão do PostgreSQL: {version[0]}")
        
        # Listar tabelas
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        print("\n📋 Tabelas no banco de dados:")
        for table in cur.fetchall():
            print(f"- {table[0]}")
        
        # Fechar conexão
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro ao conectar ao banco de dados: {e}")
        print("\nPossíveis causas e soluções:")
        print("1. Verifique se o servidor PostgreSQL está em execução")
        print("2. Verifique as credenciais de acesso")
        print("3. Verifique se o firewall permite conexões na porta 5432")
        print("4. Verifique se o usuário tem permissão para acessar o banco de dados")
        print("5. Verifique se o banco de dados existe")
        print("6. Verifique a configuração SSL")

if __name__ == "__main__":
    print_config()
