# Tanque Cheio - Implementação Completa

## 🚀 Aplicativo de Indicação de Menores Preços de Combustíveis

### Visão Geral
O **Tanque Cheio** é um aplicativo web que ajuda motoristas a encontrar os postos de combustível com menores preços ao longo de suas rotas. A aplicação calcula automaticamente desvios, economia potencial e fornece recomendações inteligentes baseadas em múltros fatores.

### ✅ Funcionalidades Implementadas

#### Backend (Flask)
- **API REST completa** com endpoints para:
  - Gerenciamento de postos de combustível
  - Controle de preços por tipo de combustível
  - Cálculo inteligente de recomendações de rota
  - Busca avançada por proximidade e preços
  - Health check e monitoramento

#### Frontend (React)
- **Interface moderna e responsiva** com:
  - Formulário intuitivo para origem e destino
  - Exibição detalhada das informações da rota
  - Cards elegantes com recomendações de postos
  - Indicadores visuais de economia e scores
  - Design mobile-first com Tailwind CSS

#### Algoritmo de Recomendação
- Cálculo de distância usando fórmula de Haversine
- Análise de desvio de rota e tempo adicional
- Estimativa de economia real de combustível
- Score ponderado considerando múltiplos fatores
- Filtragem por raio máximo de desvio

### 🏗️ Arquitetura Técnica

#### Backend
- **Framework**: Flask 3.1.1
- **Banco de Dados**: SQLite com SQLAlchemy ORM
- **APIs**: RESTful com JSON responses
- **CORS**: Habilitado para integração frontend
- **Estrutura**: Modular com blueprints

#### Frontend
- **Framework**: React 18 com Vite
- **UI Components**: shadcn/ui + Tailwind CSS
- **Icons**: Lucide React
- **Build**: Otimizado para produção
- **Responsividade**: Mobile-first design

#### Integração
- **Full-stack**: Frontend servido pelo Flask
- **APIs**: Comunicação via fetch API
- **Deploy**: Aplicação única integrada

### 📊 Modelos de Dados

#### GasStation (Postos)
```python
- id: UUID único
- name: Nome do posto
- brand: Marca (Shell, Petrobras, etc.)
- address: Endereço completo
- latitude/longitude: Coordenadas GPS
- amenities: Comodidades disponíveis
- operating_hours: Horários de funcionamento
```

#### FuelPrice (Preços)
```python
- id: UUID único
- gas_station_id: Referência ao posto
- fuel_type: Tipo de combustível
- price: Preço por litro
- source: Fonte da informação
- source_confidence: Confiabilidade (0-1)
- reported_at: Data/hora do preço
- is_active: Status ativo/inativo
```

#### Route (Rotas)
```python
- id: UUID único
- origin/destination: Coordenadas de origem e destino
- distance_km: Distância total
- estimated_fuel_needed: Combustível estimado
- preferences: Preferências do usuário
```

### 🔧 APIs Disponíveis

#### Postos de Combustível
- `POST /api/gas-stations` - Criar novo posto
- `GET /api/gas-stations` - Listar postos
- `GET /api/gas-stations/{id}` - Obter posto específico
- `POST /api/gas-stations/{id}/prices` - Adicionar preço
- `GET /api/gas-stations/{id}/prices` - Obter preços

#### Recomendações
- `POST /api/recommendations/calculate` - Calcular recomendações de rota

#### Busca Avançada
- `GET /api/search/nearby` - Postos próximos a uma localização
- `GET /api/search/cheapest` - Postos com combustível mais barato
- `GET /api/search/brands` - Marcas disponíveis
- `GET /api/search/cities` - Cidades com postos

### 🧮 Algoritmo de Score

O score de recomendação é calculado considerando:

1. **Economia de preço** (peso: 40%)
2. **Distância de desvio** (peso: 30%)
3. **Tempo adicional** (peso: 20%)
4. **Confiabilidade da fonte** (peso: 10%)

```python
score = (
    price_score * 0.4 +
    distance_score * 0.3 +
    time_score * 0.2 +
    confidence_score * 0.1
)
```

### 🚀 Como Executar

#### Desenvolvimento
```bash
# Backend
cd backend/tanque-cheio-api
source venv/bin/activate
python src/main.py

# Frontend (desenvolvimento separado)
cd frontend/tanque-cheio-app
pnpm run dev
```

#### Produção (Integrado)
```bash
# Build do frontend
cd frontend/tanque-cheio-app
pnpm run build

# Copiar para Flask
cp -r dist/* ../../backend/tanque-cheio-api/src/static/

# Executar aplicação integrada
cd backend/tanque-cheio-api
source venv/bin/activate
python src/main.py
```

### 📱 Interface do Usuário

#### Tela Principal
- Campo de origem com ícone de localização
- Campo de destino com ícone de localização
- Botão "Encontrar postos na rota"
- Estado vazio elegante quando sem dados

#### Resultados
- **Informações da Rota**: Distância, combustível estimado, postos encontrados
- **Cards de Recomendação**: 
  - Nome e endereço do posto
  - Marca e preço por litro
  - Métricas: desvio, tempo extra, economia, score
  - Comodidades disponíveis
  - Indicadores visuais coloridos

### 🎯 Próximos Passos

#### Melhorias Sugeridas
1. **Integração com APIs de Mapas** (Google Maps, OpenStreetMap)
2. **Geocoding automático** para endereços
3. **Histórico de rotas** e favoritos
4. **Notificações push** para preços baixos
5. **Sistema de usuários** e personalização
6. **Dados em tempo real** via web scraping
7. **Aplicativo mobile nativo** (React Native)

#### Escalabilidade
1. **Banco de dados PostgreSQL** para produção
2. **Cache Redis** para consultas frequentes
3. **CDN** para assets estáticos
4. **Load balancer** para múltiplas instâncias
5. **Monitoramento** e logs estruturados

### 📄 Licença
Este projeto foi desenvolvido como MVP demonstrativo do conceito Tanque Cheio.

---

**Desenvolvido com ❤️ usando Flask + React**

