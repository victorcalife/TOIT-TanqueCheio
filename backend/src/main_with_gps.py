#!/usr/bin/env python3
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
    
    # Tabela de viagens
    cur.execute('''
        CREATE TABLE IF NOT EXISTS trips (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            origin_address TEXT,
            destination_address TEXT,
            fuel_type TEXT DEFAULT 'gasoline',
            notification_interval INTEGER DEFAULT 100,
            status TEXT DEFAULT 'active',
            start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            end_time TIMESTAMP,
            distance_traveled REAL DEFAULT 0.0,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Tabela de pontos GPS
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
    
    # Tabela de notificações
    cur.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id TEXT PRIMARY KEY,
            trip_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            station_name TEXT,
            fuel_price REAL,
            coupon_code TEXT,
            distance_traveled REAL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            read BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (trip_id) REFERENCES trips (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

def find_cheapest_gas_station(latitude, longitude, fuel_type):
    """Simular busca do posto mais barato nas proximidades"""
    stations = [
        {
            'name': 'Posto Shell BR-101',
            'price': 5.75,
            'distance': 2.5,
            'coupon': 'SHELL10 - 10% desconto',
            'address': 'BR-101, Km 145'
        },
        {
            'name': 'Petrobras Itajaí',
            'price': 5.82,
            'distance': 4.1,
            'coupon': None,
            'address': 'Av. Marcos Konder, 1234'
        },
        {
            'name': 'Ipiranga Centro',
            'price': 5.69,
            'distance': 6.2,
            'coupon': 'IPIRANGA15 - R$ 0,15/litro',
            'address': 'Rua Central, 567'
        }
    ]
    
    return min(stations, key=lambda x: x['price'])

def create_sample_data():
    conn = get_db()
    cur = conn.cursor()
    
    # Verificar se já existem dados
    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] > 0:
        conn.close()
        return
    
    # Criar usuário admin
    admin_id = str(uuid.uuid4())
    admin_hash = generate_password_hash("admin123")
    
    cur.execute('''
        INSERT INTO users (id, name, email, phone, password_hash, preferred_fuel)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (admin_id, "Admin Tanque Cheio", "admin@tanquecheio.app", "+55 11 99999-9999", admin_hash, "gasoline"))
    
    # Criar postos de exemplo
    stations = [
        {
            'id': str(uuid.uuid4()),
            'name': 'Posto Shell Centro',
            'brand': 'Shell',
            'address': 'Av. Paulista, 1000 - São Paulo, SP',
            'latitude': -23.5505,
            'longitude': -46.6333,
            'gasoline_price': 5.89,
            'ethanol_price': 4.29,
            'diesel_price': 5.45,
            'diesel_s10_price': 5.65,
            'gnv_price': 4.85
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'Posto Petrobras Vila Olímpia',
            'brand': 'Petrobras',
            'address': 'Rua Funchal, 500 - São Paulo, SP',
            'latitude': -23.5955,
            'longitude': -46.6890,
            'gasoline_price': 5.75,
            'ethanol_price': 4.15,
            'diesel_price': 5.35,
            'diesel_s10_price': 5.55,
            'gnv_price': 4.75
        }
    ]
    
    for station in stations:
        cur.execute('''
            INSERT INTO gas_stations 
            (id, name, brand, address, latitude, longitude, gasoline_price, ethanol_price, diesel_price, diesel_s10_price, gnv_price)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            station['id'], station['name'], station['brand'], station['address'],
            station['latitude'], station['longitude'], station['gasoline_price'],
            station['ethanol_price'], station['diesel_price'], station['diesel_s10_price'], station['gnv_price']
        ))
    
    conn.commit()
    conn.close()

def create_app():
    app = Flask(__name__)
    
    app.config['JWT_SECRET_KEY'] = 'tanque-cheio-secret-2025'
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    
    jwt = JWTManager(app)
    CORS(app)
    
    init_db()
    create_sample_data()
    
    @app.route('/api/health')
    def health():
        return jsonify({
            'success': True,
            'message': 'Tanque Cheio API funcionando',
            'version': '1.0.0'
        })
    
    @app.route('/api/auth/register', methods=['POST'])
    def register():
        try:
            data = request.get_json()
            
            if not data.get('name') or not data.get('email') or not data.get('password'):
                return jsonify({
                    'success': False,
                    'error': 'Nome, email e senha são obrigatórios'
                }), 400
            
            conn = get_db()
            cur = conn.cursor()
            
            # Verificar email existente
            cur.execute("SELECT id FROM users WHERE email = ?", (data['email'],))
            if cur.fetchone():
                conn.close()
                return jsonify({
                    'success': False,
                    'error': 'Email já cadastrado'
                }), 409
            
            # Criar usuário
            user_id = str(uuid.uuid4())
            password_hash = generate_password_hash(data['password'])
            
            cur.execute('''
                INSERT INTO users (id, name, email, phone, password_hash, preferred_fuel)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                user_id, data['name'], data['email'], data.get('phone'),
                password_hash, data.get('preferred_fuel', 'gasoline')
            ))
            
            conn.commit()
            
            # Buscar usuário criado
            cur.execute("SELECT id, name, email, phone, preferred_fuel, created_at FROM users WHERE id = ?", (user_id,))
            user = dict(cur.fetchone())
            
            conn.close()
            
            # Gerar token
            access_token = create_access_token(identity=user_id)
            
            return jsonify({
                'success': True,
                'message': 'Usuário criado com sucesso',
                'user': user,
                'access_token': access_token
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
            
            if not data.get('email') or not data.get('password'):
                return jsonify({
                    'success': False,
                    'error': 'Email e senha são obrigatórios'
                }), 400
            
            conn = get_db()
            cur = conn.cursor()
            
            cur.execute("SELECT * FROM users WHERE email = ?", (data['email'],))
            user = cur.fetchone()
            
            if not user or not check_password_hash(user['password_hash'], data['password']):
                conn.close()
                return jsonify({
                    'success': False,
                    'error': 'Email ou senha inválidos'
                }), 401
            
            # Converter para dict e remover password_hash
            user_data = dict(user)
            del user_data['password_hash']
            
            conn.close()
            
            access_token = create_access_token(identity=user['id'])
            
            return jsonify({
                'success': True,
                'message': 'Login realizado com sucesso',
                'user': user_data,
                'access_token': access_token
            }), 200
            
        except Exception as e:
            print(f"Erro no login: {e}")
            return jsonify({
                'success': False,
                'error': 'Erro interno do servidor'
            }), 500
    
    # ===== APIs GPS =====
    
    @app.route('/api/gps/start-trip', methods=['POST'])
    @jwt_required()
    def start_trip():
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            
            conn = get_db()
            cur = conn.cursor()
            
            # Verificar se já existe viagem ativa
            cur.execute("SELECT id FROM trips WHERE user_id = ? AND status = 'active'", (user_id,))
            if cur.fetchone():
                conn.close()
                return jsonify({
                    'success': False,
                    'error': 'Já existe uma viagem ativa'
                }), 400
            
            # Criar nova viagem
            trip_id = str(uuid.uuid4())
            
            cur.execute('''
                INSERT INTO trips (id, user_id, origin_address, destination_address, fuel_type, notification_interval, status, distance_traveled)
                VALUES (?, ?, ?, ?, ?, ?, 'active', 0.0)
            ''', (
                trip_id, user_id,
                data.get('origin_address', 'Balneário Camboriú, SC'),
                data.get('destination_address', 'São Paulo, SP'),
                data.get('fuel_type', 'gasoline'),
                data.get('notification_interval', 100)
            ))
            
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True,
                'trip_id': trip_id,
                'message': f'Viagem iniciada! Notificações a cada {data.get("notification_interval", 100)}km'
            })
            
        except Exception as e:
            print(f"Erro ao iniciar viagem: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/gps/update-location', methods=['POST'])
    @jwt_required()
    def update_location():
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            
            conn = get_db()
            cur = conn.cursor()
            
            # Buscar viagem ativa
            cur.execute("SELECT * FROM trips WHERE user_id = ? AND status = 'active'", (user_id,))
            trip = cur.fetchone()
            
            if not trip:
                conn.close()
                return jsonify({
                    'success': False,
                    'error': 'Nenhuma viagem ativa encontrada'
                }), 400
            
            trip_dict = dict(trip)
            latitude = float(data.get('latitude'))
            longitude = float(data.get('longitude'))
            accuracy = data.get('accuracy', 10)
            speed = data.get('speed', 0)
            
            # Buscar último ponto GPS
            cur.execute("SELECT * FROM gps_points WHERE trip_id = ? ORDER BY timestamp DESC LIMIT 1", (trip_dict['id'],))
            last_point = cur.fetchone()
            
            # Calcular distância percorrida
            distance_increment = 0.0
            if last_point:
                distance_increment = calculate_distance(
                    last_point['latitude'], last_point['longitude'],
                    latitude, longitude
                )
            
            # Atualizar distância total da viagem
            new_distance = trip_dict['distance_traveled'] + distance_increment
            
            cur.execute("UPDATE trips SET distance_traveled = ? WHERE id = ?", (new_distance, trip_dict['id']))
            
            # Salvar novo ponto GPS
            gps_point_id = str(uuid.uuid4())
            cur.execute('''
                INSERT INTO gps_points (id, trip_id, latitude, longitude, accuracy, speed)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (gps_point_id, trip_dict['id'], latitude, longitude, accuracy, speed))
            
            # Verificar se deve enviar notificação
            notification_sent = False
            notification_message = None
            
            # Calcular quantas notificações já foram enviadas
            cur.execute("SELECT COUNT(*) FROM notifications WHERE trip_id = ?", (trip_dict['id'],))
            notifications_sent = cur.fetchone()[0]
            
            expected_notifications = int(new_distance // trip_dict['notification_interval'])
            
            if expected_notifications > notifications_sent:
                # Buscar posto mais barato
                station = find_cheapest_gas_station(latitude, longitude, trip_dict['fuel_type'])
                
                # Criar notificação
                notification_id = str(uuid.uuid4())
                cur.execute('''
                    INSERT INTO notifications (id, trip_id, user_id, title, message, station_name, fuel_price, coupon_code, distance_traveled)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    notification_id, trip_dict['id'], user_id,
                    '⛽ Posto Mais Barato Encontrado!',
                    f'{station["name"]} - R$ {station["price"]:.2f}/L - {station["distance"]:.1f}km de distância',
                    station['name'], station['price'], station.get('coupon'), new_distance
                ))
                
                notification_sent = True
                notification_message = f"⛽ {station['name']} - R$ {station['price']:.2f}/L"
                
                if station.get('coupon'):
                    notification_message += f" | Cupom: {station['coupon']}"
            
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True,
                'distance_traveled': round(new_distance, 2),
                'notification_sent': notification_sent,
                'notification_message': notification_message,
                'current_location': {
                    'latitude': latitude,
                    'longitude': longitude
                }
            })
            
        except Exception as e:
            print(f"Erro ao atualizar localização: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/gps/stop-trip', methods=['POST'])
    @jwt_required()
    def stop_trip():
        try:
            user_id = get_jwt_identity()
            
            conn = get_db()
            cur = conn.cursor()
            
            # Buscar viagem ativa
            cur.execute("SELECT * FROM trips WHERE user_id = ? AND status = 'active'", (user_id,))
            trip = cur.fetchone()
            
            if not trip:
                conn.close()
                return jsonify({
                    'success': False,
                    'error': 'Nenhuma viagem ativa encontrada'
                }), 400
            
            trip_dict = dict(trip)
            
            # Finalizar viagem
            cur.execute("UPDATE trips SET status = 'completed', end_time = CURRENT_TIMESTAMP WHERE id = ?", (trip_dict['id'],))
            
            # Calcular estatísticas
            cur.execute("SELECT COUNT(*) FROM notifications WHERE trip_id = ?", (trip_dict['id'],))
            notifications_count = cur.fetchone()[0]
            
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True,
                'trip_summary': {
                    'distance_traveled': round(trip_dict['distance_traveled'], 2),
                    'notifications_sent': notifications_count,
                    'fuel_type': trip_dict['fuel_type'],
                    'origin': trip_dict['origin_address'],
                    'destination': trip_dict['destination_address']
                }
            })
            
        except Exception as e:
            print(f"Erro ao finalizar viagem: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/gps/trip-status', methods=['GET'])
    @jwt_required()
    def get_trip_status():
        try:
            user_id = get_jwt_identity()
            
            conn = get_db()
            cur = conn.cursor()
            
            # Buscar viagem ativa
            cur.execute("SELECT * FROM trips WHERE user_id = ? AND status = 'active'", (user_id,))
            trip = cur.fetchone()
            
            if trip:
                trip_dict = dict(trip)
                conn.close()
                return jsonify({
                    'success': True,
                    'has_active_trip': True,
                    'trip': {
                        'id': trip_dict['id'],
                        'origin': trip_dict['origin_address'],
                        'destination': trip_dict['destination_address'],
                        'fuel_type': trip_dict['fuel_type'],
                        'distance_traveled': round(trip_dict['distance_traveled'], 2),
                        'notification_interval': trip_dict['notification_interval'],
                        'start_time': trip_dict['start_time']
                    }
                })
            else:
                conn.close()
                return jsonify({
                    'success': True,
                    'has_active_trip': False
                })
                
        except Exception as e:
            print(f"Erro ao obter status da viagem: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)

