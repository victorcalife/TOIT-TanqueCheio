"""
WSGI config for backend.
It exposes the WSGI callable as a module-level variable named ``application``.
"""
import os
from main import create_app

# Cria a aplicação usando a configuração de produção
app = create_app('production')

# Wrapper para compatibilidade com Gunicorn
def application(environ, start_response):
    return app(environ, start_response)

if __name__ == "__main__":
    # Isso é útil para desenvolvimento local, mas não deve ser usado em produção
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
