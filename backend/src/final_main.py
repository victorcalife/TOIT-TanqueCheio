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
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'Posto Ipiranga República',
            'brand': 'Ipiranga',
            'address': 'Largo do Arouche, 200 - São Paulo, SP',
            'latitude': -23.5431,
            'longitude': -46.6291,
            'gasoline_price': 5.95,
            'ethanol_price': 4.35,
            'diesel_price': 5.55,
            'diesel_s10_price': 5.75,
            'gnv_price': 4.95
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'Posto Ale Moema',
            'brand': 'Ale',
            'address': 'Av. Ibirapuera, 800 - São Paulo, SP',
            'latitude': -23.5893,
            'longitude': -46.6658,
            'gasoline_price': 5.69,
            'ethanol_price': 4.09,
            'diesel_price': 5.25,
            'diesel_s10_price': 5.45,
            'gnv_price': 4.65
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
    print("✅ Dados de exemplo criados!")

def create_app():
    app = Flask(__name__)
    
    app.config['JWT_SECRET_KEY'] = ( 'aouH&9sa&a86dsha*A6doishaoisjao' )
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    
    jwt = JWTManager(app)
    CORS(app)
    
    init_db()
    create_sample_data()
    
    # API Routes
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
    
    @app.route('/api/auth/me', methods=['GET'])
    @jwt_required()
    def get_current_user():
        try:
            user_id = get_jwt_identity()
            
            conn = get_db()
            cur = conn.cursor()
            
            cur.execute("SELECT id, name, email, phone, preferred_fuel, created_at FROM users WHERE id = ?", (user_id,))
            user = cur.fetchone()
            
            if not user:
                conn.close()
                return jsonify({
                    'success': False,
                    'error': 'Usuário não encontrado'
                }), 404
            
            conn.close()
            
            return jsonify({
                'success': True,
                'user': dict(user)
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
                'stations': stations,
                'count': len(stations)
            }), 200
            
        except Exception as e:
            print(f"Erro ao listar postos: {e}")
            return jsonify({
                'success': False,
                'error': 'Erro interno do servidor'
            }), 500
    
    @app.route('/api/recommendations', methods=['POST'])
    def get_recommendations():
        try:
            data = request.get_json()
            
            origin_lat = data.get('origin_latitude')
            origin_lng = data.get('origin_longitude')
            dest_lat = data.get('destination_latitude')
            dest_lng = data.get('destination_longitude')
            fuel_type = data.get('fuel_type', 'gasoline')
            
            if not all([origin_lat, origin_lng, dest_lat, dest_lng]):
                return jsonify({
                    'success': False,
                    'error': 'Coordenadas de origem e destino são obrigatórias'
                }), 400
            
            # Calcular distância da rota
            route_distance = calculate_distance(origin_lat, origin_lng, dest_lat, dest_lng)
            
            # Estimar combustível necessário (assumindo 12km/L)
            fuel_needed = route_distance / 12.0
            
            conn = get_db()
            cur = conn.cursor()
            
            # Buscar postos com preços
            fuel_column = f"{fuel_type}_price"
            cur.execute(f"SELECT * FROM gas_stations WHERE {fuel_column} IS NOT NULL ORDER BY {fuel_column}")
            stations = cur.fetchall()
            
            recommendations = []
            
            for station in stations:
                station_dict = dict(station)
                
                # Calcular desvio da rota
                detour_distance = (
                    calculate_distance(origin_lat, origin_lng, station['latitude'], station['longitude']) +
                    calculate_distance(station['latitude'], station['longitude'], dest_lat, dest_lng)
                ) - route_distance
                
                # Filtrar desvios muito grandes (>10km)
                if detour_distance > 10:
                    continue
                
                fuel_price = station[fuel_column]
                
                # Calcular economia (comparando com preço médio de R$ 6,00)
                reference_price = 6.00
                savings = (reference_price - fuel_price) * fuel_needed
                
                # Calcular score (preço 40%, distância 30%, economia 30%)
                price_score = max(0, 10 - (fuel_price - 4.0) * 2)
                distance_score = max(0, 10 - detour_distance)
                savings_score = max(0, savings * 2)
                
                total_score = (price_score * 0.4 + distance_score * 0.3 + savings_score * 0.3)
                
                recommendation = {
                    'station': station_dict,
                    'fuel_price': fuel_price,
                    'detour_distance_km': round(detour_distance, 2),
                    'detour_time_minutes': round(detour_distance * 2, 0),  # Estimativa 30km/h
                    'savings_amount': round(savings, 2),
                    'recommendation_score': round(total_score, 2)
                }
                
                recommendations.append(recommendation)
            
            # Ordenar por score
            recommendations.sort(key=lambda x: x['recommendation_score'], reverse=True)
            
            conn.close()
            
            return jsonify({
                'success': True,
                'route_info': {
                    'distance_km': round(route_distance, 2),
                    'estimated_fuel_liters': round(fuel_needed, 2),
                    'fuel_type': fuel_type
                },
                'recommendations': recommendations[:10],
                'count': len(recommendations)
            }), 200
            
        except Exception as e:
            print(f"Erro nas recomendações: {e}")
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': 'Erro interno do servidor'
            }), 500
    
    @app.route('/')
    def root():
        return jsonify({
            'success': True,
            'message': 'Tanque Cheio API',
            'version': '1.0.0',
            'endpoints': {
                'health': '/api/health',
                'auth': '/api/auth/*',
                'gas_stations': '/api/gas-stations/*',
                'recommendations': '/api/recommendations'
            }
        })
    
    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.getenv('PORT', 8080))
    print(f"🚀 Iniciando Tanque Cheio API na porta {port}")
    app.run(host='0.0.0.0', port=port, debug=True)

