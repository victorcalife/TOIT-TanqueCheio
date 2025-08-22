# 🚀 ATUALIZAÇÕES DO SISTEMA TANQUE CHEIO

## 📋 **Visão Geral**

Este documento detalha as atualizações e melhorias a serem implementadas no sistema Tanque Cheio, com base no feedback do cliente e nas necessidades identificadas durante o desenvolvimento.

## 🚗 **Monitoramento por Distância Percorrida**

### **Implementação Atual:**
- Monitoramento baseado em intervalos de tempo regulares
- Verificações em segundo plano a cada 10-60 segundos
- Cálculo de distância acumulada

### **Nova Implementação:**
- Monitoramento baseado exclusivamente em distância percorrida
- Configuração personalizada por usuário (50km, 100km, 200km, etc.)
- Verificação precisa quando o usuário atinge exatamente os intervalos configurados
- Notificações disparadas apenas nos pontos de verificação definidos

```python
# backend/src/services/gps_tracking_service.py
def check_notification_trigger(user_id, current_location):
    """
    Verifica se deve enviar notificação baseado na distância percorrida
    
    Args:
        user_id: ID do usuário
        current_location: Localização atual (lat, lng)
        
    Returns:
        True se deve notificar, False caso contrário
    """
    try:
        # Obter perfil do usuário
        user_profile = UserProfile.query.filter_by(user_id=user_id).first()
        if not user_profile or not user_profile.notifications_enabled:
            return False
            
        # Obter viagem ativa
        active_trip = Trip.query.filter_by(
            user_id=user_id,
            status='active'
        ).first()
        
        if not active_trip:
            return False
            
        # Obter distância total percorrida na viagem atual
        total_distance = calculate_trip_distance(active_trip.id)
        
        # Obter última notificação enviada nesta viagem
        last_notification = Notification.query.filter_by(
            user_id=user_id,
            trip_id=active_trip.id,
            type='fuel_recommendation'
        ).order_by(Notification.created_at.desc()).first()
        
        # Intervalo configurado pelo usuário (em km)
        interval_km = user_profile.notification_interval_km
        
        # Se não há notificação anterior, verificar se atingiu o primeiro intervalo
        if not last_notification:
            should_notify = total_distance >= interval_km
            notification_distance = interval_km
        else:
            # Calcular próximo ponto de notificação
            last_notification_distance = last_notification.distance_km
            next_notification_point = math.ceil(last_notification_distance / interval_km) * interval_km
            
            # Se a distância atual ultrapassou o próximo ponto de notificação
            should_notify = total_distance >= next_notification_point
            notification_distance = next_notification_point
            
        if should_notify:
            # Calcular posição aproximada do ponto de notificação
            notification_position = estimate_position_at_distance(
                active_trip.id, 
                notification_distance
            )
            
            return {
                'should_notify': True,
                'distance': notification_distance,
                'position': notification_position
            }
        
        return {'should_notify': False}
        
    except Exception as e:
        logger.error(f"Erro ao verificar gatilho de notificação: {str(e)}")
        return {'should_notify': False}
```

## 🔄 **Fontes de Dados de Postos**

### **Implementação Atual:**
- Múltiplas fontes incluindo crowdsourcing
- Sem modelo de monetização claro para postos
- Foco em quantidade de dados

### **Nova Implementação:**
- **Remoção do crowdsourcing** para dados de postos
- **Sistema de cadastro para postos e redes**
- **APIs para atualização de preços**
- **Modelo de assinatura mensal** para manutenção do cadastro

```python
# backend/src/models/subscription.py
class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    partner_id = db.Column(db.Integer, db.ForeignKey('partners.id'), nullable=False)
    
    # Detalhes da assinatura
    plan_type = db.Column(db.String(20), nullable=False)  # 'basic', 'premium', 'enterprise'
    price_monthly = db.Column(db.Numeric(10, 2), nullable=False)
    max_stations = db.Column(db.Integer)  # Número máximo de postos permitidos
    api_calls_limit = db.Column(db.Integer)  # Limite de chamadas API por mês
    
    # Status e datas
    status = db.Column(db.String(20), default='active', nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    auto_renew = db.Column(db.Boolean, default=True)
    
    # Pagamento
    payment_method = db.Column(db.String(50))
    last_payment_date = db.Column(db.DateTime)
    next_payment_date = db.Column(db.DateTime)
    
    # Metadados
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    partner = db.relationship('Partner')
    payment_history = db.relationship('SubscriptionPayment', backref='subscription')
```

