# 🎟️ SISTEMA DE CUPONS E VOUCHERS - TANQUE CHEIO

## 📋 **Visão Geral**

O sistema de cupons e vouchers é uma funcionalidade central do Tanque Cheio, permitindo que redes parceiras ofereçam descontos aos usuários. Estes descontos são considerados no algoritmo de recomendação, influenciando diretamente qual posto será sugerido ao motorista.

## 🔧 **Arquitetura do Sistema de Cupons**

### **1. Modelo de Dados**

#### **1.1 Tabela `coupons`**

```sql
CREATE TABLE coupons (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    partner_id INTEGER REFERENCES partners(id),
    gas_station_id INTEGER REFERENCES gas_stations(id),
    
    -- Tipo de desconto
    discount_type VARCHAR(20) NOT NULL CHECK (discount_type IN ('percentage', 'fixed_amount')),
    discount_value DECIMAL(10, 2) NOT NULL,
    
    -- Restrições
    fuel_type VARCHAR(20) CHECK (fuel_type IN ('gasoline', 'ethanol', 'diesel', 'diesel_s10', 'gnv')),
    min_liters DECIMAL(10, 2),
    valid_from TIMESTAMP NOT NULL,
    valid_until TIMESTAMP NOT NULL,
    max_uses INTEGER,
    current_uses INTEGER DEFAULT 0,
    
    -- Metadados
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_coupons_code ON coupons(code);
CREATE INDEX idx_coupons_partner ON coupons(partner_id);
CREATE INDEX idx_coupons_gas_station ON coupons(gas_station_id);
CREATE INDEX idx_coupons_validity ON coupons(valid_from, valid_until);
```

#### **1.2 Tabela `coupon_usage`**

```sql
CREATE TABLE coupon_usage (
    id SERIAL PRIMARY KEY,
    coupon_id INTEGER NOT NULL REFERENCES coupons(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    gas_station_id INTEGER NOT NULL REFERENCES gas_stations(id),
    
    -- Detalhes do uso
    used_at TIMESTAMP NOT NULL DEFAULT NOW(),
    fuel_type VARCHAR(20) NOT NULL,
    liters DECIMAL(10, 2) NOT NULL,
    original_price DECIMAL(10, 2) NOT NULL,
    discounted_price DECIMAL(10, 2) NOT NULL,
    total_discount DECIMAL(10, 2) NOT NULL,
    
    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'used' CHECK (status IN ('used', 'cancelled', 'refunded')),
    
    -- Metadados
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_coupon_usage_coupon ON coupon_usage(coupon_id);
CREATE INDEX idx_coupon_usage_user ON coupon_usage(user_id);
CREATE INDEX idx_coupon_usage_gas_station ON coupon_usage(gas_station_id);
CREATE INDEX idx_coupon_usage_date ON coupon_usage(used_at);
```

#### **1.3 Tabela `partners`**

```sql
CREATE TABLE partners (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    logo_url VARCHAR(255),
    api_key VARCHAR(64) UNIQUE,
    webhook_url VARCHAR(255),
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'pending')),
    commission_rate DECIMAL(5, 2) NOT NULL DEFAULT 5.00,
    
    -- Configurações de integração
    integration_type VARCHAR(20) CHECK (integration_type IN ('api', 'manual', 'webhook')),
    integration_settings JSONB,
    
    -- Metadados
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_partners_status ON partners(status);
```

### **2. Implementação Backend**

#### **2.1 Modelos**

