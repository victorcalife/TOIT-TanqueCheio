import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import uuid
from datetime import datetime, timedelta
import traceback
import math

DATABASE_PATH = "/tmp/tanque_cheio.db"

def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    
    # Tabela de usuários
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            password_hash TEXT NOT NULL,
            preferred_fuel TEXT DEFAULT 'gasoline',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de postos
    cur.execute('''
        CREATE TABLE IF NOT EXISTS gas_stations (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            brand TEXT,
            address TEXT,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            gasoline_price REAL,
            ethanol_price REAL,
            diesel_price REAL,
            diesel_s10_price REAL,
            gnv_price REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabelas GPS
    cur.execute('''
        CREATE TABLE IF NOT EXISTS trips (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            origin_address TEXT NOT NULL,
            destination_address TEXT NOT NULL,
            origin_latitude REAL NOT NULL,
            origin_longitude REAL NOT NULL,
            destination_latitude REAL NOT NULL,
            destination_longitude REAL NOT NULL,
            fuel_type TEXT NOT NULL DEFAULT 'gasoline',
            notification_interval INTEGER NOT NULL DEFAULT 100,
            distance_traveled REAL DEFAULT 0,
            last_notification_km REAL DEFAULT 0,
            status TEXT DEFAULT 'active',
            route_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMP,
            ended_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS gps_points (
            id TEXT PRIMARY KEY,
            trip_id TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            accuracy REAL,
            speed REAL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (trip_id) REFERENCES trips (id)
        )
    ''')
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS trip_notifications (
            id TEXT PRIMARY KEY,
            trip_id TEXT NOT NULL,
            gas_station_id TEXT,
            notification_type TEXT DEFAULT 'fuel_recommendation',
            message TEXT NOT NULL,
            distance_km REAL,
            fuel_price REAL,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            clicked BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (trip_id) REFERENCES trips (id),
            FOREIGN KEY (gas_station_id) REFERENCES gas_stations (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def populate_sample_data():
    conn = get_db()
    cur = conn.cursor()
    
    # Verificar se já existem dados
    cur.execute("SELECT COUNT(*) FROM gas_stations")
    if cur.fetchone()[0] > 0:
        conn.close()
        return
    
    # Dados de exemplo
    stations = [
        {
            'id': str(uuid.uuid4()),
            'name': 'Posto Shell Centro',
            'brand': 'Shell',
            'address': 'Av. Brasil, 1000 - Centro, São Paulo - SP',
            'latitude': -23.5505,
            'longitude': -46.6333,
            'gasoline_price': 5.89,
            'ethanol_price': 4.29,
            'diesel_price': 5.99,
            'diesel_s10_price': 6.09,
            'gnv_price': 4.89
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'Posto Petrobras Vila Olímpia',
            'brand': 'Petrobras',
            'address': 'Rua Funchal, 500 - Vila Olímpia, São Paulo - SP',
            'latitude': -23.5955,
            'longitude': -46.6890,
            'gasoline_price': 5.75,
            'ethanol_price': 4.15,
            'diesel_price': 5.85,
            'diesel_s10_price': 5.95,
            'gnv_price': 4.75
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'Posto Ipiranga Moema',
            'brand': 'Ipiranga',
            'address': 'Av. Ibirapuera, 2000 - Moema, São Paulo - SP',
            'latitude': -23.5893,
            'longitude': -46.6658,
            'gasoline_price': 5.79,
            'ethanol_price': 4.19,
            'diesel_price': 5.89,
            'diesel_s10_price': 5.99,
            'gnv_price': 4.79
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'Posto Shell BR-101 Balneário Camboriú',
            'brand': 'Shell',
            'address': 'BR-101, Km 145 - Balneário Camboriú, SC',
            'latitude': -26.9906,
            'longitude': -48.6356,
            'gasoline_price': 5.95,
            'ethanol_price': 4.35,
            'diesel_price': 6.05,
            'diesel_s10_price': 6.15,
            'gnv_price': 4.95
        }
    ]
    
    for station in stations:
        cur.execute('''
            INSERT INTO gas_stations 
            (id, name, brand, address, latitude, longitude, gasoline_price, ethanol_price, 
             diesel_price, diesel_s10_price, gnv_price)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            station['id'], station['name'], station['brand'], station['address'],
            station['latitude'], station['longitude'], station['gasoline_price'],
            station['ethanol_price'], station['diesel_price'], station['diesel_s10_price'],
            station['gnv_price']
        ))
    
    conn.commit()
    conn.close()

