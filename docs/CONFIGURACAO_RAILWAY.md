# 🚂 Configuração Completa para Railway

Este guia detalha como configurar todos os serviços do projeto Tanque Cheio na Railway, incluindo banco de dados PostgreSQL, backend Flask e frontend React.

## 📋 Visão Geral da Arquitetura

O projeto Tanque Cheio na Railway consiste em três serviços principais:

1. **PostgreSQL** - Banco de dados
2. **Backend Flask** - API REST
3. **Frontend React** - Interface de usuário

Cada serviço é implantado como um serviço separado na Railway, permitindo escalabilidade e gerenciamento independentes.

## 🔧 Configuração do Banco de Dados PostgreSQL

### Passo 1: Criar um novo serviço PostgreSQL
1. No dashboard da Railway, clique em "New Project" ou "Add Service"
2. Selecione "Database" e depois "PostgreSQL"
3. Aguarde a criação do banco de dados

### Passo 2: Configurar variáveis de ambiente
1. Vá para a aba "Variables" do serviço PostgreSQL
2. Anote as seguintes variáveis que serão usadas pelo backend:
   - `PGDATABASE`
   - `PGHOST`
   - `PGPASSWORD`
   - `PGPORT`
   - `PGUSER`

### Passo 3: Executar migrações
1. Conecte-se ao banco de dados usando TablePlus ou outro cliente SQL
2. Execute o script `000_run_all_migrations.sql` para criar todas as tabelas
3. Alternativamente, execute os scripts de migração individuais na ordem numérica

## 🔧 Configuração do Backend Flask

### Passo 1: Criar um novo serviço para o backend
1. No dashboard da Railway, clique em "New Service"
2. Selecione "GitHub Repo" e escolha seu repositório
3. Configure para usar o diretório `/backend`

### Passo 2: Configurar variáveis de ambiente
1. Vá para a aba "Variables" do serviço backend
2. Adicione as seguintes variáveis:
   ```
   DATABASE_URL=postgresql://${PGUSER}:${PGPASSWORD}@${PGHOST}:${PGPORT}/${PGDATABASE}
   JWT_SECRET_KEY=seu_segredo_super_secreto
   FLASK_APP=src/main.py
   PORT=8080
   GOOGLE_MAPS_API_KEY=sua_chave_google_maps
   ```

3. Vincule as variáveis do PostgreSQL:
   - Clique em "Reference another service's variables"
   - Selecione o serviço PostgreSQL
   - Selecione todas as variáveis PG*

### Passo 3: Configurar o deploy
1. Certifique-se de que os arquivos `Procfile` e `railway.json` estão no diretório `/backend`
2. Verifique se o arquivo `requirements_railway.txt` está presente
3. Na aba "Settings", configure:
   - Build Command: `pip install -r requirements_railway.txt`
   - Start Command: `gunicorn src.main:app`

## 🔧 Configuração do Frontend React

### Passo 1: Criar um novo serviço para o frontend
1. No dashboard da Railway, clique em "New Service"
2. Selecione "GitHub Repo" e escolha seu repositório
3. Configure para usar o diretório `/frontend`

### Passo 2: Configurar variáveis de ambiente
1. Vá para a aba "Variables" do serviço frontend
2. Adicione as seguintes variáveis:
   ```
   VITE_API_URL=https://[URL-DO-BACKEND-RAILWAY]/api
   VITE_GOOGLE_MAPS_API_KEY=sua_chave_google_maps
   NODE_VERSION=18.17.0
   ```

### Passo 3: Configurar o deploy
1. Certifique-se de que o arquivo `railway.json` está no diretório `/frontend`
2. Certifique-se de que o `package.json` inclui a dependência `serve` e o script `start`
3. Na aba "Settings", configure:
   - Build Command: `npm install && npm run build`
   - Start Command: `npx serve -s dist`

## 🔗 Configuração de Domínios

### Backend
1. Vá para a aba "Settings" do serviço backend
2. Em "Domains", gere um domínio personalizado ou use o fornecido pela Railway
3. Anote este URL para configurar o frontend

### Frontend
1. Vá para a aba "Settings" do serviço frontend
2. Em "Domains", gere um domínio personalizado ou use o fornecido pela Railway
3. Este será o URL público do seu aplicativo

## 🔄 Configuração de Ambientes (Desenvolvimento/Produção)

### Opção 1: Projetos Separados
- Crie dois projetos Railway separados: "Tanque Cheio Dev" e "Tanque Cheio Prod"
- Configure cada um seguindo os passos acima

### Opção 2: Ambientes no Mesmo Projeto
1. No dashboard da Railway, vá para "Settings" do projeto
2. Clique em "New Environment"
3. Nomeie como "production"
4. Duplique todos os serviços do ambiente "development" para "production"
5. Ajuste as variáveis de ambiente conforme necessário

## 🔍 Monitoramento e Logs

1. Acesse a aba "Metrics" de cada serviço para monitorar:
   - Uso de CPU
   - Uso de memória
   - Requisições por minuto
   - Tempo de resposta

2. Acesse a aba "Logs" para visualizar logs em tempo real e solucionar problemas

## 🚀 Atualizações e Implantações Contínuas

### Configuração de CI/CD
1. Cada push para a branch `main` pode acionar automaticamente um deploy
2. Configure na aba "Settings" > "Deployments"
3. Selecione "Deploy on push" e escolha a branch `main`

### Deploy Manual
1. Vá para a aba "Deployments" do serviço
2. Clique em "Deploy Now"
3. Selecione a branch a ser implantada

## 📊 Escalabilidade

Se necessário, você pode escalar verticalmente cada serviço:

1. Vá para a aba "Settings" do serviço
2. Em "Instance Size", selecione um plano com mais recursos

## 🔒 Segurança

1. Mantenha o `JWT_SECRET_KEY` seguro e único para cada ambiente
2. Restrinja o acesso às variáveis de ambiente apenas a membros da equipe
3. Configure CORS no backend para permitir apenas domínios confiáveis

## 🆘 Solução de Problemas

### Problemas de Conexão com o Banco de Dados
- Verifique se as variáveis de ambiente do PostgreSQL estão corretamente vinculadas
- Teste a conexão usando o comando `psql` no terminal do serviço backend

### Problemas de Build do Frontend
- Verifique se o Node.js está na versão correta (variável `NODE_VERSION`)
- Verifique se todas as dependências estão no `package.json`

### Problemas de API
- Verifique os logs do serviço backend
- Teste os endpoints usando o Postman ou curl