```python
# backend/src/models/coupon.py
class Coupon(db.Model):
    __tablename__ = 'coupons'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    partner_id = db.Column(db.Integer, db.ForeignKey('partners.id'))
    gas_station_id = db.Column(db.Integer, db.ForeignKey('gas_stations.id'))
    
    # Tipo de desconto
    discount_type = db.Column(db.String(20), nullable=False)  # 'percentage', 'fixed_amount'
    discount_value = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Restrições
    fuel_type = db.Column(db.String(20))  # Tipo específico ou NULL para todos
    min_liters = db.Column(db.Numeric(10, 2))  # Litros mínimos ou NULL
    valid_from = db.Column(db.DateTime, nullable=False)
    valid_until = db.Column(db.DateTime, nullable=False)
    max_uses = db.Column(db.Integer)
    current_uses = db.Column(db.Integer, default=0)
    
    # Metadados
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    partner = db.relationship('Partner')
    gas_station = db.relationship('GasStation')
    usage_history = db.relationship('CouponUsage', backref='coupon')
    
    def is_valid(self):
        """Verifica se o cupom está válido"""
        now = datetime.utcnow()
        
        # Verificar período de validade
        if now < self.valid_from or now > self.valid_until:
            return False
            
        # Verificar limite de usos
        if self.max_uses and self.current_uses >= self.max_uses:
            return False
            
        return True
        
    def calculate_discount(self, base_price, liters=None):
        """Calcula o desconto aplicado pelo cupom"""
        # Verificar quantidade mínima de litros
        if self.min_liters and (not liters or liters < self.min_liters):
            return 0.0
            
        # Calcular desconto
        if self.discount_type == 'percentage':
            return base_price * (self.discount_value / 100)
        else:  # fixed_amount
            return self.discount_value
            
    def apply_discount(self, base_price, liters=None):
        """Aplica o desconto e retorna o preço final"""
        discount = self.calculate_discount(base_price, liters)
        return base_price - discount
```

```python
# backend/src/models/coupon_usage.py
class CouponUsage(db.Model):
    __tablename__ = 'coupon_usage'
    
    id = db.Column(db.Integer, primary_key=True)
    coupon_id = db.Column(db.Integer, db.ForeignKey('coupons.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    gas_station_id = db.Column(db.Integer, db.ForeignKey('gas_stations.id'), nullable=False)
    
    # Detalhes do uso
    used_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    fuel_type = db.Column(db.String(20), nullable=False)
    liters = db.Column(db.Numeric(10, 2), nullable=False)
    original_price = db.Column(db.Numeric(10, 2), nullable=False)
    discounted_price = db.Column(db.Numeric(10, 2), nullable=False)
    total_discount = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Status
    status = db.Column(db.String(20), default='used', nullable=False)
    
    # Metadados
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    user = db.relationship('User')
    gas_station = db.relationship('GasStation')
```

#### **2.2 Serviço de Cupons**

