import psycopg2
import sys
import socket
import time

def test_connection():
    print("🔍 Iniciando teste de conexão com o banco de dados...")
    
    # Configurações de conexão
    db_config = {
        'dbname': 'railway',
        'user': 'postgres',
        'password': 'HXmzPSGlMEcjpzICIZphyTFuNLcGbAjL',
        'host': 'postgres-admt.railway.internal',
        'port': 5432,
        'connect_timeout': 5
    }
    
    # 1. Verificar resolução DNS
    print("\n🔍 Verificando resolução DNS...")
    try:
        ip = socket.gethostbyname(db_config['host'])
        print(f"✅ Host resolvido: {db_config['host']} -> {ip}")
    except socket.gaierror as e:
        print(f"❌ Falha ao resolver o host {db_config['host']}: {e}")
        print("   Verifique a conectividade de rede e as configurações de DNS.")
        return
    
    # 2. Verificar acessibilidade da porta
    print("\n🔍 Verificando acessibilidade da porta...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        start_time = time.time()
        result = sock.connect_ex((db_config['host'], db_config['port']))
        end_time = time.time()
        
        if result == 0:
            print(f"✅ Porta {db_config['port']} está aberta e acessível em {db_config['host']}")
            print(f"   Tempo de resposta: {(end_time - start_time) * 1000:.2f} ms")
        else:
            print(f"❌ Porta {db_config['port']} está fechada ou inacessível em {db_config['host']}")
            print("   Verifique se o servidor PostgreSQL está em execução e acessível.")
            return
        
        sock.close()
    except Exception as e:
        print(f"❌ Erro ao verificar a porta: {e}")
        return
    
    # 3. Testar conexão com o banco de dados
    print("\n🔍 Testando conexão com o banco de dados...")
    try:
        start_time = time.time()
        conn = psycopg2.connect(**db_config)
        end_time = time.time()
        
        print(f"✅ Conexão bem-sucedida em {(end_time - start_time) * 1000:.2f} ms!")
        
        # 4. Verificar versão do PostgreSQL
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"\n📊 {version}")
        
        # 5. Listar tabelas
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        print(f"\n📋 Tabelas no banco de dados ({len(tables)}):")
        for i, table in enumerate(tables, 1):
            print(f"{i:2d}. {table[0]}")
        
        # 6. Verificar tabelas importantes
        important_tables = [
            'users', 
            'user_profiles', 
            'gas_stations', 
            'fuel_prices',
            'user_sessions',
            'alembic_version'
        ]
        
        missing_tables = [t for t in important_tables if t not in [x[0] for x in tables]]
        
        if missing_tables:
            print(f"\n⚠️  Tabelas importantes ausentes: {', '.join(missing_tables)}")
            
            if 'alembic_version' in missing_tables:
                print("\nℹ️  A tabela 'alembic_version' não foi encontrada.")
                print("   Execute 'flask db upgrade' para aplicar as migrações do banco de dados.")
        else:
            print("\n✅ Todas as tabelas importantes estão presentes!")
        
        # 7. Verificar se há dados nas tabelas
        if 'users' in [x[0] for x in tables]:
            cursor.execute("SELECT COUNT(*) FROM users;")
            user_count = cursor.fetchone()[0]
            print(f"\n👥 Total de usuários cadastrados: {user_count}")
        
        if 'gas_stations' in [x[0] for x in tables]:
            cursor.execute("SELECT COUNT(*) FROM gas_stations;")
            station_count = cursor.fetchone()[0]
            print(f"⛽ Total de postos cadastrados: {station_count}")
        
        # Fechar conexão
        cursor.close()
        conn.close()
        
    except psycopg2.OperationalError as e:
        print(f"\n❌ Erro ao conectar ao banco de dados: {e}")
        
        if "password authentication failed" in str(e).lower():
            print("\n🔒 Erro de autenticação. Verifique as credenciais de acesso.")
        elif "does not exist" in str(e).lower():
            print("\nℹ️  O banco de dados especificado não existe.")
            print(f"   Verifique se o banco de dados '{db_config['dbname']}' foi criado corretamente.")
        elif "connection refused" in str(e).lower():
            print("\n🔌 Conexão recusada. Verifique se o servidor PostgreSQL está em execução.")
        elif "timeout expired" in str(e).lower():
            print("\n⏱️  Tempo limite de conexão excedido. Verifique a conectividade de rede.")
        
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        print(f"Tipo de erro: {type(e).__name__}")
    
    print("\n🔧 Dicas para solução de problemas:")
    print("1. Verifique se o servidor PostgreSQL está em execução")
    print("2. Verifique as credenciais de acesso (usuário/senha)")
    print("3. Verifique se o banco de dados 'railway' existe")
    print("4. Execute 'flask db upgrade' para aplicar as migrações")
    print("5. Verifique as configurações de rede e firewall")

if __name__ == "__main__":
    test_connection()
