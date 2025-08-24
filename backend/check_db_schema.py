import psycopg2
import sys

def check_schema():
    print("🔍 Verificando esquema do banco de dados...")
    
    # Configurações de conexão
    conn_params = {
        'dbname': 'railway',
        'user': 'postgres',
        'password': 'HXmzPSGlMEcjpzICIZphyTFuNLcGbAjL',
        'host': 'postgres-admt.railway.internal',
        'port': 5432
    }
    
    try:
        # Conectar ao banco de dados
        print(f"🔗 Conectando ao banco de dados {conn_params['dbname']} em {conn_params['host']}:{conn_params['port']}...")
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        
        # Verificar se o banco de dados existe
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (conn_params['dbname'],))
        if not cursor.fetchone():
            print(f"❌ O banco de dados '{conn_params['dbname']}' não existe.")
            return
        
        # Verificar se o esquema público existe
        cursor.execute("SELECT 1 FROM information_schema.schemata WHERE schema_name = 'public'")
        if not cursor.fetchone():
            print("❌ O esquema 'public' não existe no banco de dados.")
            return
        
        # Listar todas as tabelas no esquema público
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        
        if not tables:
            print("ℹ️  Nenhuma tabela encontrada no esquema público.")
            return
            
        print(f"\n📋 Tabelas encontradas ({len(tables)}):")
        for i, table in enumerate(tables, 1):
            print(f"{i:2d}. {table[0]}")
        
        # Verificar tabelas importantes
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
            
            # Verificar se as migrações foram aplicadas
            if 'alembic_version' in missing_tables:
                print("\nℹ️  A tabela 'alembic_version' não foi encontrada.")
                print("   Isso pode indicar que as migrações do banco de dados não foram aplicadas.")
                print("   Execute 'flask db upgrade' para aplicar as migrações.")
        else:
            print("\n✅ Todas as tabelas importantes estão presentes!")
        
        # Verificar se há dados nas tabelas de usuários
        if 'users' in [x[0] for x in tables]:
            cursor.execute("SELECT COUNT(*) FROM users;")
            user_count = cursor.fetchone()[0]
            print(f"\n👥 Total de usuários cadastrados: {user_count}")
        
        if 'gas_stations' in [x[0] for x in tables]:
            cursor.execute("SELECT COUNT(*) FROM gas_stations;")
            station_count = cursor.fetchone()[0]
            print(f"⛽ Total de postos cadastrados: {station_count}")
        
        # Verificar estrutura da tabela users
        if 'users' in [x[0] for x in tables]:
            print("\n🔍 Estrutura da tabela 'users':")
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'users'
                ORDER BY ordinal_position;
            """)
            print("\n   Coluna          | Tipo            | Pode ser nulo?")
            print("-" * 60)
            for col in cursor.fetchall():
                print(f"   {col[0]:<16} | {col[1]:<15} | {col[2]}")
        
        # Fechar conexão
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro ao verificar o esquema do banco de dados: {e}")
        print(f"Tipo de erro: {type(e).__name__}")
        
        if "does not exist" in str(e):
            print("\nℹ️  O banco de dados ou esquema especificado não existe.")
            print("   Verifique se o banco de dados 'railway' foi criado corretamente.")
        elif "permission denied" in str(e).lower():
            print("\n🔒 Erro de permissão. Verifique se o usuário tem permissão para acessar o banco de dados.")
        
        print("\n🔧 Dicas para solução de problemas:")
        print("1. Verifique se o banco de dados 'railway' existe")
        print("2. Execute 'flask db upgrade' para aplicar as migrações")
        print("3. Verifique as permissões do usuário 'postgres'")
        print("4. Verifique se o esquema 'public' existe e está acessível")

if __name__ == "__main__":
    check_schema()
