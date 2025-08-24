import os
import sys

def main():
    print("Verificando variáveis de ambiente...\n")
    
    # Lista de variáveis de ambiente importantes para verificar
    env_vars = [
        'DATABASE_URL',
        'JWT_SECRET_KEY',
        'REDIS_URL',
        'SECRET_KEY',
        'FLASK_APP',
        'FLASK_ENV',
        'PYTHONPATH'
    ]
    
    # Verificar cada variável de ambiente
    for var in env_vars:
        value = os.environ.get(var, 'NÃO DEFINIDA')
        print(f"{var}: {value}")
    
    # Verificar se o Python pode importar os módulos necessários
    print("\nVerificando módulos Python...")
    try:
        import flask
        import psycopg2
        import sqlalchemy
        print("Módulos Python necessários estão instalados.")
    except ImportError as e:
        print(f"Erro ao importar módulos: {e}")
    
    # Verificar se o diretório src está no PYTHONPATH
    print("\nVerificando PYTHONPATH...")
    python_path = os.environ.get('PYTHONPATH', '')
    if 'src' in python_path:
        print("O diretório 'src' está no PYTHONPATH.")
    else:
        print("AVISO: O diretório 'src' NÃO está no PYTHONPATH.")
    
    # Verificar se o Flask está configurado corretamente
    flask_app = os.environ.get('FLASK_APP')
    if flask_app and os.path.exists(flask_app):
        print(f"\nArquivo FLASK_APP encontrado em: {flask_app}")
    elif flask_app:
        print(f"\nAVISO: Arquivo FLASK_APP não encontrado: {flask_app}")
    
    # Verificar se o ambiente está configurado
    flask_env = os.environ.get('FLASK_ENV', 'production')
    print(f"\nAmbiente Flask: {flask_env}")

if __name__ == "__main__":
    main()
