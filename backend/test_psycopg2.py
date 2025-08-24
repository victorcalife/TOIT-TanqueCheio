import psycopg2

print("Testando conexão com psycopg2...")

try:
    # Tentar importar o psycopg2
    import psycopg2
    print("✅ psycopg2 está instalado corretamente.")
    
    # Verificar versão do psycopg2
    print(f"📦 Versão do psycopg2: {psycopg2.__version__}")
    
    # Testar conexão básica
    print("\n🔍 Testando conexão com o banco de dados...")
    
    # Configurações de conexão
    conn_params = {
        'dbname': 'railway',
        'user': 'postgres',
        'password': 'HXmzPSGlMEcjpzICIZphyTFuNLcGbAjL',
        'host': 'postgres-admt.railway.internal',
        'port': 5432,
        'connect_timeout': 5
    }
    
    # Tentar conectar ao banco de dados
    print(f"🔗 Conectando ao banco de dados {conn_params['dbname']} em {conn_params['host']}:{conn_params['port']}...")
    conn = psycopg2.connect(**conn_params)
    
    # Criar cursor
    cursor = conn.cursor()
    
    # Testar conexão
    cursor.execute("SELECT 1")
    result = cursor.fetchone()
    
    if result[0] == 1:
        print("✅ Conexão bem-sucedida! O banco de dados está respondendo.")
    
    # Fechar conexão
    cursor.close()
    conn.close()
    
    print("\n🎉 Teste concluído com sucesso!")
    
except ImportError:
    print("❌ O psycopg2 não está instalado. Instale-o com: pip install psycopg2-binary")
    
except Exception as e:
    print(f"\n❌ Erro durante o teste: {e}")
    print(f"Tipo de erro: {type(e).__name__}")
    
    if "password authentication failed" in str(e).lower():
        print("\n🔒 Erro de autenticação. Verifique as credenciais de acesso.")
    elif "could not connect" in str(e).lower():
        print("\n🔌 Erro de conexão. Verifique se o servidor PostgreSQL está em execução e acessível.")
    elif "timeout expired" in str(e).lower():
        print("\n⏱️  Tempo limite de conexão excedido. Verifique a conectividade de rede.")
    
    print("\n🔧 Dicas para solução de problemas:")
    print("1. Verifique se o servidor PostgreSQL está em execução")
    print("2. Verifique as credenciais de acesso (usuário/senha)")
    print("3. Verifique se o banco de dados 'railway' existe")
    print("4. Verifique as configurações de rede e firewall")