```python
# backend/src/services/coupon_service.py
class CouponService:
    @staticmethod
    def get_available_coupons(user_id, gas_station_id=None, fuel_type=None):
        """
        Obtém cupons disponíveis para um usuário, posto e tipo de combustível
        
        Args:
            user_id: ID do usuário
            gas_station_id: ID do posto (opcional)
            fuel_type: Tipo de combustível (opcional)
            
        Returns:
            Lista de cupons válidos
        """
        try:
            now = datetime.utcnow()
            
            # Consulta base
            query = Coupon.query.filter(
                Coupon.valid_from <= now,
                Coupon.valid_until >= now
            )
            
            # Filtrar por posto se especificado
            if gas_station_id:
                query = query.filter(
                    db.or_(
                        Coupon.gas_station_id == gas_station_id,
                        Coupon.gas_station_id == None
                    )
                )
                
            # Filtrar por tipo de combustível se especificado
            if fuel_type:
                query = query.filter(
                    db.or_(
                        Coupon.fuel_type == fuel_type,
                        Coupon.fuel_type == None
                    )
                )
                
            # Filtrar por limite de usos
            query = query.filter(
                db.or_(
                    Coupon.max_uses == None,
                    Coupon.current_uses < Coupon.max_uses
                )
            )
            
            # Verificar se o usuário já usou cupons específicos
            # (para cupons de uso único por usuário)
            used_coupon_ids = db.session.query(CouponUsage.coupon_id)\
                .filter(CouponUsage.user_id == user_id)\
                .filter(CouponUsage.status == 'used')\
                .join(Coupon)\
                .filter(Coupon.max_uses_per_user == 1)\
                .all()
                
            if used_coupon_ids:
                used_ids = [id[0] for id in used_coupon_ids]
                query = query.filter(~Coupon.id.in_(used_ids))
                
            return query.all()
            
        except Exception as e:
            logger.error(f"Erro ao obter cupons disponíveis: {str(e)}")
            return []
            
    @staticmethod
    def apply_coupon(coupon_code, user_id, gas_station_id, fuel_type, liters, original_price):
        """
        Aplica um cupom e registra seu uso
        
        Args:
            coupon_code: Código do cupom
            user_id: ID do usuário
            gas_station_id: ID do posto
            fuel_type: Tipo de combustível
            liters: Quantidade de litros
            original_price: Preço original por litro
            
        Returns:
            Tuple (success, discounted_price, message)
        """
        try:
            # Buscar cupom pelo código
            coupon = Coupon.query.filter_by(code=coupon_code).first()
            
            if not coupon:
                return False, original_price, "Cupom não encontrado"
                
            # Verificar validade
            if not coupon.is_valid():
                return False, original_price, "Cupom expirado ou limite de usos atingido"
                
            # Verificar restrições de posto
            if coupon.gas_station_id and coupon.gas_station_id != gas_station_id:
                return False, original_price, "Cupom não válido para este posto"
                
            # Verificar restrições de combustível
            if coupon.fuel_type and coupon.fuel_type != fuel_type:
                return False, original_price, "Cupom não válido para este combustível"
                
            # Verificar quantidade mínima
            if coupon.min_liters and liters < coupon.min_liters:
                return False, original_price, f"Quantidade mínima: {coupon.min_liters}L"
                
            # Calcular preço com desconto
            discounted_price = coupon.apply_discount(original_price)
            total_discount = (original_price - discounted_price) * liters
            
            # Registrar uso do cupom
            usage = CouponUsage(
                coupon_id=coupon.id,
                user_id=user_id,
                gas_station_id=gas_station_id,
                fuel_type=fuel_type,
                liters=liters,
                original_price=original_price,
                discounted_price=discounted_price,
                total_discount=total_discount
            )
            
            # Incrementar contador de usos
            coupon.current_uses += 1
            
            # Salvar no banco
            db.session.add(usage)
            db.session.commit()
            
            # Notificar parceiro via webhook (se configurado)
            if coupon.partner and coupon.partner.webhook_url:
                notify_partner_webhook.delay(
                    partner_id=coupon.partner_id,
                    coupon_code=coupon.code,
                    usage_id=usage.id
                )
            
            return True, discounted_price, "Cupom aplicado com sucesso"
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao aplicar cupom: {str(e)}")
            return False, original_price, "Erro ao processar cupom"
```

### **3. Integração com o Sistema de Recomendação**

