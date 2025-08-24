import os
import sys
import psycopg2
from urllib.parse import urlparse

def check_database():
    print("🔍 Verificando conexão com o banco de dados...")
    
    # Configurações de conexão
    db_config = {
        'dbname': 'railway',
        'user': 'postgres',
        'password': 'HXmzPSGlMEcjpzICIZphyTFuNLcGbAjL',
        'host': 'postgres-admt.railway.internal',
        'port': '5432',
        'connect_timeout': 5
    }
    
    try:
        # Tentar conectar ao banco de dados
        print(f"🔗 Conectando ao banco de dados em {db_config['host']}:{db_config['port']}...")
        conn = psycopg2.connect(**db_config)
        
        # Criar cursor
        cur = conn.cursor()
        
        # Verificar versão do PostgreSQL
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]
        print(f"✅ Conexão bem-sucedida!")
        print(f"📊 {version}")
        
        # Listar tabelas
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        tables = cur.fetchall()
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
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"\n❌ Erro ao conectar ao banco de dados:")
        print(f"   {str(e)}")
        print("\n🔧 Possíveis soluções:")
        print("1. Verifique se o servidor PostgreSQL está em execução")
        print("2. Verifique as credenciais de acesso")
        print("3. Verifique se o firewall permite conexões na porta 5432")
        print("4. Verifique se o banco de dados 'railway' existe")
        print("5. Verifique se o usuário 'postgres' tem permissão de acesso")

if __name__ == "__main__":
    check_database()