def create_app():
    app = Flask(__name__)
    app.config['JWT_SECRET_KEY'] = 'tanque-cheio-secret-key-2025'
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)
    
    jwt = JWTManager(app)
    CORS(app)
    
    # Importar serviços GPS
    from services.maps_service import maps_service
    from models.trip import trip_manager
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({
            'success': True,
            'message': 'Tanque Cheio API funcionando',
            'version': '1.0.0'
        }), 200
    
    @app.route('/api/auth/register', methods=['POST'])
    def register():
        try:
            data = request.get_json()
            name = data.get('name')
            email = data.get('email')
            phone = data.get('phone')
            password = data.get('password')
            
            if not all([name, email, password]):
                return jsonify({
                    'success': False,
                    'error': 'Nome, email e senha são obrigatórios'
                }), 400
            
            conn = get_db()
            cur = conn.cursor()
            
            # Verificar se email já existe
            cur.execute("SELECT id FROM users WHERE email = ?", (email,))
            if cur.fetchone():
                conn.close()
                return jsonify({
                    'success': False,
                    'error': 'Email já cadastrado'
                }), 409
            
            # Criar usuário
            user_id = str(uuid.uuid4())
            password_hash = generate_password_hash(password)
            
            cur.execute('''
                INSERT INTO users (id, name, email, phone, password_hash)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, name, email, phone, password_hash))
            
            conn.commit()
            conn.close()
            
            # Gerar token
            access_token = create_access_token(identity=user_id)
            
            return jsonify({
                'success': True,
                'message': 'Usuário criado com sucesso',
                'access_token': access_token,
                'user': {
                    'id': user_id,
                    'name': name,
                    'email': email,
                    'phone': phone
                }
            }), 201
            
        except Exception as e:
            print(f"Erro no registro: {e}")
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': 'Erro interno do servidor'
            }), 500
    
    @app.route('/api/auth/login', methods=['POST'])
    def login():
        try:
            data = request.get_json()
            email = data.get('email')
            password = data.get('password')
            
            if not email or not password:
                return jsonify({
                    'success': False,
                    'error': 'Email e senha são obrigatórios'
                }), 400
            
            conn = get_db()
            cur = conn.cursor()
            
            cur.execute("SELECT * FROM users WHERE email = ?", (email,))
            user = cur.fetchone()
            conn.close()
            
            if not user or not check_password_hash(user['password_hash'], password):
                return jsonify({
                    'success': False,
                    'error': 'Email ou senha inválidos'
                }), 401
            
            access_token = create_access_token(identity=user['id'])
            
            return jsonify({
                'success': True,
                'message': 'Login realizado com sucesso',
                'access_token': access_token,
                'user': {
                    'id': user['id'],
                    'name': user['name'],
                    'email': user['email'],
                    'phone': user['phone']
                }
            }), 200
            
        except Exception as e:
            print(f"Erro no login: {e}")
            return jsonify({
                'success': False,
                'error': 'Erro interno do servidor'
            }), 500
    
    @app.route('/api/auth/me', methods=['GET'])
    @jwt_required()
    def get_current_user():
        try:
            user_id = get_jwt_identity()
            
            conn = get_db()
            cur = conn.cursor()
            
            cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            user = cur.fetchone()
            conn.close()
            
            if not user:
                return jsonify({
                    'success': False,
                    'error': 'Usuário não encontrado'
                }), 404
            
            return jsonify({
                'success': True,
                'user': {
                    'id': user['id'],
                    'name': user['name'],
                    'email': user['email'],
                    'phone': user['phone'],
                    'preferred_fuel': user['preferred_fuel']
                }
            }), 200
            
        except Exception as e:
            print(f"Erro ao obter usuário: {e}")
            return jsonify({
                'success': False,
                'error': 'Erro interno do servidor'
            }), 500
    
    @app.route('/api/gas-stations', methods=['GET'])
    def get_gas_stations():
        try:
            conn = get_db()
            cur = conn.cursor()
            
            cur.execute("SELECT * FROM gas_stations ORDER BY name")
            stations = [dict(row) for row in cur.fetchall()]
            conn.close()
            
            return jsonify({
                'success': True,
                'gas_stations': stations,
                'count': len(stations)
            }), 200
            
        except Exception as e:
            print(f"Erro ao obter postos: {e}")
            return jsonify({
                'success': False,
                'error': 'Erro interno do servidor'
            }), 500
    
    @app.route('/api/recommendations', methods=['POST'])
    def get_recommendations():
        try:
            data = request.get_json()
            origin = data.get('origin', 'República, São Paulo, SP')
            destination = data.get('destination', 'Vila Olímpia, São Paulo, SP')
            fuel_type = data.get('fuel_type', 'gasoline')
            
            # Simular coordenadas
            origin_coords = (-23.5431, -46.6291)  # República
            dest_coords = (-23.5955, -46.6890)    # Vila Olímpia
            
            conn = get_db()
            cur = conn.cursor()
            
            fuel_column = f"{fuel_type}_price"
            cur.execute(f'''
                SELECT * FROM gas_stations 
                WHERE {fuel_column} IS NOT NULL 
                ORDER BY {fuel_column} ASC
            ''')
            
            stations = cur.fetchall()
            conn.close()
            
            recommendations = []
            
            for station in stations:
                # Calcular distância do posto à rota
                station_coords = (station['latitude'], station['longitude'])
                distance_to_station = calculate_distance(origin_coords, station_coords)
                
                # Calcular desvio
                direct_distance = calculate_distance(origin_coords, dest_coords)
                detour_distance = distance_to_station + calculate_distance(station_coords, dest_coords) - direct_distance
                
                if detour_distance <= 10:  # Máximo 10km de desvio
                    fuel_price = station[fuel_column]
                    
                    # Calcular score (menor é melhor)
                    price_score = fuel_price * 0.4
                    distance_score = distance_to_station * 0.3
                    detour_score = detour_distance * 0.3
                    total_score = price_score + distance_score + detour_score
                    
                    recommendations.append({
                        'station': dict(station),
                        'fuel_price': fuel_price,
                        'distance_km': round(distance_to_station, 2),
                        'detour_km': round(detour_distance, 2),
                        'score': round(total_score, 2)
                    })
            
            # Ordenar por score
            recommendations.sort(key=lambda x: x['score'])
            
            return jsonify({
                'success': True,
                'route_info': {
                    'origin': origin,
                    'destination': destination,
                    'distance_km': round(direct_distance, 2),
                    'estimated_fuel_liters': round(direct_distance * 0.08, 2)
                },
                'recommendations': recommendations[:5],
                'count': len(recommendations)
            }), 200
            
        except Exception as e:
            print(f"Erro nas recomendações: {e}")
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': 'Erro interno do servidor'
            }), 500
    
    # APIs Google Maps
    @app.route('/api/maps/geocode', methods=['POST'])
    def geocode_address():
        try:
            data = request.get_json()
            address = data.get('address')
            
            if not address:
                return jsonify({
                    'success': False,
                    'error': 'Endereço é obrigatório'
                }), 400
            
            result = maps_service.geocode_address(address)
            
            if result:
                return jsonify({
                    'success': True,
                    'location': result
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': 'Endereço não encontrado'
                }), 404
                
        except Exception as e:
            print(f"Erro no geocoding: {e}")
            return jsonify({
                'success': False,
                'error': 'Erro interno do servidor'
            }), 500
    
    @app.route('/api/maps/route', methods=['POST'])
    def get_route():
        try:
            data = request.get_json()
            origin = data.get('origin')
            destination = data.get('destination')
            
            if not origin or not destination:
                return jsonify({
                    'success': False,
                    'error': 'Origem e destino são obrigatórios'
                }), 400
            
            result = maps_service.get_route(origin, destination)
            
            if result:
                return jsonify({
                    'success': True,
                    'route': result
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': 'Rota não encontrada'
                }), 404
                
        except Exception as e:
            print(f"Erro ao obter rota: {e}")
            return jsonify({
                'success': False,
                'error': 'Erro interno do servidor'
            }), 500
    
    # APIs GPS Tracking
    @app.route('/api/gps/start-trip', methods=['POST'])
    @jwt_required()
    def start_trip():
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            
            origin_address = data.get('origin_address')
            destination_address = data.get('destination_address')
            fuel_type = data.get('fuel_type', 'gasoline')
            notification_interval = data.get('notification_interval', 100)
            
            if not origin_address or not destination_address:
                return jsonify({
                    'success': False,
                    'error': 'Endereços de origem e destino são obrigatórios'
                }), 400
            
            # Geocoding dos endereços
            origin_coords = maps_service.geocode_address(origin_address)
            dest_coords = maps_service.geocode_address(destination_address)
            
            if not origin_coords or not dest_coords:
                return jsonify({
                    'success': False,
                    'error': 'Não foi possível localizar os endereços'
                }), 400
            
            # Obter rota
            route_data = maps_service.get_route_coordinates(
                origin_coords['latitude'], origin_coords['longitude'],
                dest_coords['latitude'], dest_coords['longitude']
            )
            
            # Verificar se já existe viagem ativa
            active_trip = trip_manager.get_active_trip(user_id)
            if active_trip:
                # Finalizar viagem anterior
                trip_manager.end_trip(active_trip['id'])
            
            # Criar nova viagem
            trip_id = trip_manager.create_trip(
                user_id=user_id,
                origin_address=origin_address,
                destination_address=destination_address,
                origin_lat=origin_coords['latitude'],
                origin_lng=origin_coords['longitude'],
                dest_lat=dest_coords['latitude'],
                dest_lng=dest_coords['longitude'],
                fuel_type=fuel_type,
                notification_interval=notification_interval,
                route_data=route_data
            )
            
            return jsonify({
                'success': True,
                'message': 'Viagem iniciada com sucesso',
                'trip_id': trip_id,
                'route': route_data,
                'origin': origin_coords,
                'destination': dest_coords
            }), 201
            
        except Exception as e:
            print(f"Erro ao iniciar viagem: {e}")
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': 'Erro interno do servidor'
            }), 500
    
    @app.route('/api/gps/update-location', methods=['POST'])
    @jwt_required()
    def update_location():
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            accuracy = data.get('accuracy')
            speed = data.get('speed')
            
            if not latitude or not longitude:
                return jsonify({
                    'success': False,
                    'error': 'Coordenadas são obrigatórias'
                }), 400
            
            # Obter viagem ativa
            active_trip = trip_manager.get_active_trip(user_id)
            if not active_trip:
                return jsonify({
                    'success': False,
                    'error': 'Nenhuma viagem ativa encontrada'
                }), 404
            
            # Adicionar ponto GPS
            point_id = trip_manager.add_gps_point(
                trip_id=active_trip['id'],
                latitude=latitude,
                longitude=longitude,
                accuracy=accuracy,
                speed=speed
            )
            
            # Calcular distância percorrida
            distance_traveled = trip_manager.calculate_distance_traveled(active_trip['id'])
            trip_manager.update_trip_distance(active_trip['id'], distance_traveled)
            
            # Verificar se deve enviar notificação
            should_notify = trip_manager.should_send_notification(active_trip['id'])
            notification_sent = False
            
            if should_notify:
                # Buscar posto mais barato na rota
                fuel_type = active_trip['fuel_type']
                notification_sent = send_fuel_notification(active_trip, latitude, longitude, fuel_type)
            
            return jsonify({
                'success': True,
                'message': 'Localização atualizada',
                'point_id': point_id,
                'distance_traveled': round(distance_traveled, 2),
                'notification_sent': notification_sent
            }), 200
            
        except Exception as e:
            print(f"Erro ao atualizar localização: {e}")
            return jsonify({
                'success': False,
                'error': 'Erro interno do servidor'
            }), 500
    
    def send_fuel_notification(trip, current_lat, current_lng, fuel_type):
        """Envia notificação de combustível mais barato"""
        try:
            # Buscar postos próximos
            conn = get_db()
            cur = conn.cursor()
            
            fuel_column = f"{fuel_type}_price"
            cur.execute(f'''
                SELECT * FROM gas_stations 
                WHERE {fuel_column} IS NOT NULL 
                ORDER BY {fuel_column} ASC
                LIMIT 5
            ''')
            
            stations = cur.fetchall()
            conn.close()
            
            if not stations:
                return False
            
            # Encontrar posto mais próximo e barato
            best_station = None
            best_distance = float('inf')
            
            for station in stations:
                distance = calculate_distance(
                    (current_lat, current_lng),
                    (station['latitude'], station['longitude'])
                )
                
                # Considerar apenas postos até 50km de distância
                if distance < 50 and distance < best_distance:
                    best_distance = distance
                    best_station = station
            
            if best_station:
                fuel_price = best_station[fuel_column]
                message = f"⛽ {best_station['name']} - R$ {fuel_price:.2f}/L - {best_distance:.1f}km à frente"
                
                # Marcar notificação como enviada
                trip_manager.mark_notification_sent(
                    trip_id=trip['id'],
                    gas_station_id=best_station['id'],
                    message=message,
                    distance_km=best_distance,
                    fuel_price=fuel_price
                )
                
                print(f"🔔 Notificação enviada: {message}")
                return True
            
            return False
            
        except Exception as e:
            print(f"Erro ao enviar notificação: {e}")
            return False
    
    @app.route('/api/gps/stop-trip', methods=['POST'])
    @jwt_required()
    def stop_trip():
        try:
            user_id = get_jwt_identity()
            
            # Obter viagem ativa
            active_trip = trip_manager.get_active_trip(user_id)
            if not active_trip:
                return jsonify({
                    'success': False,
                    'error': 'Nenhuma viagem ativa encontrada'
                }), 404
            
            # Finalizar viagem
            success = trip_manager.end_trip(active_trip['id'])
            
            if success:
                # Calcular estatísticas finais
                final_distance = trip_manager.calculate_distance_traveled(active_trip['id'])
                
                return jsonify({
                    'success': True,
                    'message': 'Viagem finalizada com sucesso',
                    'trip_summary': {
                        'trip_id': active_trip['id'],
                        'distance_traveled': round(final_distance, 2),
                        'origin': active_trip['origin_address'],
                        'destination': active_trip['destination_address'],
                        'fuel_type': active_trip['fuel_type']
                    }
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': 'Erro ao finalizar viagem'
                }), 500
                
        except Exception as e:
            print(f"Erro ao parar viagem: {e}")
            return jsonify({
                'success': False,
                'error': 'Erro interno do servidor'
            }), 500
    
    @app.route('/api/gps/trip-status', methods=['GET'])
    @jwt_required()
    def get_trip_status():
        try:
            user_id = get_jwt_identity()
            
            # Obter viagem ativa
            active_trip = trip_manager.get_active_trip(user_id)
            
            if active_trip:
                distance_traveled = trip_manager.calculate_distance_traveled(active_trip['id'])
                
                return jsonify({
                    'success': True,
                    'has_active_trip': True,
                    'trip': {
                        'id': active_trip['id'],
                        'origin': active_trip['origin_address'],
                        'destination': active_trip['destination_address'],
                        'fuel_type': active_trip['fuel_type'],
                        'notification_interval': active_trip['notification_interval'],
                        'distance_traveled': round(distance_traveled, 2),
                        'started_at': active_trip['started_at']
                    }
                }), 200
            else:
                return jsonify({
                    'success': True,
                    'has_active_trip': False,
                    'trip': None
                }), 200
                
        except Exception as e:
            print(f"Erro ao obter status da viagem: {e}")
            return jsonify({
                'success': False,
                'error': 'Erro interno do servidor'
            }), 500
    
    return app

def calculate_distance(coord1, coord2):
    """Calcula distância entre duas coordenadas usando fórmula de Haversine"""
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    
    R = 6371  # Raio da Terra em km
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

if __name__ == '__main__':
    app = create_app()
    init_db()
    populate_sample_data()
    
    port = int(os.environ.get('PORT', 8080))
    print(f"🚀 Iniciando Tanque Cheio API na porta {port}")
    app.run(host='0.0.0.0', port=port, debug=True)

