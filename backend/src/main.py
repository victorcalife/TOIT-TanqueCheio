from flask import Flask, request, jsonify, send_from_directory, current_app
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt, verify_jwt_in_request
)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, timezone
import os
import sys
import traceback
import json
from database_postgres import db, init_database, test_connection, get_db_stats
from config_consolidated import get_config, config_by_name
from functools import wraps

# Configuração do sistema
sys.path.append(os.path.dirname(__file__))

def create_app(config_name=None):
    """Factory function para criar a aplicação Flask"""
    app = Flask(__name__)
    
    # Configuração da aplicação
    if config_name:
        config_object = config_by_name(config_name)
        if not config_object:
            raise ValueError(f"Configuração '{config_name}' não encontrada.")
        app.config.from_object(config_object)
    else:
        # Usa configuração baseada em ambiente
        app.config.from_object(get_config())
    
    # Inicializar extensões
    jwt = JWTManager(app)
    
    # Inicializar banco de dados PostgreSQL
    db.init_app(app)
    
    # Criar tabelas se não existirem (apenas em desenvolvimento)
    if app.config.get('ENV') == 'production':
        with app.app_context():
            db.create_all()
    
    # Configuração CORS simplificada e unificada
    @app.after_request
    def add_cors_headers(response):
        origin = request.headers.get('Origin', '')
        allowed_origins = [
            'https://fetc-production.up.railway.app',
            'https://tanquecheio.toit.com.br',
            'http://tanquecheio.toit.com.br',
            'https://betc-production.up.railway.app',
            'https://apitanquecheio.toit.com.br',
            'http://localhost:3000',
            'http://127.0.0.1:3000',
            'http://localhost:8080',
            'http://127.0.0.1:8080'
        ]
        
        if origin in allowed_origins:
            response.headers['Access-Control-Allow-Origin'] = origin
            
        # Always add these headers for all responses
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Accept, Origin, X-Session-Id'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Max-Age'] = '3600'  # Cache preflight for 1 hour
        
        # Handle preflight requests
        if request.method == 'OPTIONS':
            response.status_code = 204
            return response
            
        return response
    
    # Registrar blueprints
    from routes.auth import auth_bp
    from routes.user_profile import profile_bp
    from routes.gas_stations import gas_stations_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(profile_bp, url_prefix='/api/profile')
    app.register_blueprint(gas_stations_bp, url_prefix='/api/gas-stations')
    
    # Configuração do JWT
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            'success': False,
            'error': 'Token expirado',
            'is_authenticated': False
        }), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({
            'success': False,
            'error': 'Token inválido',
            'is_authenticated': False
        }), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({
            'success': False,
            'error': 'Token não fornecido',
            'is_authenticated': False
        }), 401

    @app.before_request
    @jwt_required(optional=True)
    def check_token():
        # Ignorar verificação para rotas públicas
        public_routes = ['login', 'register', 'health_check']
        if request.endpoint in public_routes or request.method == 'OPTIONS':
            return
            
        # Verificar token JWT
        try:
            verify_jwt_in_request(optional=True)
            
            # Verificar se o token está prestes a expirar (menos de 30 minutos)
            exp_timestamp = get_jwt().get('exp')
            if exp_timestamp:
                now = datetime.now(timezone.utc)
                target_timestamp = datetime.timestamp(now + timedelta(minutes=30))
                if target_timestamp > exp_timestamp:
                    # Criar novo token
                    identity = get_jwt_identity()
                    new_token = create_access_token(identity=identity, fresh=False)
                    
                    # Adicionar novo token ao cabeçalho da resposta
                    response = jsonify({
                        'success': True,
                        'message': 'Token atualizado',
                        'new_token': new_token
                    })
                    response.headers['X-New-Token'] = new_token
                    return response
                    
        except Exception as e:
            return jsonify({
                'success': False,
                'error': 'Falha na autenticação',
                'details': str(e),
                'is_authenticated': False
            }), 401
    
    # Health check
    @app.route('/api/health', methods=['GET'])
    def health_check():
        try:
            # Testar conexão com PostgreSQL
            connection_test = test_connection()
            db_stats = get_db_stats()
            
            return jsonify({
                'success': True,
                'message': 'Tanque Cheio API PostgreSQL funcionando',
                'version': '2.0.0',
                'database': connection_test,
                'stats': db_stats,
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e),
                'database': 'PostgreSQL connection failed'
            }), 500
    
    # Rota de registro
    @app.route('/api/auth/register', methods=['POST'])
    def register():
        try:
            data = request.get_json()
            
            # Validar dados obrigatórios
            required_fields = ['name', 'email', 'phone', 'password']
            for field in required_fields:
                if not data.get(field):
                    return jsonify({
                        'success': False,
                        'error': f'Campo {field} é obrigatório'
                    }), 400
            
            # Importar modelos
            from models.user import User
            from models.user_profile import UserProfile
            
            # Verificar se usuário já existe
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user:
                return jsonify({
                    'success': False,
                    'error': 'Email já cadastrado'
                }), 400
            
            # Criar usuário
            user = User(
                name=data['name'],
                email=data['email'],
                phone=data['phone'],
                password_hash=generate_password_hash(data['password'])
            )
            
            db.session.add(user)
            db.session.flush()  # Para obter o ID
            
            # Criar perfil padrão
            profile = UserProfile(
                user_id=user.id,
                preferred_fuel_type=data.get('preferred_fuel_type', 'gasoline'),
                notification_interval_km=data.get('notification_interval_km', 100),
                notifications_enabled=True
            )
            
            db.session.add(profile)
            db.session.commit()
            
            # Criar token JWT
            access_token = create_access_token(identity=user.id)
            
            return jsonify({
                'success': True,
                'message': 'Usuário criado com sucesso',
                'user': {
                    'id': user.id,
                    'name': user.name,
                    'email': user.email,
                    'phone': user.phone
                },
                'access_token': access_token
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': f'Erro interno: {str(e)}'
            }), 500
    
    # Rota de login
    @app.route('/api/auth/login', methods=['POST'])
    def login():
        try:
            data = request.get_json()
            
            if not data.get('email') or not data.get('password'):
                return jsonify({
                    'success': False,
                    'error': 'Email e senha são obrigatórios'
                }), 400
            
            from models.user import User
            
            # Buscar usuário
            user = User.query.filter_by(email=data['email']).first()
            
            if not user or not check_password_hash(user.password_hash, data['password']):
                return jsonify({
                    'success': False,
                    'error': 'Email ou senha inválidos'
                }), 401
            
            # Criar token JWT
            access_token = create_access_token(identity=user.id)
            
            return jsonify({
                'success': True,
                'message': 'Login realizado com sucesso',
                'user': {
                    'id': user.id,
                    'name': user.name,
                    'email': user.email,
                    'phone': user.phone
                },
                'access_token': access_token
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Erro interno: {str(e)}'
            }), 500
    
    # Rotas de postos de combustível foram movidas para o blueprint gas_stations_bp
    # que está registrado com o prefixo /api/gas-stations
    # Rota de recomendações
    @app.route('/api/recommendations', methods=['POST'])
    def get_recommendations():
        try:
            data = request.get_json()
            
            origin = data.get('origin', '')
            destination = data.get('destination', '')
            fuel_type = data.get('fuel_type', 'gasoline')
            
            if not origin or not destination:
                return jsonify({
                    'success': False,
                    'error': 'Origem e destino são obrigatórios'
                }), 400
            
            from models.gas_station import GasStation, FuelPrice
            import math
            
            # Buscar postos com o combustível solicitado
            fuel_prices = FuelPrice.query.filter_by(fuel_type=fuel_type).all()
            
            recommendations = []
            for fuel_price in fuel_prices:
                station = fuel_price.gas_station
                if not station.is_active:
                    continue
                
                # Calcular distância simulada (em produção usaria Google Maps)
                distance_from_route = abs(hash(station.name)) % 10 + 1  # 1-10 km
                detour_time = distance_from_route * 2  # 2 min por km
                
                # Calcular economia estimada
                regional_average = 5.75  # Média regional simulada
                savings_per_liter = max(0, regional_average - fuel_price.price)
                estimated_fuel_needed = 50  # Litros estimados
                total_savings = savings_per_liter * estimated_fuel_needed
                
                # Calcular score (economia vs desvio)
                if distance_from_route > 0:
                    score = max(0, (savings_per_liter * 10) - (distance_from_route * 0.5))
                else:
                    score = savings_per_liter * 10
                
                recommendations.append({
                    'station': {
                        'id': station.id,
                        'name': station.name,
                        'brand': station.brand,
                        'address': station.address,
                        'latitude': station.latitude,
                        'longitude': station.longitude
                    },
                    'fuel': {
                        'type': fuel_type,
                        'price': fuel_price.price,
                        'last_updated': fuel_price.last_updated.isoformat() if fuel_price.last_updated else None
                    },
                    'route_info': {
                        'distance_from_route': distance_from_route,
                        'detour_time_minutes': detour_time,
                        'savings_per_liter': round(savings_per_liter, 2),
                        'estimated_total_savings': round(total_savings, 2)
                    },
                    'score': round(score, 2)
                })
            
            # Ordenar por score (melhor primeiro)
            recommendations.sort(key=lambda x: x['score'], reverse=True)
            
            # Informações da rota
            route_info = {
                'origin': origin,
                'destination': destination,
                'estimated_distance_km': 7.57,
                'estimated_fuel_consumption_liters': 0.63,
                'fuel_type': fuel_type
            }
            
            return jsonify({
                'success': True,
                'route': route_info,
                'recommendations': recommendations[:5],  # Top 5
                'total_found': len(recommendations)
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Erro interno: {str(e)}'
            }), 500
    
    # Rota de perfil do usuário
    @app.route('/api/profile', methods=['GET'])
    @jwt_required()
    def get_profile():
        try:
            user_id = get_jwt_identity()
            
            from models.user import User
            from models.user_profile import UserProfile
            
            user = User.query.get(user_id)
            if not user:
                return jsonify({
                    'success': False,
                    'error': 'Usuário não encontrado'
                }), 404
            
            profile = UserProfile.query.filter_by(user_id=user_id).first()
            
            return jsonify({
                'success': True,
                'user': {
                    'id': user.id,
                    'name': user.name,
                    'email': user.email,
                    'phone': user.phone,
                    'created_at': user.created_at.isoformat() if user.created_at else None
                },
                'profile': {
                    'preferred_fuel_type': profile.preferred_fuel_type if profile else 'gasoline',
                    'notification_interval_km': profile.notification_interval_km if profile else 100,
                    'notifications_enabled': profile.notifications_enabled if profile else True,
                    'current_latitude': profile.current_latitude if profile else None,
                    'current_longitude': profile.current_longitude if profile else None,
                    'total_distance_traveled': profile.total_distance_traveled if profile else 0.0
                }
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Erro interno: {str(e)}'
            }), 500
    
    # Rota para atualizar perfil
    @app.route('/api/profile', methods=['PUT'])
    @jwt_required()
    def update_profile():
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            
            from models.user_profile import UserProfile
            
            profile = UserProfile.query.filter_by(user_id=user_id).first()
            if not profile:
                # Criar perfil se não existir
                profile = UserProfile(user_id=user_id)
                db.session.add(profile)
            
            # Atualizar campos se fornecidos
            if 'preferred_fuel_type' in data:
                profile.preferred_fuel_type = data['preferred_fuel_type']
            if 'notification_interval_km' in data:
                profile.notification_interval_km = data['notification_interval_km']
            if 'notifications_enabled' in data:
                profile.notifications_enabled = data['notifications_enabled']
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Perfil atualizado com sucesso'
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': f'Erro interno: {str(e)}'
            }), 500
    
    # Rota para iniciar viagem
    @app.route('/api/trips/start', methods=['POST'])
    @jwt_required()
    def start_trip():
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            
            from models.gps_tracking import Trip
            
            # Verificar se já há viagem ativa
            active_trip = Trip.query.filter_by(user_id=user_id, is_active=True).first()
            if active_trip:
                return jsonify({
                    'success': False,
                    'error': 'Já existe uma viagem ativa'
                }), 400
            
            # Criar nova viagem
            trip = Trip(
                user_id=user_id,
                origin=data.get('origin', ''),
                destination=data.get('destination', ''),
                fuel_type=data.get('fuel_type', 'gasoline'),
                start_latitude=data.get('latitude'),
                start_longitude=data.get('longitude'),
                is_active=True
            )
            
            db.session.add(trip)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Viagem iniciada com sucesso',
                'trip': {
                    'id': trip.id,
                    'origin': trip.origin,
                    'destination': trip.destination,
                    'fuel_type': trip.fuel_type,
                    'started_at': trip.started_at.isoformat()
                }
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': f'Erro interno: {str(e)}'
            }), 500
    
    # Rota para atualizar localização GPS
    @app.route('/api/gps/update', methods=['POST'])
    @jwt_required()
    def update_gps():
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            
            if not latitude or not longitude:
                return jsonify({
                    'success': False,
                    'error': 'Latitude e longitude são obrigatórias'
                }), 400
            
            from models.gps_tracking import GPSTracking, Trip
            from models.user_profile import UserProfile
            import math
            
            # Buscar viagem ativa
            active_trip = Trip.query.filter_by(user_id=user_id, is_active=True).first()
            if not active_trip:
                return jsonify({
                    'success': False,
                    'error': 'Nenhuma viagem ativa encontrada'
                }), 400
            
            # Buscar perfil do usuário
            profile = UserProfile.query.filter_by(user_id=user_id).first()
            
            # Calcular distância percorrida
            distance_traveled = 0.0
            if profile and profile.current_latitude and profile.current_longitude:
                # Fórmula de Haversine para calcular distância
                lat1, lon1 = math.radians(profile.current_latitude), math.radians(profile.current_longitude)
                lat2, lon2 = math.radians(latitude), math.radians(longitude)
                
                dlat = lat2 - lat1
                dlon = lon2 - lon1
                
                a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
                c = 2 * math.asin(math.sqrt(a))
                distance_traveled = 6371 * c  # Raio da Terra em km
            
            # Criar registro GPS
            gps_record = GPSTracking(
                user_id=user_id,
                trip_id=active_trip.id,
                latitude=latitude,
                longitude=longitude,
                accuracy=data.get('accuracy', 10.0),
                speed=data.get('speed', 0.0)
            )
            
            db.session.add(gps_record)
            
            # Atualizar perfil do usuário
            if profile:
                profile.current_latitude = latitude
                profile.current_longitude = longitude
                profile.total_distance_traveled += distance_traveled
                
                # Verificar se deve enviar notificação
                should_notify = False
                if profile.notifications_enabled and profile.notification_interval_km > 0:
                    if profile.total_distance_traveled >= profile.notification_interval_km:
                        should_notify = True
                        # Reset do contador (em produção seria mais sofisticado)
                        profile.total_distance_traveled = 0.0
            
            db.session.commit()
            
            response_data = {
                'success': True,
                'message': 'Localização atualizada com sucesso',
                'distance_traveled_km': round(distance_traveled, 2),
                'total_distance_km': round(profile.total_distance_traveled if profile else 0, 2)
            }
            
            if should_notify:
                response_data['notification'] = {
                    'should_notify': True,
                    'message': f'Você percorreu {profile.notification_interval_km}km! Verificando postos próximos...',
                    'fuel_type': profile.preferred_fuel_type
                }
            
            return jsonify(response_data)
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': f'Erro interno: {str(e)}'
            }), 500
    
    return app

# Criar a aplicação
app = create_app(os.getenv('FLASK_CONFIG', 'production'))

# Registrar APIs de inteligência de preços
try:
    from routes.intelligence_api import intelligence_bp
    app.register_blueprint(intelligence_bp, url_prefix='/api/intelligence')
    print("✅ APIs de inteligência de preços registradas")
except Exception as e:
    print(f"⚠️ Erro ao registrar APIs de inteligência: {e}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"🚀 Iniciando Tanque Cheio API PostgreSQL na porta {port}")
    app.run(host='0.0.0.0', port=port)
