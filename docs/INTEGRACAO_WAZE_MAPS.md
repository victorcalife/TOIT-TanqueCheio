# 🗺️ INTEGRAÇÃO COM WAZE E GOOGLE MAPS - TANQUE CHEIO

## 📋 **Visão Geral**

O sistema Tanque Cheio implementa uma integração avançada com aplicativos de navegação (Waze, Google Maps) para identificar postos de combustível ao longo da rota do motorista e recomendar os melhores preços em tempo real.

## 🔍 **Como Funciona**

### **1. Detecção de Aplicativo de Navegação**

O sistema detecta automaticamente qual aplicativo de navegação está sendo usado:

```javascript
// Trecho do código frontend/src/services/NavigationDetector.js
export const detectNavigationApp = async () => {
  try {
    // Verifica apps instalados
    const installedApps = await AppDetector.getInstalledApps();
    
    // Verifica qual está em uso
    if (installedApps.includes('com.waze')) {
      const isActive = await AppDetector.isAppActive('com.waze');
      if (isActive) return 'waze';
    }
    
    if (installedApps.includes('com.google.android.apps.maps')) {
      const isActive = await AppDetector.isAppActive('com.google.android.apps.maps');
      if (isActive) return 'google_maps';
    }
    
    return 'unknown';
  } catch (error) {
    console.error('Erro ao detectar app de navegação:', error);
    return 'unknown';
  }
};
```

### **2. Extração da Rota Atual**

#### **2.1 Integração com Waze**

Utilizamos a Waze Transport API para extrair a rota atual:

```python
# Trecho do código backend/src/services/waze_integration.py
def get_current_route(user_id):
    """Obtém a rota atual do usuário no Waze"""
    try:
        # Obter último ponto GPS do usuário
        last_point = GPSTracking.query.filter_by(user_id=user_id).order_by(GPSTracking.timestamp.desc()).first()
        
        if not last_point:
            return None
            
        # Parâmetros para a API do Waze
        params = {
            'lat': last_point.latitude,
            'lon': last_point.longitude,
            'format': 'json'
        }
        
        # Chamada à API do Waze
        response = requests.get(WAZE_API_URL + '/current-route', params=params)
        
        if response.status_code == 200:
            route_data = response.json()
            
            # Extrair pontos da rota
            route_points = []
            for segment in route_data['response']['segments']:
                for point in segment['points']:
                    route_points.append({
                        'latitude': point['lat'],
                        'longitude': point['lon'],
                        'order': len(route_points)
                    })
            
            # Salvar pontos da rota no banco
            save_route_points(user_id, route_points)
            
            return route_points
        else:
            logger.error(f"Erro ao obter rota do Waze: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Exceção ao obter rota do Waze: {str(e)}")
        return None
```

#### **2.2 Integração com Google Maps**

Utilizamos a Google Maps Directions API:

```python
# Trecho do código backend/src/services/google_maps_integration.py
def get_current_route(user_id):
    """Obtém a rota atual do usuário no Google Maps"""
    try:
        # Obter último ponto GPS e destino configurado
        last_point = GPSTracking.query.filter_by(user_id=user_id).order_by(GPSTracking.timestamp.desc()).first()
        user_trip = Trip.query.filter_by(user_id=user_id, status='active').first()
        
        if not last_point or not user_trip:
            return None
            
        # Parâmetros para a API do Google Maps
        params = {
            'origin': f"{last_point.latitude},{last_point.longitude}",
            'destination': f"{user_trip.destination_lat},{user_trip.destination_lng}",
            'key': GOOGLE_MAPS_API_KEY
        }
        
        # Chamada à API do Google Maps
        response = requests.get(GOOGLE_MAPS_API_URL + '/directions/json', params=params)
        
        if response.status_code == 200:
            route_data = response.json()
            
            if route_data['status'] == 'OK':
                # Extrair pontos da rota
                route_points = []
                
                for step in route_data['routes'][0]['legs'][0]['steps']:
                    start_point = {
                        'latitude': step['start_location']['lat'],
                        'longitude': step['start_location']['lng'],
                        'order': len(route_points)
                    }
                    route_points.append(start_point)
                    
                    # Adicionar pontos intermediários se disponíveis
                    if 'path' in step:
                        for point in step['path']:
                            route_points.append({
                                'latitude': point['lat'],
                                'longitude': point['lng'],
                                'order': len(route_points)
                            })
                    
                    end_point = {
                        'latitude': step['end_location']['lat'],
                        'longitude': step['end_location']['lng'],
                        'order': len(route_points)
                    }
                    route_points.append(end_point)
                
                # Salvar pontos da rota no banco
                save_route_points(user_id, route_points)
                
                return route_points
            else:
                logger.error(f"Erro na resposta do Google Maps: {route_data['status']}")
                return None
        else:
            logger.error(f"Erro ao obter rota do Google Maps: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Exceção ao obter rota do Google Maps: {str(e)}")
        return None
```