```python
# backend/src/services/recommendation_engine.py
def calculate_best_gas_station(user_id, stations_on_route, vehicle_consumption=10.0):
    """
    Calcula qual posto oferece a melhor economia considerando preço, desvio e cupons
    
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
        max_score = -float('inf')
        
        # Encontrar o posto mais caro como referência
        highest_price = max(station['price'] for station in stations_on_route)
        
        for station in stations_on_route:
            # Preço base
            base_price = station['price']
            final_price = base_price
            applied_coupon = None
            
            # Verificar cupons disponíveis para este posto/combustível
            available_coupons = CouponService.get_available_coupons(
                user_id, 
                station['station_id'],
                station['fuel_type']
            )
            
            # Aplicar melhor cupom disponível
            if available_coupons:
                best_discount = 0
                for coupon in available_coupons:
                    discount = coupon.calculate_discount(base_price, fuel_amount)
                    
                    if discount > best_discount:
                        best_discount = discount
                        applied_coupon = coupon
                
                # Aplicar desconto ao preço
                if applied_coupon:
                    final_price = applied_coupon.apply_discount(base_price, fuel_amount)
            
            # Custo do combustível neste posto
            fuel_cost = final_price * fuel_amount
            
            # Custo do desvio (combustível gasto para ir até o posto)
            detour_fuel_used = station['detour_distance'] / vehicle_consumption
            detour_cost = detour_fuel_used * final_price
            
            # Custo total (combustível + desvio)
            total_cost = fuel_cost + detour_cost
            
            # Economia em relação ao posto mais caro
            savings = (highest_price * fuel_amount) - total_cost
            
            # Calcular score ponderado (40% preço, 30% distância, 20% tempo, 10% confiabilidade)
            price_score = (highest_price - final_price) / highest_price * 100
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
            
            # Adicionar bônus para postos com cupom (incentivo para parceiros)
            if applied_coupon:
                weighted_score *= 1.1  # 10% de bônus para postos com cupom
            
            station['savings'] = savings
            station['total_cost'] = total_cost
            station['score'] = weighted_score
            
            # Adicionar informações do cupom ao resultado
            if applied_coupon:
                station['has_coupon'] = True
                station['coupon_code'] = applied_coupon.code
                station['coupon_description'] = get_coupon_description(applied_coupon)
                station['original_price'] = base_price
                station['discounted_price'] = final_price
                station['discount_value'] = base_price - final_price
                station['discount_percentage'] = ((base_price - final_price) / base_price) * 100
            else:
                station['has_coupon'] = False
            
            if weighted_score > max_score:
                max_score = weighted_score
                best_station = station
        
        return best_station
        
    except Exception as e:
        logger.error(f"Erro ao calcular melhor posto: {str(e)}")
        return None
```

### **4. APIs de Cupons**

```python
# backend/src/routes/coupons.py
@coupons_bp.route('/available', methods=['GET'])
@jwt_required()
def get_available_coupons():
    """Obter cupons disponíveis para o usuário"""
    try:
        user_id = get_jwt_identity()
        
        # Parâmetros opcionais
        gas_station_id = request.args.get('gas_station_id', type=int)
        fuel_type = request.args.get('fuel_type')
        
        # Obter cupons disponíveis
        coupons = CouponService.get_available_coupons(
            user_id, gas_station_id, fuel_type
        )
        
        # Formatar resposta
        result = []
        for coupon in coupons:
            partner_name = coupon.partner.name if coupon.partner else None
            gas_station_name = coupon.gas_station.name if coupon.gas_station else "Qualquer posto"
            
            result.append({
                'id': coupon.id,
                'code': coupon.code,
                'partner': partner_name,
                'gas_station': gas_station_name,
                'discount_type': coupon.discount_type,
                'discount_value': float(coupon.discount_value),
                'fuel_type': coupon.fuel_type or "Qualquer combustível",
                'min_liters': float(coupon.min_liters) if coupon.min_liters else None,
                'valid_until': coupon.valid_until.isoformat(),
                'description': get_coupon_description(coupon)
            })
        
        return jsonify({
            'success': True,
            'coupons': result
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter cupons disponíveis: {str(e)}")
        return jsonify({
            'success': False,
            'message': "Erro ao obter cupons disponíveis"
        }), 500

@coupons_bp.route('/apply', methods=['POST'])
@jwt_required()
def apply_coupon():
    """Aplicar um cupom"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validar dados
        if not all(k in data for k in ['coupon_code', 'gas_station_id', 'fuel_type', 'liters']):
            return jsonify({
                'success': False,
                'message': "Dados incompletos"
            }), 400
            
        # Obter preço original
        gas_station_id = data['gas_station_id']
        fuel_type = data['fuel_type']
        
        fuel_price = FuelPrice.query.filter_by(
            gas_station_id=gas_station_id,
            fuel_type=fuel_type
        ).first()
        
        if not fuel_price:
            return jsonify({
                'success': False,
                'message': "Preço não encontrado para este posto/combustível"
            }), 404
            
        original_price = float(fuel_price.price)
        
        # Aplicar cupom
        success, discounted_price, message = CouponService.apply_coupon(
            data['coupon_code'],
            user_id,
            gas_station_id,
            fuel_type,
            float(data['liters']),
            original_price
        )
        
        return jsonify({
            'success': success,
            'message': message,
            'original_price': original_price,
            'discounted_price': float(discounted_price),
            'discount': original_price - float(discounted_price),
            'discount_percentage': ((original_price - float(discounted_price)) / original_price) * 100
        }), 200 if success else 400
        
    except Exception as e:
        logger.error(f"Erro ao aplicar cupom: {str(e)}")
        return jsonify({
            'success': False,
            'message': "Erro ao processar cupom"
        }), 500
```

