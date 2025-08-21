# TODO - Tanque Cheio - Sistema GPS Automático

## ✅ CONCLUÍDO - MVP Backend/Frontend
- [x] Backend API completo em produção: https://kkh7ikcy300m.manus.space
- [x] Sistema de autenticação JWT funcional
- [x] Algoritmo de recomendações inteligente
- [x] Frontend React com interface completa
- [x] 6 APIs REST testadas e funcionais
- [x] Deploy em produção estável

## 🎯 FASE ATUAL: SISTEMA GPS AUTOMÁTICO

### 1. Google Maps API Integration (PRIORIDADE ALTA)
- [ ] Configurar Google Maps API key
- [ ] Implementar geocoding de endereços reais
- [ ] Calcular rotas reais (não apenas distância linear)
- [ ] Obter pontos da rota para monitoramento
- [ ] Testar com rotas reais (Balneário Camboriú → São Paulo)

### 2. Sistema de Monitoramento GPS (CRÍTICO)
- [ ] API para iniciar/parar monitoramento de viagem
- [ ] Endpoint para receber atualizações de GPS
- [ ] Lógica de cálculo de distância percorrida
- [ ] Detecção automática de intervalos (100km, 200km, etc.)
- [ ] Histórico de pontos GPS da viagem

### 3. Sistema de Notificações Push (CRÍTICO)
- [ ] Configurar Firebase Cloud Messaging
- [ ] Service Worker para notificações
- [ ] API para enviar notificações
- [ ] Template de notificação: "Posto [Nome] - R$ [Preço] - [Distância]km à frente"
- [ ] Sistema de agendamento de notificações

### 4. Perfil GPS do Usuário (ESSENCIAL)
- [ ] Interface para configurar combustível preferido
- [ ] Configuração de intervalo de notificação (100km, 200km, 300km)
- [ ] Ativar/desativar monitoramento GPS
- [ ] Histórico de viagens e economia
- [ ] Configurações de privacidade

### 5. Sistema de Cupons/Vouchers
- [ ] Modelo de cupons no banco de dados
- [ ] API para gerenciar cupons por posto
- [ ] Validação de cupons por tipo de combustível
- [ ] Integração com notificações (incluir cupom se disponível)
- [ ] Interface para visualizar cupons disponíveis

## 🔄 PRÓXIMAS 2 HORAS - IMPLEMENTAÇÃO IMEDIATA

### Tarefa 1: Google Maps API (30 min)
```python
# Implementar em /api/maps/geocode
# Implementar em /api/maps/route
# Testar com endereços reais
```

### Tarefa 2: APIs GPS Tracking (45 min)
```python
# POST /api/gps/start-trip
# POST /api/gps/update-location
# POST /api/gps/stop-trip
# GET /api/gps/trip-status
```

### Tarefa 3: Sistema de Notificações (30 min)
```python
# POST /api/notifications/send
# Lógica de detecção de intervalos
# Template de mensagens
```

### Tarefa 4: Interface GPS (15 min)
```javascript
// Componente de configuração GPS
// Monitoramento em tempo real
// Histórico de viagens
```

## 📋 ESPECIFICAÇÃO TÉCNICA DETALHADA

### Fluxo GPS Automático:
1. **Usuário configura perfil:**
   - Combustível: Gasolina
   - Intervalo: 100km
   - Status: Ativo

2. **Usuário inicia viagem:**
   - POST /api/gps/start-trip
   - Origem: Balneário Camboriú, SC
   - Destino: São Paulo, SP

3. **App monitora GPS:**
   - A cada 30 segundos: POST /api/gps/update-location
   - Backend calcula distância percorrida
   - Quando atinge 100km → trigger notificação

4. **Sistema envia notificação:**
   - Busca postos nos próximos 100km da rota
   - Encontra mais barato: "Posto Shell - R$ 5,75"
   - Envia push: "⛽ Posto Shell - R$ 5,75/L - 2km à frente"

### Estrutura de Dados GPS:
```python
trip = {
    'id': uuid,
    'user_id': uuid,
    'origin': 'Balneário Camboriú, SC',
    'destination': 'São Paulo, SP',
    'fuel_type': 'gasoline',
    'notification_interval': 100,  # km
    'distance_traveled': 0,
    'last_notification_km': 0,
    'status': 'active',
    'route_points': [...],  # Google Maps route
    'gps_history': [...]
}
```

## 🎯 CRITÉRIOS DE SUCESSO

### Teste Final:
1. Configurar perfil: Gasolina, 100km
2. Iniciar viagem: Balneário Camboriú → São Paulo
3. Simular GPS updates a cada 30s
4. Verificar notificação automática aos 100km
5. Validar recomendação de posto mais barato

### Métricas:
- [ ] Notificação enviada automaticamente
- [ ] Posto recomendado é realmente o mais barato
- [ ] Distância calculada corretamente
- [ ] Interface GPS funcional
- [ ] Histórico de viagem salvo

## 📁 ARQUIVOS A CRIAR/ATUALIZAR

### Backend:
- [ ] `/api/maps/` - Google Maps integration
- [ ] `/api/gps/` - GPS tracking APIs
- [ ] `/api/notifications/` - Push notifications
- [ ] `models/trip.py` - Modelo de viagem
- [ ] `services/gps_service.py` - Lógica GPS

### Frontend:
- [ ] `components/GPSConfig.jsx` - Configuração GPS
- [ ] `components/TripMonitor.jsx` - Monitoramento
- [ ] `contexts/GPSContext.jsx` - Estado GPS
- [ ] `services/gps.js` - Integração GPS

## 🔧 FERRAMENTAS NECESSÁRIAS

### APIs Externas:
- **Google Maps API** - Geocoding e rotas
- **Firebase FCM** - Push notifications
- **Geolocation API** - GPS do browser

### Bibliotecas:
- **googlemaps** (Python) - Google Maps client
- **firebase-admin** (Python) - FCM server
- **workbox** (JS) - Service Worker

## ⚡ IMPLEMENTAÇÃO IMEDIATA

Vou começar implementando:
1. Google Maps API integration
2. Sistema básico de GPS tracking
3. Lógica de detecção de intervalos
4. Notificações automáticas

**Status:** 🚀 **INICIANDO DESENVOLVIMENTO GPS**