### **3. Identificação de Postos na Rota**

Algoritmo para identificar postos próximos à rota:

```python
# Trecho do código backend/src/services/route_analyzer.py
def find_gas_stations_on_route(user_id, route_points, max_distance_km=2.0):
    """
    Encontra postos de combustível próximos à rota
    
    Args:
        user_id: ID do usuário
        route_points: Lista de pontos da rota
        max_distance_km: Distância máxima em km para considerar um posto como "na rota"
        
    Returns:
        Lista de postos próximos à rota com distância e desvio calculados
    """
    try:
        # Obter perfil do usuário para saber tipo de combustível
        user_profile = UserProfile.query.filter_by(user_id=user_id).first()
        if not user_profile:
            return []
            
        fuel_type = user_profile.preferred_fuel_type
        
        # Obter todos os postos com preço para o combustível desejado
        stations_query = db.session.query(GasStation, FuelPrice)\
            .join(FuelPrice, GasStation.id == FuelPrice.gas_station_id)\
            .filter(FuelPrice.fuel_type == fuel_type)\
            .all()
            
        stations_on_route = []
        
        # Para cada posto, calcular a distância mínima até a rota
        for station, price in stations_query:
            min_distance = float('inf')
            closest_point_index = -1
            
            # Calcular distância para cada ponto da rota
            for i, point in enumerate(route_points):
                distance = haversine_distance(
                    station.latitude, station.longitude,
                    point['latitude'], point['longitude']
                )
                
                if distance < min_distance:
                    min_distance = distance
                    closest_point_index = i
            
            # Se o posto está dentro da distância máxima, adicionar à lista
            if min_distance <= max_distance_km:
                # Calcular desvio necessário (ida e volta ao posto)
                detour_distance = min_distance * 2  # km
                
                # Calcular tempo extra necessário (assumindo velocidade média de 40 km/h em desvios)
                extra_time_minutes = (detour_distance / 40) * 60
                
                stations_on_route.append({
                    'station_id': station.id,
                    'name': station.name,
                    'brand': station.brand,
                    'latitude': station.latitude,
                    'longitude': station.longitude,
                    'fuel_type': fuel_type,
                    'price': price.price,
                    'distance_from_route': min_distance,
                    'detour_distance': detour_distance,
                    'extra_time_minutes': extra_time_minutes,
                    'route_point_index': closest_point_index
                })
        
        return stations_on_route
        
    except Exception as e:
        logger.error(f"Erro ao encontrar postos na rota: {str(e)}")
        return []
```

### **4. Cálculo de Economia e Recomendação**

Algoritmo para calcular a economia real e recomendar o melhor posto:

```python
# Trecho do código backend/src/services/recommendation_engine.py
def calculate_best_gas_station(user_id, stations_on_route, vehicle_consumption=10.0):
    """
    Calcula qual posto oferece a melhor economia considerando preço e desvio
    
    Args:
        user_id: ID do usuário
        stations_on_route: Lista de postos próximos à rota
        vehicle_consumption: Consumo do veículo em km/L (padrão: 10 km/L)
        
    Returns:
        Posto recomendado com cálculos de economia
    """
    try:
        if not stations_on_route:
            return None
            
        # Obter perfil do usuário
        user_profile = UserProfile.query.filter_by(user_id=user_id).first()
        if not user_profile:
            return None
            
        # Quantidade estimada de combustível para abastecer (padrão: tanque médio de 40L)
        fuel_amount = 40.0  # litros
        
        best_station = None
        max_savings = -float('inf')
        
        # Encontrar o posto mais caro como referência
        highest_price = max(station['price'] for station in stations_on_route)
        
        for station in stations_on_route:
            # Custo do combustível neste posto
            fuel_cost = station['price'] * fuel_amount
            
            # Custo do desvio (combustível gasto para ir até o posto)
            detour_fuel_used = station['detour_distance'] / vehicle_consumption
            detour_cost = detour_fuel_used * station['price']
            
            # Custo total (combustível + desvio)
            total_cost = fuel_cost + detour_cost
            
            # Economia em relação ao posto mais caro
            savings = (highest_price * fuel_amount) - total_cost
            
            # Calcular score ponderado (40% preço, 30% distância, 20% tempo, 10% confiabilidade)
            price_score = (highest_price - station['price']) / highest_price * 100
            distance_score = (2.0 - station['distance_from_route']) / 2.0 * 100
            time_score = (30 - min(station['extra_time_minutes'], 30)) / 30 * 100
            
            # Confiabilidade baseada em avaliações (se disponível)
            reliability_score = 80  # valor padrão
            
            # Score final ponderado
            weighted_score = (
                0.4 * price_score +
                0.3 * distance_score +
                0.2 * time_score +
                0.1 * reliability_score
            )
            
            station['savings'] = savings
            station['total_cost'] = total_cost
            station['score'] = weighted_score
            
            if weighted_score > max_savings:
                max_savings = weighted_score
                best_station = station
        
        return best_station
        
    except Exception as e:
        logger.error(f"Erro ao calcular melhor posto: {str(e)}")
        return None
```

