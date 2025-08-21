import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from src.config import config
from src.database import init_database
from src.models.clean_models import CleanUser, CleanGasStation
from src.routes.clean_auth import clean_auth_bp
from src.routes.clean_gas_stations import clean_gas_stations_bp

def create_clean_app(config_name=None):
    """Application factory pattern - versão limpa"""
    if config_name is None:
        config_name = os.getenv('NODE_ENV', 'development')
    
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    init_database(app)
    
    # Initialize JWT
    jwt = JWTManager(app)
    
    # Initialize CORS
    CORS(app, origins=['*'])  # Permitir todas as origens para teste
    
    # JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            'success': False,
            'error': 'Token expirado'
        }), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({
            'success': False,
            'error': 'Token inválido'
        }), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({
            'success': False,
            'error': 'Token de acesso necessário'
        }), 401
    
    # Register blueprints
    app.register_blueprint(clean_auth_bp, url_prefix='/api/auth')
    app.register_blueprint(clean_gas_stations_bp, url_prefix='/api/gas-stations')
    
    # Health check endpoint
    @app.route('/api/health')
    def health_check():
        return jsonify({
            'success': True,
            'message': 'Tanque Cheio API Clean is running',
            'version': '1.0.0-clean',
            'environment': config_name
        }), 200
    
    # Root endpoint
    @app.route('/')
    def root():
        return jsonify({
            'success': True,
            'message': 'Tanque Cheio API Clean',
            'version': '1.0.0-clean',
            'endpoints': {
                'health': '/api/health',
                'auth': '/api/auth/*',
                'gas_stations': '/api/gas-stations/*'
            }
        }), 200
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 'Endpoint não encontrado'
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            'success': False,
            'error': 'Método não permitido'
        }), 405
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500
    
    return app

# Create app instance
app = create_clean_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    debug = os.getenv('NODE_ENV', 'development') == 'development'
    
    with app.app_context():
        # Create database tables
        from src.database import db
        db.create_all()
        print("✅ Database tables created successfully!")
        
        # Criar dados de exemplo se não existirem
        if CleanUser.query.count() == 0:
            # Usuário de exemplo
            user = CleanUser(
                name="Admin Tanque Cheio",
                email="admin@tanquecheio.app",
                phone="+55 11 99999-9999",
                preferred_fuel="gasoline"
            )
            user.set_password("admin123")
            db.session.add(user)
            
            # Postos de exemplo
            stations_data = [
                {
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
                    'name': 'Posto Petrobras Vila Olímpia',
                    'brand': 'Petrobras',
                    'address': 'Rua Funchal, 500 - São Paulo, SP',
                    'latitude': -23.5955,
                    'longitude': -46.6890,
                    'gasoline_price': 5.75,
                    'ethanol_price': 4.15,
                    'diesel_price': 5.35,
                    'diesel_s10_price': 5.55
                },
                {
                    'name': 'Posto Ipiranga República',
                    'brand': 'Ipiranga',
                    'address': 'Largo do Arouche, 200 - São Paulo, SP',
                    'latitude': -23.5431,
                    'longitude': -46.6291,
                    'gasoline_price': 5.95,
                    'ethanol_price': 4.35,
                    'diesel_price': 5.55,
                    'diesel_s10_price': 5.75
                }
            ]
            
            for station_data in stations_data:
                station = CleanGasStation(**station_data)
                db.session.add(station)
            
            db.session.commit()
            print("✅ Sample data created successfully!")
    
    print(f"🚀 Starting Tanque Cheio Clean API on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)