### **5. Integração com Parceiros**

#### **5.1 Webhook para Parceiros**

```python
# backend/src/services/partner_service.py
def notify_partner_webhook(partner_id, coupon_code, usage_id):
    """
    Notifica parceiro sobre uso de cupom via webhook
    
    Args:
        partner_id: ID do parceiro
        coupon_code: Código do cupom usado
        usage_id: ID do registro de uso
    """
    try:
        # Obter parceiro
        partner = Partner.query.get(partner_id)
        if not partner or not partner.webhook_url:
            logger.warning(f"Parceiro {partner_id} não tem webhook configurado")
            return False
            
        # Obter detalhes do uso
        usage = CouponUsage.query.get(usage_id)
        if not usage:
            logger.error(f"Uso de cupom {usage_id} não encontrado")
            return False
            
        # Preparar payload
        payload = {
            'event': 'coupon_used',
            'timestamp': datetime.utcnow().isoformat(),
            'coupon': {
                'code': coupon_code,
                'id': usage.coupon_id
            },
            'usage': {
                'id': usage.id,
                'gas_station_id': usage.gas_station_id,
                'gas_station_name': usage.gas_station.name,
                'fuel_type': usage.fuel_type,
                'liters': float(usage.liters),
                'original_price': float(usage.original_price),
                'discounted_price': float(usage.discounted_price),
                'total_discount': float(usage.total_discount),
                'used_at': usage.used_at.isoformat()
            }
        }
        
        # Assinar payload com chave secreta
        signature = hmac.new(
            partner.api_key.encode(),
            json.dumps(payload).encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Enviar webhook
        response = requests.post(
            partner.webhook_url,
            json=payload,
            headers={
                'Content-Type': 'application/json',
                'X-Tanque-Cheio-Signature': signature
            },
            timeout=5
        )
        
        if response.status_code >= 200 and response.status_code < 300:
            logger.info(f"Webhook enviado com sucesso para parceiro {partner_id}")
            return True
        else:
            logger.warning(f"Falha ao enviar webhook para parceiro {partner_id}: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"Erro ao notificar parceiro {partner_id}: {str(e)}")
        return False
```

#### **5.2 API para Parceiros**

