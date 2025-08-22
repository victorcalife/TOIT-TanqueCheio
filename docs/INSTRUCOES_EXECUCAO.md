# 🚀 Instruções de Execução do Projeto Tanque Cheio

Este documento contém instruções detalhadas para configurar e executar o projeto Tanque Cheio em ambiente de desenvolvimento e produção.

## 📋 Pré-requisitos

- Python 3.8+ instalado
- Node.js 16+ instalado
- PostgreSQL 14+ instalado e configurado
- Redis (opcional, para tarefas em segundo plano)

## 🔧 Configuração do Backend (Flask)

### 1. Instalação de Dependências

```bash
# Navegar até o diretório do backend
cd backend

# Instalar dependências
pip install -r requirements_minimal.txt
```

### 2. Configuração do Ambiente

Crie um arquivo `.env` no diretório do backend com o seguinte conteúdo:

```
# Configuração do banco de dados
DATABASE_URL=postgresql://username:password@localhost:5432/tanque_cheio
TEST_DATABASE_URL=postgresql://username:password@localhost:5432/tanque_cheio_test

# Configuração JWT
JWT_SECRET_KEY=seu_segredo_super_secreto
JWT_ACCESS_TOKEN_EXPIRES=86400

# APIs externas
GOOGLE_MAPS_API_KEY=sua_chave_google_maps
OPENROUTE_API_KEY=sua_chave_openroute

# Configuração do servidor
FLASK_APP=src/main.py
FLASK_ENV=development
PORT=8080
```

Substitua os valores acima pelos seus próprios valores.

### 3. Configuração do Banco de Dados

Execute os scripts SQL de migração no PostgreSQL:

```bash
# Usando psql
psql -U seu_usuario -d tanque_cheio -f database/migrations/000_run_all_migrations.sql

# Ou usando o cliente PostgreSQL de sua preferência (TablePlus, pgAdmin, etc.)
# Importe e execute o arquivo database/migrations/000_run_all_migrations.sql
```

### 4. Executando o Backend

```bash
# Modo desenvolvimento
python src/main.py

# Ou para produção com Gunicorn
gunicorn -w 4 -b 0.0.0.0:8080 "src.main:app"
```

O backend estará disponível em `http://localhost:8080`.

## 📱 Configuração do Frontend (React)

### 1. Instalação de Dependências

```bash
# Navegar até o diretório do frontend
cd frontend

# Instalar dependências
npm install
# Ou se houver conflitos:
npm install --legacy-peer-deps
```

### 2. Configuração do Ambiente

Crie um arquivo `.env` no diretório do frontend com o seguinte conteúdo:

```
VITE_API_URL=http://localhost:8080/api
VITE_GOOGLE_MAPS_API_KEY=sua_chave_google_maps
VITE_APP_VERSION=1.0.0
```

### 3. Executando o Frontend

```bash
# Modo desenvolvimento
npm run dev

# Build para produção
npm run build
```

O frontend de desenvolvimento estará disponível em `http://localhost:5173`.

## 🚀 Execução Completa do Projeto

Para executar o projeto completo, você precisará iniciar tanto o backend quanto o frontend:

```bash
# Terminal 1 - Backend
cd backend
python src/main.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

## 🔐 Usuários de Teste

O sistema vem pré-configurado com os seguintes usuários de teste:

1. **Admin:** admin@tanquecheio.app (senha: 241286)
2. **Motorista:** joao.motorista@gmail.com (senha: 241286)
3. **Caminhoneiro:** carlos.caminhoneiro@gmail.com (senha: 241286)
4. **Motociclista:** ana.moto@gmail.com (senha: 241286)

## 🌐 Deploy em Produção

### Backend (Flask)

Para deploy em produção, recomendamos usar Gunicorn com Nginx:

```bash
# Instalar Gunicorn
pip install gunicorn

# Executar com Gunicorn
gunicorn -w 4 -b 127.0.0.1:8080 "src.main:app"
```

Configure o Nginx para proxy reverso:

```nginx
server {
    listen 80;
    server_name seu-dominio.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Frontend (React)

Para deploy do frontend:

```bash
# Build de produção
cd frontend
npm run build

# Os arquivos estáticos estarão na pasta 'dist'
```

Configure o Nginx para servir os arquivos estáticos:

```nginx
server {
    listen 80;
    server_name seu-dominio-frontend.com;
    root /caminho/para/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

## 🔍 Solução de Problemas

### Conflitos de Dependências no Frontend

Se encontrar conflitos de dependências ao instalar pacotes no frontend:

```bash
npm install --legacy-peer-deps
# ou
npm install --force
```

### Erros de Conexão com o Banco de Dados

Verifique se:
1. O PostgreSQL está em execução
2. As credenciais no arquivo `.env` estão corretas
3. O banco de dados `tanque_cheio` existe

```bash
# Criar banco de dados manualmente
psql -U postgres -c "CREATE DATABASE tanque_cheio;"
```

### Problemas com CORS

Se encontrar erros de CORS, verifique se o backend está configurado corretamente:

```python
# No arquivo src/main.py
from flask_cors import CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})
```

## 📞 Suporte

Para suporte adicional, entre em contato com a equipe de desenvolvimento.

