import os
import sys
from flask import jsonify

# Adiciona o diretório src ao path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Importa e cria a aplicação
from main import app as application

# Configura o app para produção
application.config['ENV'] = 'production'
application.config['DEBUG'] = False

print("✅ Aplicação WSGI configurada com sucesso na raiz do projeto")