```python
# backend/src/routes/partner_api.py
@partner_api_bp.route('/coupons', methods=['POST'])
@partner_auth_required
def create_coupon():
    """Criar novo cupom (acesso apenas para parceiros)"""
    try:
        partner_id = g.partner_id
        data = request.get_json()
        
        # Validar dados
        required_fields = ['code', 'discount_type', 'discount_value', 'valid_from', 'valid_until']
        if not all(k in data for k in required_fields):
            return jsonify({
                'success': False,
                'message': "Dados incompletos"
            }), 400
            
        # Criar cupom
        coupon = Coupon(
            code=data['code'],
            partner_id=partner_id,
            gas_station_id=data.get('gas_station_id'),
            discount_type=data['discount_type'],
            discount_value=data['discount_value'],
            fuel_type=data.get('fuel_type'),
            min_liters=data.get('min_liters'),
            valid_from=datetime.fromisoformat(data['valid_from']),
            valid_until=datetime.fromisoformat(data['valid_until']),
            max_uses=data.get('max_uses')
        )
        
        db.session.add(coupon)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': "Cupom criado com sucesso",
            'coupon_id': coupon.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar cupom: {str(e)}")
        return jsonify({
            'success': False,
            'message': "Erro ao criar cupom"
        }), 500

@partner_api_bp.route('/coupons/<code>', methods=['DELETE'])
@partner_auth_required
def deactivate_coupon(code):
    """Desativar cupom (acesso apenas para parceiros)"""
    try:
        partner_id = g.partner_id
        
        # Buscar cupom
        coupon = Coupon.query.filter_by(code=code, partner_id=partner_id).first()
        
        if not coupon:
            return jsonify({
                'success': False,
                'message': "Cupom não encontrado"
            }), 404
            
        # Desativar cupom (definir data de validade para o passado)
        coupon.valid_until = datetime.utcnow() - timedelta(seconds=1)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': "Cupom desativado com sucesso"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao desativar cupom: {str(e)}")
        return jsonify({
            'success': False,
            'message': "Erro ao desativar cupom"
        }), 500
```

## 📱 **Interface do Usuário**

### **1. Exibição de Cupons na Recomendação**

```jsx
// frontend/src/components/RecommendationCard.jsx
const RecommendationCard = ({ recommendation }) => {
  const {
    name,
    brand,
    address,
    distance_from_route,
    detour_distance,
    extra_time_minutes,
    fuel_type,
    original_price,
    discounted_price,
    has_coupon,
    coupon_code,
    coupon_description,
    savings,
    score
  } = recommendation;

  // Formatar valores
  const formattedOriginalPrice = `R$ ${original_price.toFixed(2)}`;
  const formattedDiscountedPrice = has_coupon ? `R$ ${discounted_price.toFixed(2)}` : null;
  const formattedDistance = `${distance_from_route.toFixed(1)} km`;
  const formattedDetour = `+${detour_distance.toFixed(1)} km`;
  const formattedTime = `+${Math.round(extra_time_minutes)} min`;
  const formattedSavings = `R$ ${savings.toFixed(2)}`;
  
  // Calcular porcentagem de desconto
  const discountPercentage = has_coupon 
    ? ((original_price - discounted_price) / original_price * 100).toFixed(0)
    : null;

  return (
    <Card className="recommendation-card">
      <CardHeader>
        <div className="flex justify-between items-center">
          <div>
            <CardTitle>{name}</CardTitle>
            <CardDescription>{brand}</CardDescription>
          </div>
          <div className="score-badge">
            <span>{Math.round(score)}</span>
            <small>score</small>
          </div>
        </div>
      </CardHeader>
      
      <CardContent>
        <div className="address mb-3">
          <MapPinIcon className="inline mr-1" size={16} />
          <span>{address}</span>
        </div>
        
        <div className="grid grid-cols-3 gap-2 mb-4">
          <div className="text-center">
            <p className="text-sm text-muted-foreground">Distância</p>
            <p className="font-medium">{formattedDistance}</p>
          </div>
          <div className="text-center">
            <p className="text-sm text-muted-foreground">Desvio</p>
            <p className="font-medium">{formattedDetour}</p>
          </div>
          <div className="text-center">
            <p className="text-sm text-muted-foreground">Tempo extra</p>
            <p className="font-medium">{formattedTime}</p>
          </div>
        </div>
        
        <div className="price-section">
          <div className="flex justify-between items-center">
            <div>
              <p className="text-sm text-muted-foreground">{getFuelTypeName(fuel_type)}</p>
              <p className="price">
                {has_coupon ? (
                  <>
                    <span className="original-price line-through mr-2">
                      {formattedOriginalPrice}
                    </span>
                    <span className="discounted-price font-bold">
                      {formattedDiscountedPrice}
                    </span>
                  </>
                ) : (
                  <span className="font-bold">{formattedOriginalPrice}</span>
                )}
              </p>
            </div>
            
            <div className="savings">
              <p className="text-sm text-muted-foreground">Economia</p>
              <p className="font-medium text-green-600">{formattedSavings}</p>
            </div>
          </div>
        </div>
        
        {has_coupon && (
          <div className="coupon-badge mt-3">
            <TagIcon className="inline mr-1" size={16} />
            <span className="font-medium">{discountPercentage}% OFF</span>
            <span className="ml-1 text-sm">{coupon_description}</span>
          </div>
        )}
      </CardContent>
      
      <CardFooter className="flex justify-between">
        <Button variant="outline" onClick={() => openInMaps(name, latitude, longitude)}>
          <MapIcon className="mr-2" size={16} />
          Ver no mapa
        </Button>
        <Button onClick={() => navigateTo(latitude, longitude)}>
          <NavigationIcon className="mr-2" size={16} />
          Ir para lá
        </Button>
      </CardFooter>
    </Card>
  );
};
```

