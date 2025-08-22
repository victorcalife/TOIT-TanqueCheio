# Backend do Tanque Cheio

Este é o backend da aplicação Tanque Cheio, desenvolvido em Python com Flask e PostgreSQL.

## Requisitos

- Python 3.8+
- PostgreSQL
- pip

## Configuração do Ambiente

1. Clone o repositório
2. Crie um ambiente virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # No Windows: venv\Scripts\activate
   ```
3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure as variáveis de ambiente no arquivo `.env`

## Executando em Desenvolvimento

```bash
flask run --port 5000
```

## Executando em Produção

1. Certifique-se de que todas as migrações foram aplicadas:
   ```bash
   flask db upgrade
   ```

2. Inicie o servidor com Gunicorn:
   ```bash
   gunicorn --bind 0.0.0.0:$PORT --workers 4 --timeout 120 src.main:create_app
   ```

Ou use o script de inicialização:

```bash
chmod +x start.sh
./start.sh
```

## Variáveis de Ambiente

- `DATABASE_URL`: URL de conexão com o banco de dados PostgreSQL
- `JWT_SECRET_KEY`: Chave secreta para geração de tokens JWT
- `GOOGLE_MAPS_API_KEY`: Chave da API do Google Maps
- `FLASK_ENV`: Ambiente de execução (development/production)

## Migrações do Banco de Dados

Para criar uma nova migração:
```bash
flask db migrate -m "Descrição da migração"
```

Para aplicar migrações pendentes:
```bash
flask db upgrade
```

Para reverter uma migração:
```bash
flask db downgrade
```