### **APIs para Parceiros:**

```python
# backend/src/routes/partner_api.py
@partner_api_bp.route('/prices/batch', methods=['POST'])
@partner_auth_required
def update_prices_batch():
    """Atualizar preços em lote (acesso apenas para parceiros)"""
    try:
        partner_id = g.partner_id
        data = request.get_json()
        
        if not 'prices' in data or not isinstance(data['prices'], list):
            return jsonify({
                'success': False,
                'message': "Formato inválido. Esperado array 'prices'"
            }), 400
            
        # Verificar limite de chamadas API
        subscription = Subscription.query.filter_by(
            partner_id=partner_id,
            status='active'
        ).first()
        
        if not subscription:
            return jsonify({
                'success': False,
                'message': "Assinatura inativa ou inexistente"
            }), 403
            
        # Verificar se parceiro tem permissão para estes postos
        gas_station_ids = [price['gas_station_id'] for price in data['prices']]
        authorized_stations = GasStation.query.filter(
            GasStation.id.in_(gas_station_ids),
            GasStation.partner_id == partner_id
        ).count()
        
        if authorized_stations != len(gas_station_ids):
            return jsonify({
                'success': False,
                'message': "Acesso negado a um ou mais postos"
            }), 403
            
        # Processar atualizações de preço
        results = []
        for price_data in data['prices']:
            try:
                # Validar dados
                if not all(k in price_data for k in ['gas_station_id', 'fuel_type', 'price']):
                    results.append({
                        'gas_station_id': price_data.get('gas_station_id'),
                        'success': False,
                        'message': "Dados incompletos"
                    })
                    continue
                    
                # Buscar preço existente
                fuel_price = FuelPrice.query.filter_by(
                    gas_station_id=price_data['gas_station_id'],
                    fuel_type=price_data['fuel_type']
                ).first()
                
                if fuel_price:
                    # Atualizar preço existente
                    old_price = float(fuel_price.price)
                    fuel_price.price = price_data['price']
                    fuel_price.updated_at = datetime.utcnow()
                    
                    # Registrar histórico
                    price_history = FuelPriceHistory(
                        gas_station_id=price_data['gas_station_id'],
                        fuel_type=price_data['fuel_type'],
                        old_price=old_price,
                        new_price=price_data['price'],
                        updated_by='partner_api',
                        partner_id=partner_id
                    )
                    db.session.add(price_history)
                    
                else:
                    # Criar novo preço
                    fuel_price = FuelPrice(
                        gas_station_id=price_data['gas_station_id'],
                        fuel_type=price_data['fuel_type'],
                        price=price_data['price'],
                        last_verified_at=datetime.utcnow(),
                        source='partner_api'
                    )
                    db.session.add(fuel_price)
                    
                results.append({
                    'gas_station_id': price_data['gas_station_id'],
                    'fuel_type': price_data['fuel_type'],
                    'success': True,
                    'price': float(price_data['price'])
                })
                    
            except Exception as e:
                results.append({
                    'gas_station_id': price_data.get('gas_station_id'),
                    'success': False,
                    'message': str(e)
                })
                
        # Registrar uso da API
        api_usage = PartnerAPIUsage(
            partner_id=partner_id,
            endpoint='/prices/batch',
            request_count=len(data['prices']),
            success_count=sum(1 for r in results if r.get('success', False))
        )
        db.session.add(api_usage)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f"Processados {len(results)} registros",
            'results': results
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao atualizar preços em lote: {str(e)}")
        return jsonify({
            'success': False,
            'message': "Erro ao processar atualizações de preço"
        }), 500
```