### **2. Tela de Cupons Disponíveis**

```jsx
// frontend/src/pages/CouponsPage.jsx
const CouponsPage = () => {
  const [coupons, setCoupons] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const { authToken } = useAuth();
  
  useEffect(() => {
    const fetchCoupons = async () => {
      try {
        setLoading(true);
        
        const response = await fetch('/api/coupons/available', {
          headers: {
            'Authorization': `Bearer ${authToken}`
          }
        });
        
        if (!response.ok) {
          throw new Error('Falha ao carregar cupons');
        }
        
        const data = await response.json();
        setCoupons(data.coupons);
        
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    
    fetchCoupons();
  }, [authToken]);
  
  if (loading) {
    return <LoadingSpinner />;
  }
  
  if (error) {
    return <ErrorMessage message={error} />;
  }
  
  return (
    <div className="coupons-page">
      <h1 className="text-2xl font-bold mb-4">Meus Cupons</h1>
      
      {coupons.length === 0 ? (
        <EmptyState
          icon={<TicketIcon size={48} />}
          title="Sem cupons disponíveis"
          description="Você não tem cupons disponíveis no momento. Continue usando o app para receber ofertas exclusivas."
        />
      ) : (
        <div className="grid gap-4">
          {coupons.map(coupon => (
            <CouponCard key={coupon.id} coupon={coupon} />
          ))}
        </div>
      )}
    </div>
  );
};

const CouponCard = ({ coupon }) => {
  const {
    code,
    partner,
    gas_station,
    discount_type,
    discount_value,
    fuel_type,
    valid_until,
    description
  } = coupon;
  
  // Formatar data de validade
  const validUntilDate = new Date(valid_until);
  const formattedDate = validUntilDate.toLocaleDateString();
  
  // Formatar valor do desconto
  const formattedDiscount = discount_type === 'percentage'
    ? `${discount_value}%`
    : `R$ ${discount_value.toFixed(2)}`;
  
  return (
    <Card className="coupon-card">
      <CardHeader className="pb-2">
        <div className="flex justify-between items-center">
          <div>
            <CardTitle>{partner || 'Tanque Cheio'}</CardTitle>
            <CardDescription>{gas_station}</CardDescription>
          </div>
          <div className="discount-badge">
            <span>{formattedDiscount}</span>
            <small>OFF</small>
          </div>
        </div>
      </CardHeader>
      
      <CardContent>
        <div className="coupon-details">
          <p className="text-sm mb-1">
            <span className="text-muted-foreground">Combustível:</span> {fuel_type}
          </p>
          <p className="text-sm mb-3">
            <span className="text-muted-foreground">Válido até:</span> {formattedDate}
          </p>
          <p className="description">{description}</p>
        </div>
        
        <div className="coupon-code mt-4">
          <p className="text-xs text-muted-foreground mb-1">Código do cupom</p>
          <div className="code-display">
            <span className="font-mono font-bold">{code}</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                navigator.clipboard.writeText(code);
                toast.success('Código copiado!');
              }}
            >
              <CopyIcon size={16} />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
```

