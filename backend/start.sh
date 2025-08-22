#!/bin/bash

# Navegar para o diretório src
cd "$(dirname "$0")/src"

# Ativar o ambiente virtual (se existir)
if [ -d "../venv" ]; then
    echo "Ativando ambiente virtual..."
    source ../venv/Scripts/activate
fi

# Instalar dependências
echo "Instalando dependências..."
pip install -r ../requirements.txt

# Executar migrações do banco de dados
echo "Executando migrações do banco de dados..."
flask db upgrade

# Popular o banco de dados com dados iniciais (se necessário)
echo "Verificando dados iniciais..."
python -c "from database_postgres import populate_sample_data; from main import create_app; app = create_app(); with app.app_context(): populate_sample_data()"

# Iniciar o servidor Gunicorn
echo "Iniciando o servidor Gunicorn..."
exec gunicorn --bind 0.0.0.0:$PORT --workers 4 --timeout 120 main:create_app