### **Fontes de Dados Implementadas:**

1. **ANP (Agência Nacional do Petróleo):**
   - Importação inicial de ~42.000 postos
   - Atualização semanal de preços médios
   - Dados públicos via API ou arquivos CSV

2. **Google Places API:**
   - Integração para busca de postos por proximidade
   - Dados de localização, horários, avaliações
   - Complemento para informações não disponíveis na ANP

3. **OpenStreetMap:**
   - Dados de localização precisos
   - Informações sobre serviços disponíveis
   - Coordenadas e metadados

4. **API para Parceiros:**
   - Interface para postos e redes atualizarem preços
   - Sistema de autenticação e validação
   - Webhooks para notificações em tempo real

## 🗺️ **Integração com Navegação**

### **Implementação Atual:**
- Recomendação de postos sem integração direta com navegação
- Usuário precisa sair do app para navegar até o posto

### **Nova Implementação:**
- **Exibição das 3 melhores opções** de preços
- **Integração direta com apps de navegação**
- **Adição automática de pontos de parada na rota atual**

```javascript
// frontend/src/services/NavigationService.js
export const addWaypointToNavigation = async (appName, latitude, longitude, name) => {
  try {
    // Verificar qual app de navegação usar
    const app = appName || await detectNavigationApp();
    
    switch (app) {
      case 'waze':
        return addWaypointToWaze(latitude, longitude, name);
        
      case 'google_maps':
        return addWaypointToGoogleMaps(latitude, longitude, name);
        
      default:
        // Fallback para abrir mapa genérico
        return openGenericMap(latitude, longitude, name);
    }
  } catch (error) {
    console.error('Erro ao adicionar ponto de parada:', error);
    throw error;
  }
};

const addWaypointToWaze = async (latitude, longitude, name) => {
  try {
    // Formatar URL para Waze
    const encodedName = encodeURIComponent(name);
    const wazeUrl = `waze://?ll=${latitude},${longitude}&navigate=yes&name=${encodedName}`;
    
    // Verificar se Waze está instalado
    const canOpen = await Linking.canOpenURL(wazeUrl);
    
    if (canOpen) {
      await Linking.openURL(wazeUrl);
      return true;
    } else {
      // Fallback para versão web
      const webUrl = `https://www.waze.com/ul?ll=${latitude},${longitude}&navigate=yes&zoom=17&name=${encodedName}`;
      await Linking.openURL(webUrl);
      return true;
    }
  } catch (error) {
    console.error('Erro ao abrir Waze:', error);
    return false;
  }
};