## 🔄 **Fluxo de Uso**

### **1. Criação de Cupons**

1. **Parceiros criam cupons** através do painel administrativo ou API
2. **Definem parâmetros:**
   - Código do cupom
   - Tipo de desconto (percentual ou valor fixo)
   - Valor do desconto
   - Período de validade
   - Restrições (posto específico, tipo de combustível, litros mínimos)
   - Limite de usos

### **2. Recomendação com Cupons**

1. **Usuário inicia viagem** com o app Tanque Cheio
2. **Sistema monitora localização** e detecta quando atingir o intervalo configurado
3. **Algoritmo de recomendação:**
   - Identifica postos próximos à rota
   - Verifica preços base de combustível
   - Busca cupons disponíveis para cada posto
   - Aplica o melhor cupom disponível para cada posto
   - Calcula economia total considerando preço com desconto e desvio necessário
   - Determina o posto com melhor custo-benefício

### **3. Notificação ao Usuário**

1. **Usuário recebe notificação push** com recomendação
2. **Notificação inclui:**
   - Nome do posto recomendado
   - Preço original e com desconto
   - Distância e tempo de desvio
   - Economia estimada
   - Detalhes do cupom (se aplicável)

### **4. Uso do Cupom**

1. **Usuário navega até o posto** recomendado
2. **Apresenta código do cupom** no caixa
3. **Sistema registra uso do cupom** e notifica parceiro
4. **Parceiro recebe comissão** baseada no uso do cupom

## 📊 **Métricas e Analytics**

### **1. Dashboard de Parceiros**

Os parceiros têm acesso a um dashboard com métricas importantes:

- **Cupons criados:** Total e por período
- **Cupons utilizados:** Taxa de conversão
- **Valor total de descontos:** Quanto foi concedido em descontos
- **Novos clientes:** Quantos usuários visitaram o posto pela primeira vez
- **Fidelização:** Taxa de retorno de usuários
- **ROI:** Retorno sobre investimento em cupons

### **2. Relatórios para Administradores**

A equipe do Tanque Cheio tem acesso a relatórios detalhados:

- **Uso de cupons por região:** Mapa de calor
- **Cupons mais populares:** Por tipo de desconto e combustível
- **Impacto nas recomendações:** Como os cupons afetam as escolhas dos usuários
- **Receita de comissões:** Valor gerado por parceiro
- **Economia para usuários:** Valor total economizado pelos usuários

## 🚀 **Próximos Passos**

### **1. Cupons Personalizados**

Implementar sistema de cupons personalizados baseados em:
- Histórico de abastecimento
- Localização frequente
- Padrões de consumo
- Fidelidade a marcas

### **2. Gamificação**

Adicionar elementos de gamificação:
- Cupons como recompensas por uso contínuo
- Desafios para desbloquear cupons especiais
- Sistema de níveis com benefícios crescentes
- Cupons sazonais e promocionais

### **3. Integração com Programas de Fidelidade**

Conectar com programas de fidelidade existentes:
- Petrobras Premmia
- Shell Box
- Ipiranga Km de Vantagens
- Outros programas de parceiros

### **4. Cupons Dinâmicos**

Implementar cupons com valores dinâmicos baseados em:
- Horário do dia (descontos maiores em horários de menor movimento)
- Nível de estoque do posto
- Preços da concorrência
- Condições climáticas