### **5. Notificação em Tempo Real**

Sistema de notificações baseado no intervalo configurado:

```python
# Trecho do código backend/src/services/notification_service.py
def check_notification_trigger(user_id):
    """
    Verifica se deve enviar notificação baseado na distância percorrida
    
    Args:
        user_id: ID do usuário
        
    Returns:
        True se deve notificar, False caso contrário
    """
    try:
        # Obter perfil do usuário
        user_profile = UserProfile.query.filter_by(user_id=user_id).first()
        if not user_profile or not user_profile.notifications_enabled:
            return False
            
        # Obter última notificação enviada
        last_notification = Notification.query.filter_by(
            user_id=user_id,
            type='fuel_recommendation'
        ).order_by(Notification.created_at.desc()).first()
        
        # Obter distância total percorrida
        total_distance = calculate_total_distance(user_id)
        
        # Se não há notificação anterior, verificar se atingiu o primeiro intervalo
        if not last_notification:
            return total_distance >= user_profile.notification_interval_km
            
        # Calcular distância desde a última notificação
        distance_since_last = total_distance - last_notification.distance_km
        
        # Verificar se atingiu o intervalo configurado
        return distance_since_last >= user_profile.notification_interval_km
        
    except Exception as e:
        logger.error(f"Erro ao verificar gatilho de notificação: {str(e)}")
        return False
```

## 🔧 **Modelo de Dados**

### **Tabela `route_points`**

```sql
CREATE TABLE route_points (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    trip_id INTEGER NOT NULL REFERENCES trips(id),
    latitude DECIMAL(10, 7) NOT NULL,
    longitude DECIMAL(10, 7) NOT NULL,
    order_index INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_route_points_user_trip ON route_points(user_id, trip_id);
CREATE INDEX idx_route_points_coordinates ON route_points USING gist (
    ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
);
```

### **Tabela `gas_stations`**

```sql
CREATE TABLE gas_stations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    brand VARCHAR(100),
    latitude DECIMAL(10, 7) NOT NULL,
    longitude DECIMAL(10, 7) NOT NULL,
    address VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(50),
    postal_code VARCHAR(20),
    country VARCHAR(50) DEFAULT 'Brasil',
    phone VARCHAR(20),
    is_24h BOOLEAN DEFAULT FALSE,
    has_convenience_store BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_gas_stations_location ON gas_stations USING gist (
    ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
);
CREATE INDEX idx_gas_stations_brand ON gas_stations(brand);
```

## 📱 **Fluxo de Uso**

1. **Usuário inicia viagem:**
   - Ativa o GPS no app Tanque Cheio
   - Configura destino no Waze ou Google Maps
   - Inicia navegação

2. **Monitoramento contínuo:**
   - App Tanque Cheio monitora localização em segundo plano
   - Extrai rota atual do Waze/Google Maps
   - Calcula distância percorrida

3. **Notificação automática:**
   - Quando atinge o intervalo configurado (ex: 100km)
   - Sistema busca postos nos próximos X km da rota
   - Calcula melhor custo-benefício

4. **Recomendação inteligente:**
   - Envia notificação push com:
     - Nome do posto recomendado
     - Preço do combustível
     - Distância até o posto
     - Economia estimada
     - Cupom/voucher (se disponível)

5. **Navegação até o posto:**
   - Usuário pode clicar na notificação
   - App abre navegação direta até o posto
   - Registra uso do cupom (se aplicável)

## 🔄 **Atualização de Dados**

### **Preços de Combustíveis**

Os preços são atualizados por múltiplas fontes:

1. **Web Scraping:** Coleta automática de preços de sites especializados
2. **API da ANP:** Integração com dados oficiais da Agência Nacional do Petróleo
3. **Crowdsourcing:** Usuários podem reportar preços atualizados
4. **Parceiros:** Postos parceiros enviam atualizações automáticas

### **Postos de Combustível**

O banco de dados de postos é mantido atualizado por:

1. **Google Places API:** Dados oficiais de POIs
2. **OpenStreetMap:** Dados abertos de postos
3. **Cadastro manual:** Equipe de suporte adiciona novos postos
4. **Sugestões de usuários:** Usuários podem sugerir novos postos

## 🚀 **Próximos Passos**

1. **Integração com mais apps de navegação:**
   - Adicionar suporte para Apple Maps, Here, TomTom, etc.

2. **Previsão de preços com IA:**
   - Implementar algoritmos de machine learning para prever variações de preços

3. **Rotas personalizadas:**
   - Permitir que o usuário defina rotas favoritas para monitoramento contínuo

4. **Integração com sistemas de bordo:**
   - Conectar com sistemas de bordo de veículos para dados precisos de consumo

5. **Expansão internacional:**
   - Adaptar o sistema para outros países e moedas