const addWaypointToGoogleMaps = async (latitude, longitude, name) => {
  try {
    // Formatar URL para Google Maps
    const encodedName = encodeURIComponent(name);
    const mapsUrl = `google.navigation:q=${latitude},${longitude}&title=${encodedName}`;
    
    // Verificar se Google Maps está instalado
    const canOpen = await Linking.canOpenURL(mapsUrl);
    
    if (canOpen) {
      await Linking.openURL(mapsUrl);
      return true;
    } else {
      // Fallback para versão web
      const webUrl = `https://www.google.com/maps/dir/?api=1&destination=${latitude},${longitude}&travelmode=driving&dir_action=navigate`;
      await Linking.openURL(webUrl);
      return true;
    }
  } catch (error) {
    console.error('Erro ao abrir Google Maps:', error);
    return false;
  }
};
```

## 🏆 **Badges e Informações Adicionais**

### **Implementação Atual:**
- Informações básicas sobre postos (nome, preço, distância)
- Sem detalhes sobre serviços disponíveis
- Sistema de avaliação limitado

### **Nova Implementação:**
- **Sistema completo de badges para serviços**
- **Informações detalhadas nas notificações**
- **Sistema de avaliação abrangente**

```sql
-- database/migrations/010_add_gas_station_services.sql
CREATE TABLE gas_station_services (
    id SERIAL PRIMARY KEY,
    gas_station_id INTEGER NOT NULL REFERENCES gas_stations(id),
    
    -- Serviços básicos
    has_convenience_store BOOLEAN DEFAULT FALSE,
    has_restaurant BOOLEAN DEFAULT FALSE,
    has_restrooms BOOLEAN DEFAULT FALSE,
    has_showers BOOLEAN DEFAULT FALSE,
    has_repair_shop BOOLEAN DEFAULT FALSE,
    has_tire_service BOOLEAN DEFAULT FALSE,
    has_truck_parking BOOLEAN DEFAULT FALSE,
    has_overnight_stay BOOLEAN DEFAULT FALSE,
    has_wifi BOOLEAN DEFAULT FALSE,
    has_atm BOOLEAN DEFAULT FALSE,
    has_car_wash BOOLEAN DEFAULT FALSE,
    
    -- Tipos de combustível
    has_gasoline BOOLEAN DEFAULT FALSE,
    has_ethanol BOOLEAN DEFAULT FALSE,
    has_diesel BOOLEAN DEFAULT FALSE,
    has_diesel_s10 BOOLEAN DEFAULT FALSE,
    has_gnv BOOLEAN DEFAULT FALSE,
    has_electric_charger BOOLEAN DEFAULT FALSE,
    
    -- Métodos de pagamento
    accepts_credit_card BOOLEAN DEFAULT FALSE,
    accepts_debit_card BOOLEAN DEFAULT FALSE,
    accepts_cash BOOLEAN DEFAULT FALSE,
    accepts_apps BOOLEAN DEFAULT FALSE,
    accepts_fleet_card BOOLEAN DEFAULT FALSE,
    
    -- Metadados
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_gas_station_services_station ON gas_station_services(gas_station_id);
```

```sql
-- database/migrations/011_add_rating_system.sql
CREATE TABLE gas_station_ratings (
    id SERIAL PRIMARY KEY,
    gas_station_id INTEGER NOT NULL REFERENCES gas_stations(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    
    -- Avaliações (1-5 estrelas)
    price_accuracy BOOLEAN, -- TRUE se preço estava correto, FALSE se não
    reported_price DECIMAL(10, 2), -- Preço reportado pelo usuário se diferente
    service_rating INTEGER CHECK (service_rating BETWEEN 1 AND 5),
    cleanliness_rating INTEGER CHECK (cleanliness_rating BETWEEN 1 AND 5),
    infrastructure_rating INTEGER CHECK (infrastructure_rating BETWEEN 1 AND 5),
    
    -- Feedback geral
    general_rating INTEGER CHECK (general_rating BETWEEN 1 AND 5),
    comment TEXT,
    
    -- Metadados
    visit_date TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_gas_station_ratings_station ON gas_station_ratings(gas_station_id);
CREATE INDEX idx_gas_station_ratings_user ON gas_station_ratings(user_id);
```

### **Componente de Exibição de Badges:**

```jsx
// frontend/src/components/ServiceBadges.jsx
const ServiceBadges = ({ services }) => {
  // Mapear serviços para ícones e descrições
  const serviceBadges = [
    { key: 'has_convenience_store', icon: <StoreIcon />, label: 'Conveniência' },
    { key: 'has_restaurant', icon: <RestaurantIcon />, label: 'Restaurante' },
    { key: 'has_restrooms', icon: <BathroomIcon />, label: 'Banheiros' },
    { key: 'has_showers', icon: <ShowerIcon />, label: 'Chuveiros' },
    { key: 'has_repair_shop', icon: <RepairIcon />, label: 'Oficina' },
    { key: 'has_tire_service', icon: <TireIcon />, label: 'Borracharia' },
    { key: 'has_truck_parking', icon: <ParkingIcon />, label: 'Estacionamento' },
    { key: 'has_overnight_stay', icon: <BedIcon />, label: 'Pernoite' },
    { key: 'has_wifi', icon: <WifiIcon />, label: 'Wi-Fi' },
    { key: 'has_atm', icon: <AtmIcon />, label: 'Caixa Eletrônico' },
    { key: 'has_car_wash', icon: <CarWashIcon />, label: 'Lava-rápido' },
  ];
  
  // Filtrar apenas os serviços disponíveis
  const availableServices = serviceBadges.filter(badge => services[badge.key]);
  
  return (
    <div className="service-badges">
      <h4 className="text-sm font-medium mb-2">Serviços Disponíveis</h4>
      <div className="flex flex-wrap gap-2">
        {availableServices.map(service => (
          <Tooltip key={service.key} content={service.label}>
            <Badge variant="outline" className="service-badge">
              {service.icon}
              <span className="ml-1">{service.label}</span>
            </Badge>
          </Tooltip>
        ))}
        
        {availableServices.length === 0 && (
          <span className="text-sm text-muted-foreground">
            Nenhum serviço adicional informado
          </span>
        )}
      </div>
    </div>
  );
};
```

### **Sistema de Avaliação:**

```jsx
// frontend/src/components/RatingForm.jsx
const RatingForm = ({ gasStationId, onSubmit }) => {
  const [priceAccurate, setPriceAccurate] = useState(true);
  const [reportedPrice, setReportedPrice] = useState('');
  const [serviceRating, setServiceRating] = useState(0);
  const [cleanlinessRating, setCleanlinessRating] = useState(0);
  const [infrastructureRating, setInfrastructureRating] = useState(0);
  const [generalRating, setGeneralRating] = useState(0);
  const [comment, setComment] = useState('');
  
  const handleSubmit = (e) => {
    e.preventDefault();
    
    onSubmit({
      gas_station_id: gasStationId,
      price_accuracy: priceAccurate,
      reported_price: priceAccurate ? null : parseFloat(reportedPrice),
      service_rating: serviceRating,
      cleanliness_rating: cleanlinessRating,
      infrastructure_rating: infrastructureRating,
      general_rating: generalRating,
      comment,
      visit_date: new Date().toISOString()
    });
  };
  
  return (
    <form onSubmit={handleSubmit} className="rating-form">
      <h3 className="text-lg font-bold mb-4">Avalie sua experiência</h3>
      
      {/* Verificação de preço */}
      <div className="mb-4">
        <p className="mb-2">O preço estava correto?</p>
        <div className="flex gap-4">
          <Button
            type="button"
            variant={priceAccurate ? "default" : "outline"}
            onClick={() => setPriceAccurate(true)}
          >
            <CheckIcon className="mr-2" size={16} />
            Sim, estava correto
          </Button>
          <Button
            type="button"
            variant={!priceAccurate ? "default" : "outline"}
            onClick={() => setPriceAccurate(false)}
          >
            <XIcon className="mr-2" size={16} />
            Não, estava diferente
          </Button>
        </div>
        
        {!priceAccurate && (
          <div className="mt-2">
            <Label htmlFor="reported-price">Qual era o preço real?</Label>
            <Input
              id="reported-price"
              type="number"
              step="0.01"
              placeholder="0.00"
              value={reportedPrice}
              onChange={(e) => setReportedPrice(e.target.value)}
              className="w-32"
            />
          </div>
        )}
      </div>
      
      {/* Avaliações por estrelas */}
      <div className="grid gap-4 mb-4">
        <div>
          <Label>Atendimento</Label>
          <StarRating value={serviceRating} onChange={setServiceRating} />
        </div>
        
        <div>
          <Label>Limpeza</Label>
          <StarRating value={cleanlinessRating} onChange={setCleanlinessRating} />
        </div>
        
        <div>
          <Label>Infraestrutura</Label>
          <StarRating value={infrastructureRating} onChange={setInfrastructureRating} />
        </div>
        
        <div>
          <Label>Avaliação Geral</Label>
          <StarRating value={generalRating} onChange={setGeneralRating} />
        </div>
      </div>
      
      {/* Comentário */}
      <div className="mb-4">
        <Label htmlFor="comment">Comentário (opcional)</Label>
        <Textarea
          id="comment"
          placeholder="Compartilhe sua experiência..."
          value={comment}
          onChange={(e) => setComment(e.target.value)}
        />
      </div>
      
      <Button type="submit" className="w-full">
        Enviar Avaliação
      </Button>
    </form>
  );
};
```

## 📱 **Notificações Aprimoradas**

### **Implementação Atual:**
- Notificações básicas com informações limitadas
- Sem opções de ação direta

### **Nova Implementação:**
- **Notificações ricas com detalhes completos**
- **Botões de ação direta (navegar, ver detalhes)**
- **Exibição de badges e serviços disponíveis**

```javascript
// frontend/src/services/NotificationService.js
export const createFuelRecommendationNotification = (recommendation) => {
  const {
    id,
    name,
    brand,
    distance_from_route,
    fuel_type,
    original_price,
    discounted_price,
    has_coupon,
    coupon_code,
    latitude,
    longitude,
    services
  } = recommendation;
  
  // Formatar preços
  const formattedOriginalPrice = `R$ ${original_price.toFixed(2)}`;
  const formattedDiscountedPrice = has_coupon ? `R$ ${discounted_price.toFixed(2)}` : null;
  
  // Calcular porcentagem de desconto
  const discountPercentage = has_coupon 
    ? ((original_price - discounted_price) / original_price * 100).toFixed(0)
    : null;
    
  // Determinar serviços principais para exibir (máximo 3)
  const mainServices = [];
  if (services) {
    if (services.has_restaurant) mainServices.push('Restaurante');
    if (services.has_convenience_store) mainServices.push('Conveniência');
    if (services.has_restrooms) mainServices.push('Banheiros');
    if (services.has_showers && mainServices.length < 3) mainServices.push('Chuveiros');
    if (services.has_tire_service && mainServices.length < 3) mainServices.push('Borracharia');
    if (services.has_overnight_stay && mainServices.length < 3) mainServices.push('Pernoite');
  }
  
  // Criar título da notificação
  let title = `${name} - ${getFuelTypeName(fuel_type)}`;
  if (has_coupon) {
    title = `${discountPercentage}% OFF! ${title}`;
  }
  
  // Criar corpo da notificação
  let body = `${formattedOriginalPrice}`;
  if (has_coupon) {
    body = `De ${formattedOriginalPrice} por ${formattedDiscountedPrice}`;
  }
  
  // Adicionar serviços se disponíveis
  if (mainServices.length > 0) {
    body += ` • ${mainServices.join(' • ')}`;
  }
  
  // Adicionar distância
  body += ` • ${distance_from_route.toFixed(1)}km`;
  
  // Criar ações
  const actions = [
    {
      id: 'navigate',
      title: 'Ir para lá',
      icon: 'navigation',
      callback: () => navigateToGasStation(latitude, longitude, name)
    },
    {
      id: 'details',
      title: 'Ver detalhes',
      icon: 'info',
      callback: () => showGasStationDetails(id)
    }
  ];
  
  // Adicionar ação de cupom se disponível
  if (has_coupon) {
    actions.push({
      id: 'coupon',
      title: 'Ver cupom',
      icon: 'ticket',
      callback: () => showCouponDetails(coupon_code)
    });
  }
  
  return {
    id: `fuel-recommendation-${id}`,
    channelId: 'fuel-recommendations',
    title,
    body,
    data: { recommendation_id: id },
    actions,
    category: 'recommendation',
    priority: 'high',
    vibrate: true,
    lights: true,
    ongoing: false,
    autoCancel: true
  };
};
```

## 🚀 **Próximos Passos**

1. **Implementar sistema de cadastro para postos e redes**
   - Portal de parceiros
   - Processo de verificação
   - Planos de assinatura

2. **Desenvolver APIs para atualização de preços**
   - Documentação para parceiros
   - Sistema de autenticação
   - Limites de uso por plano

3. **Integrar com APIs de navegação**
   - Waze Deep Links
   - Google Maps API
   - Adição de pontos de parada

4. **Implementar sistema de badges e avaliações**
   - Interface para usuários avaliarem postos
   - Exibição de badges em recomendações
   - Filtros por serviços disponíveis

5. **Aprimorar notificações**
   - Notificações ricas com mais detalhes
   - Ações diretas nas notificações
   - Personalização por usuário

