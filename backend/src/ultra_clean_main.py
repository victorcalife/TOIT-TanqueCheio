import os
from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import uuid
from datetime import datetime, timedelta
import traceback

# Usar SQLite local
DATABASE_PATH = "/tmp/tanque_cheio_ultra.db"

def get_db_connection():
    """Conexão com SQLite"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Inicializa tabelas no banco"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Criar tabela de usuários
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ultra_users (
            id VARCHAR(36) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            phone VARCHAR(20),
            password_hash VARCHAR(255) NOT NULL,
            preferred_fuel VARCHAR(20) DEFAULT 'gasoline',
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    
    # Criar tabela de postos
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ultra_gas_stations (
            id VARCHAR(36) PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            brand VARCHAR(100),
            address TEXT,
            latitude DECIMAL(10,8) NOT NULL,
            longitude DECIMAL(11,8) NOT NULL,
            gasoline_price DECIMAL(6,3),
            ethanol_price DECIMAL(6,3),
            diesel_price DECIMAL(6,3),
            diesel_s10_price DECIMAL(6,3),
            gnv_price DECIMAL(6,3),
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    
    conn.commit()
    cur.close()
    conn.close()

def create_app():
    """Cria aplicação Flask ultra limpa"""
    app = Flask(__name__)
    
    # Configuração
    app.config['JWT_SECRET_KEY'] = 'tanque-cheio-ultra-secret-key-2025'
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    
    # Extensões
    jwt = JWTManager(app)
    CORS(app)
    
    # Inicializar banco
    init_database()
    
    @app.route('/api/health')
    def health():
        return jsonify({
            'success': True,
            'message': 'Tanque Cheio Ultra Clean API',
            'version': '1.0.0-ultra'
        })
    
    @app.route('/api/auth/register', methods=['POST'])
    def register():
        try:
            data = request.get_json()
            
            # Validação
            if not data.get('name') or not data.get('email') or not data.get('password'):
                return jsonify({
                    'success': False,
                    'error': 'Nome, email e senha são obrigatórios'
                }), 400
            
            conn = get_db_connection()
            cur = conn.cursor()
            
            # Verificar se email já existe
            cur.execute("SELECT id FROM ultra_users WHERE email = %s", (data['email'],))
            if cur.fetchone():
                return jsonify({
                    'success': False,
                    'error': 'Email já cadastrado'
                }), 409
            
            # Criar usuário
            user_id = str(uuid.uuid4())
            password_hash = generate_password_hash(data['password'])
            
            cur.execute("""
                INSERT INTO ultra_users (id, name, email, phone, password_hash, preferred_fuel)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                user_id,
                data['name'],
                data['email'],
                data.get('phone'),
                password_hash,
                data.get('preferred_fuel', 'gasoline')
            ))
            
            conn.commit()
            
            # Gerar token
            access_token = create_access_token(identity=user_id)
            
            # Buscar usuário criado
            cur.execute("SELECT id, name, email, phone, preferred_fuel, created_at FROM ultra_users WHERE id = %s", (user_id,))
            user = cur.fetchone()
            
            cur.close()
            conn.close()
            
            return jsonify({
                'success': True,
                'message': 'Usuário criado com sucesso',
                'user': dict(user),
                'access_token': access_token
            }), 201
            
        except Exception as e:
            print(f"Erro no registro: {e}")
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': 'Erro interno do servidor',
                'details': str(e)
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
            
            conn = get_db_connection()
            cur = conn.cursor()
            
            # Buscar usuário
            cur.execute("""
                SELECT id, name, email, phone, preferred_fuel, password_hash, is_active, created_at 
                FROM ultra_users WHERE email = %s
            """, (data['email'],))
            
            user = cur.fetchone()
            
            if not user or not check_password_hash(user['password_hash'], data['password']):
                return jsonify({
                    'success': False,
                    'error': 'Email ou senha inválidos'
                }), 401
            
            if not user['is_active']:
                return jsonify({
                    'success': False,
                    'error': 'Conta desativada'
                }), 401
            
            # Gerar token
            access_token = create_access_token(identity=user['id'])
            
            # Remover password_hash da resposta
            user_data = {k: v for k, v in user.items() if k != 'password_hash'}
            
            cur.close()
            conn.close()
            
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
            
            conn = get_db_connection()
            cur = conn.cursor()
            
            cur.execute("""
                SELECT id, name, email, phone, preferred_fuel, is_active, created_at 
                FROM ultra_users WHERE id = %s
            """, (user_id,))
            
            user = cur.fetchone()
            
            if not user:
                return jsonify({
                    'success': False,
                    'error': 'Usuário não encontrado'
                }), 404
            
            cur.close()
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
            conn = get_db_connection()
            cur = conn.cursor()
            
            cur.execute("""
                SELECT id, name, brand, address, latitude, longitude,
                       gasoline_price, ethanol_price, diesel_price, diesel_s10_price, gnv_price,
                       is_active, created_at
                FROM ultra_gas_stations 
                WHERE is_active = TRUE
                ORDER BY name
            """)
            
            stations = cur.fetchall()
            
            cur.close()
            conn.close()
            
            return jsonify({
                'success': True,
                'stations': [dict(station) for station in stations],
                'count': len(stations)
            }), 200
            
        except Exception as e:
            print(f"Erro ao listar postos: {e}")
            return jsonify({
                'success': False,
                'error': 'Erro interno do servidor'
            }), 500
    
    @app.route('/api/gas-stations', methods=['POST'])
    def create_gas_station():
        try:
            data = request.get_json()
            
            # Validação
            required = ['name', 'latitude', 'longitude']
            for field in required:
                if field not in data:
                    return jsonify({
                        'success': False,
                        'error': f'Campo {field} é obrigatório'
                    }), 400
            
            conn = get_db_connection()
            cur = conn.cursor()
            
            station_id = str(uuid.uuid4())
            
            cur.execute("""
                INSERT INTO ultra_gas_stations 
                (id, name, brand, address, latitude, longitude, gasoline_price, ethanol_price, 
                 diesel_price, diesel_s10_price, gnv_price)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                station_id,
                data['name'],
                data.get('brand'),
                data.get('address'),
                float(data['latitude']),
                float(data['longitude']),
                data.get('gasoline_price'),
                data.get('ethanol_price'),
                data.get('diesel_price'),
                data.get('diesel_s10_price'),
                data.get('gnv_price')
            ))
            
            conn.commit()
            
            # Buscar posto criado
            cur.execute("SELECT * FROM ultra_gas_stations WHERE id = %s", (station_id,))
            station = cur.fetchone()
            
            cur.close()
            conn.close()
            
            return jsonify({
                'success': True,
                'message': 'Posto criado com sucesso',
                'station': dict(station)
            }), 201
            
        except Exception as e:
            print(f"Erro ao criar posto: {e}")
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': 'Erro interno do servidor'
            }), 500
    
    # Inserir dados de exemplo na inicialização
    @app.before_first_request
    def create_sample_data():
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            # Verificar se já existem dados
            cur.execute("SELECT COUNT(*) FROM ultra_users")
            user_count = cur.fetchone()[0]
            
            if user_count == 0:
                # Criar usuário admin
                admin_id = str(uuid.uuid4())
                admin_password = generate_password_hash("admin123")
                
                cur.execute("""
                    INSERT INTO ultra_users (id, name, email, phone, password_hash, preferred_fuel)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (admin_id, "Admin Tanque Cheio", "admin@tanquecheio.app", "+55 11 99999-9999", admin_password, "gasoline"))
                
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
                        'diesel_s10_price': 5.65
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
                        'diesel_s10_price': 5.55
                    }
                ]
                
                for station in stations:
                    cur.execute("""
                        INSERT INTO ultra_gas_stations 
                        (id, name, brand, address, latitude, longitude, gasoline_price, ethanol_price, diesel_price, diesel_s10_price)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        station['id'], station['name'], station['brand'], station['address'],
                        station['latitude'], station['longitude'], station['gasoline_price'],
                        station['ethanol_price'], station['diesel_price'], station['diesel_s10_price']
                    ))
                
                conn.commit()
                print("✅ Sample data created!")
            
            cur.close()
            conn.close()
            
        except Exception as e:
            print(f"Erro ao criar dados de exemplo: {e}")
    
    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.getenv('PORT', 8080))
    print(f"🚀 Starting Tanque Cheio Ultra Clean API on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)

