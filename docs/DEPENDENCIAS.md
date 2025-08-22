# 📦 Dependências do Projeto Tanque Cheio

Este documento lista todas as dependências necessárias para o projeto Tanque Cheio, separadas por serviço (backend e frontend).

## 🔧 Backend (Flask/Python)

### Dependências Principais

```bash
# Já instaladas no projeto
alembic==1.16.4
blinker==1.9.0
certifi==2025.8.3
charset-normalizer==3.4.3
click==8.2.1
Flask==3.1.1
flask-cors==6.0.0
Flask-JWT-Extended==4.7.1
Flask-Migrate==4.1.0
Flask-SQLAlchemy==3.1.1
googlemaps==4.10.0
greenlet==3.2.4
idna==3.10
itsdangerous==2.2.0
Jinja2==3.1.6
Mako==1.3.10
MarkupSafe==3.0.2
psycopg2-binary==2.9.10
PyJWT==2.10.1
python-dotenv==1.1.1
redis==6.4.0
requests==2.32.5
SQLAlchemy==2.0.41
typing_extensions==4.14.0
urllib3==2.5.0
Werkzeug==3.1.3
beautifulsoup4==4.12.3

# Dependências adicionais recomendadas
gunicorn==21.2.0
marshmallow==3.20.1
marshmallow-sqlalchemy==0.29.0

# Processamento geoespacial
geopy==2.4.1
haversine==2.8.0
shapely==2.0.2

# Integrações externas
openrouteservice==2.3.3

# Segurança e autenticação
bcrypt==4.0.1
passlib==1.7.4
cryptography==41.0.5

# Processamento assíncrono
celery==5.3.4
eventlet==0.33.3

# Utilitários
python-dateutil==2.8.2
pillow==10.1.0
validators==0.22.0
```

### Instalação do Backend

```bash
cd backend/tanque-cheio-backend
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 📱 Frontend (React)

### Dependências Principais

```json
{
  "dependencies": {
    "@hookform/resolvers": "^5.0.1",
    "@radix-ui/react-accordion": "^1.2.10",
    "@radix-ui/react-alert-dialog": "^1.1.13",
    "@radix-ui/react-aspect-ratio": "^1.1.6",
    "@radix-ui/react-avatar": "^1.1.9",
    "@radix-ui/react-checkbox": "^1.3.1",
    "@radix-ui/react-collapsible": "^1.1.10",
    "@radix-ui/react-context-menu": "^2.2.14",
    "@radix-ui/react-dialog": "^1.1.13",
    "@radix-ui/react-dropdown-menu": "^2.1.14",
    "@radix-ui/react-hover-card": "^1.1.13",
    "@radix-ui/react-label": "^2.1.6",
    "@radix-ui/react-menubar": "^1.1.14",
    "@radix-ui/react-navigation-menu": "^1.2.12",
    "@radix-ui/react-popover": "^1.1.13",
    "@radix-ui/react-progress": "^1.1.6",
    "@radix-ui/react-radio-group": "^1.3.6",
    "@radix-ui/react-scroll-area": "^1.2.8",
    "@radix-ui/react-select": "^2.2.4",
    "@radix-ui/react-separator": "^1.1.6",
    "@radix-ui/react-slider": "^1.3.4",
    "@radix-ui/react-slot": "^1.2.2",
    "@radix-ui/react-switch": "^1.2.4",
    "@radix-ui/react-tabs": "^1.1.11",
    "@radix-ui/react-toggle": "^1.1.8",
    "@radix-ui/react-toggle-group": "^1.1.9",
    "@radix-ui/react-tooltip": "^1.2.6",
    "@tailwindcss/vite": "^4.1.7",
    "@tanstack/react-query": "^4.35.3",
    "axios": "^1.5.0",
    "class-variance-authority": "^0.7.1",
    "clsx": "^2.1.1",
    "cmdk": "^1.1.1",
    "date-fns": "^4.1.0",
    "embla-carousel-react": "^8.6.0",
    "framer-motion": "^12.15.0",
    "input-otp": "^1.4.2",
    "jwt-decode": "^3.1.2",
    "leaflet": "^1.9.4",
    "lucide-react": "^0.510.0",
    "next-themes": "^0.4.6",
    "react": "^19.1.0",
    "react-day-picker": "8.10.1",
    "react-dom": "^19.1.0",
    "react-hook-form": "^7.56.3",
    "react-leaflet": "^4.2.1",
    "react-resizable-panels": "^3.0.2",
    "react-router-dom": "^7.6.1",
    "recharts": "^2.15.3",
    "sonner": "^2.0.3",
    "tailwind-merge": "^3.3.0",
    "tailwindcss": "^4.1.7",
    "tailwindcss-animate": "^1.0.7",
    "vaul": "^1.1.2",
    "zod": "^3.24.4",
    "zustand": "^4.4.1"
  },
  "devDependencies": {
    "@eslint/js": "^9.25.0",
    "@types/leaflet": "^1.9.4",
    "@types/node": "^20.6.2",
    "@types/react": "^19.1.2",
    "@types/react-dom": "^19.1.2",
    "@vitejs/plugin-react": "^4.4.1",
    "autoprefixer": "^10.4.15",
    "eslint": "^9.25.0",
    "eslint-plugin-react": "^7.33.2",
    "eslint-plugin-react-hooks": "^5.2.0",
    "eslint-plugin-react-refresh": "^0.4.19",
    "globals": "^16.0.0",
    "postcss": "^8.4.29",
    "tw-animate-css": "^1.2.9",
    "typescript": "^5.2.2",
    "vite": "^6.3.5",
    "vite-plugin-pwa": "^0.16.5"
  }
}
```

### Instalação do Frontend

```bash
cd frontend/tanque-cheio-app
npm install
# ou
yarn install
# ou
pnpm install
```

## 🗄️ Dependências do Sistema

Para o ambiente de produção, você também precisará:

1. **PostgreSQL 14+** (banco de dados)
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install postgresql postgresql-contrib
   
   # Verificar instalação
   psql --version
   ```

2. **Redis** (para tarefas em segundo plano e cache)
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install redis-server
   
   # Verificar instalação
   redis-cli ping
   # Deve responder com "PONG"
   ```

3. **Nginx** (servidor web para produção)
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install nginx
   
   # Verificar instalação
   nginx -v
   ```

4. **Certbot** (para certificados SSL)
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install certbot python3-certbot-nginx
   
   # Verificar instalação
   certbot --version
   ```

## 🔑 Chaves de API Necessárias

1. **Google Maps API Key** - Para geocodificação e integração com mapas
   - Obtenha em: https://console.cloud.google.com/
   - Serviços necessários:
     - Maps JavaScript API
     - Geocoding API
     - Places API
     - Directions API

2. **OpenRouteService API Key** - Para cálculos de rota alternativos
   - Obtenha em: https://openrouteservice.org/dev/#/signup

3. **ANP API Key** (se disponível) - Para dados oficiais de postos
   - Consulte a documentação da ANP para acesso aos dados

## 📦 Variáveis de Ambiente

Crie um arquivo `.env` em cada diretório (backend e frontend) com as seguintes variáveis:

### Backend (.env)
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

# Configuração Redis
REDIS_URL=redis://localhost:6379/0

# Configuração do servidor
FLASK_APP=src/main.py
FLASK_ENV=development
PORT=8080
```

### Frontend (.env)
```
VITE_API_URL=http://localhost:8080/api
VITE_GOOGLE_MAPS_API_KEY=sua_chave_google_maps
VITE_APP_VERSION=1.0.0
```

