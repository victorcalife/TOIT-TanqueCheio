import os
import psycopg2
from urllib.parse import urlparse
import time

def test_railway_connection():
    print("🚂 Testando conexão com o banco de dados no Railway...")
    
    # Configurações de conexão do Railway
    db_url = os.environ.get('DATABASE_URL', 'postgresql://postgres:HXmzPSGlMEcjpzICIZphyTFuNLcGbAjL@postgres-admt.railway.internal:5432/railway')
    
    print(f"🔗 URL de conexão: {db_url}")
    
    try:
        # Parse da URL de conexão
        result = urlparse(db_url)
        
        # Configurações de conexão
        conn_params = {
            'dbname': result.path[1:],  # Remove a barra inicial
            'user': result.username,
            'password': result.password,
            'host': result.hostname,
            'port': result.port,
            'connect_timeout': 10
        }
        
        print("\n🔍 Parâmetros de conexão:")
        for key, value in conn_params.items():
            if key == 'password':
                print(f"   {key}: {'*' * len(value) if value else 'N/A'}")
            else:
                print(f"   {key}: {value}")
        
        # Tentar conectar ao banco de dados
        print("\n🔌 Tentando conectar ao banco de dados...")
        start_time = time.time()
        conn = psycopg2.connect(**conn_params)
        end_time = time.time()
        
        print(f"✅ Conexão bem-sucedida em {end_time - start_time:.2f} segundos!")
        
        # Criar cursor
        cursor = conn.cursor()
        
        # Verificar versão do PostgreSQL
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"\n📊 {version}")
        
        # Listar tabelas
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
        
        # Verificar tabelas importantes
        important_tables = ['users', 'user_profiles', 'gas_stations', 'fuel_prices']
        missing_tables = [t for t in important_tables if t not in [x[0] for x in tables]]
        
        if missing_tables:
            print(f"\n⚠️  Tabelas importantes ausentes: {', '.join(missing_tables)}")
        else:
            print("\n✅ Todas as tabelas importantes estão presentes!")
        
        # Fechar conexão
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"\n❌ Erro ao conectar ao banco de dados:")
        print(f"   {str(e)}")
        print("\n🔧 Possíveis soluções:")
        print("1. Verifique se o servidor PostgreSQL está em execução")
        print("2. Verifique as credenciais de acesso")
        print("3. Verifique se o firewall permite conexões na porta 5432")
        print("4. Verifique se o banco de dados 'railway' existe")
        print("5. Verifique se o usuário tem permissão de acesso")
        print("6. Verifique a configuração de rede e DNS")

if __name__ == "__main__":
    test_railway_connection()
