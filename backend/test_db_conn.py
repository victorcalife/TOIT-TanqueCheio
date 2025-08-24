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
        'port': 5432
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
        
        print("\n🔧 Informações adicionais:")
        print(f"- Mensagem de erro: {e}")
        print(f"- Tipo de erro: {type(e).__name__}")
        print("\n📌 Dicas para solução de problemas:")
        print("1. Verifique se o servidor PostgreSQL está em execução")
        print("2. Verifique as credenciais de acesso (usuário/senha)")
        print("3. Verifique se o firewall permite conexões na porta 5432")
        print("4. Verifique se o banco de dados 'railway' existe")
        print("5. Verifique se o host 'postgres-admt.railway.internal' está acessível")
        
        # Verificar se o host está acessível
        try:
            import socket
            host = conn_params['host']
            port = conn_params['port']
            print(f"\n🔍 Verificando acessibilidade do host {host}:{port}...")
            
            # Tentar resolver o nome do host
            try:
                ip = socket.gethostbyname(host)
                print(f"- Host resolvido para: {ip}")
                
                # Tentar conectar via socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)  # Timeout de 5 segundos
                
                try:
                    result = sock.connect_ex((ip, port))
                    if result == 0:
                        print(f"✅ A porta {port} está aberta e acessível em {host}")
                    else:
                        print(f"❌ A porta {port} está fechada ou inacessível em {host} (código: {result})")
                        print("   - Verifique se o servidor PostgreSQL está em execução")
                        print(f"   - Verifique se o firewall permite conexões na porta {port}")
                except socket.error as e:
                    print(f"❌ Erro ao tentar conectar a {host}:{port}: {e}")
                finally:
                    sock.close()
                    
            except socket.gaierror as e:
                print(f"❌ Não foi possível resolver o nome do host '{host}': {e}")
                print("   - Verifique a conectividade de rede")
                print("   - Verifique se o nome do host está correto")
                
        except Exception as e:
            print(f"⚠️  Não foi possível verificar a acessibilidade do host: {e}")

if __name__ == "__main__":
    test_connection()
