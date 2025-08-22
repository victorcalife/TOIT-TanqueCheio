from flask_sqlalchemy import SQLAlchemy
import os

# Instância global do SQLAlchemy
db = SQLAlchemy()

def init_database(app):
    """
    Função mantida para compatibilidade com código existente.
    A inicialização do banco de dados agora é feita no main.py
    """
    pass

def populate_sample_data():
    """Popula dados de exemplo no PostgreSQL"""
    try:
        from models.user import User
        from models.user_profile import UserProfile
        from models.gas_station import GasStation, FuelPrice
        from models.partner import Partner
        from models.coupon import Coupon
        from werkzeug.security import generate_password_hash
        from datetime import datetime, timedelta
        
        # Verificar se já existem usuários
        if User.query.count() > 0:
            print("ℹ️  Já existem dados no banco. Pulando população de dados de exemplo.")
            return
            
        print("📝 Populando dados de exemplo...")
        
        # Criar usuário de exemplo
        user = User(
            name="João Motorista GPS",
            email="joao.motorista@gmail.com",
            phone="+55 47 99999-8888",
            password_hash=generate_password_hash("senha123456")
        )
        db.session.add(user)
        db.session.flush()  # Para obter o ID
        
        # Criar perfil do usuário
        profile = UserProfile(
            user_id=user.id,
            preferred_fuel_type="gasoline",
            notification_interval_km=100,
            notifications_enabled=True,
            current_latitude=-26.9194,
            current_longitude=-49.0661,
            total_distance_traveled=0.0
        )
        db.session.add(profile)
        
        # Criar postos de exemplo
        stations_data = [
            {
                'name': 'Shell BR-101',
                'brand': 'Shell',
                'address': 'BR-101, Km 142, Balneário Camboriú - SC',
                'latitude': -26.9194,
                'longitude': -49.0661,
                'city': 'Balneário Camboriú',
                'state': 'SC',
                'is_active': True,
                'fuels': {
                    'gasoline': 5.82,
                    'ethanol': 4.15,
                    'diesel': 5.95
                }
            },
            {
                'name': 'Ipiranga Centro',
                'brand': 'Ipiranga',
                'address': 'Av. Brasil, 1500, Centro, Balneário Camboriú - SC',
                'latitude': -26.9766,
                'longitude': -48.6354,
                'city': 'Balneário Camboriú',
                'state': 'SC',
                'is_active': True,
                'fuels': {
                    'gasoline': 5.67,
                    'ethanol': 4.02,
                    'diesel': 5.78,
                    'diesel_s10': 5.89
                }
            },
            {
                'name': 'Petrobras Rodovia',
                'brand': 'Petrobras',
                'address': 'BR-470, Km 89, Navegantes - SC',
                'latitude': -26.8986,
                'longitude': -48.6516,
                'city': 'Navegantes',
                'state': 'SC',
                'is_active': True,
                'fuels': {
                    'gasoline': 5.73,
                    'ethanol': 4.08,
                    'diesel': 5.84,
                    'gnv': 3.45
                }
            }
        ]
        
        for station_data in stations_data:
            # Criar posto
            station = GasStation(
                name=station_data['name'],
                brand=station_data['brand'],
                address=station_data['address'],
                latitude=station_data['latitude'],
                longitude=station_data['longitude'],
                is_active=True
            )
            db.session.add(station)
            db.session.flush()
            
            # Criar preços de combustível
            for fuel_type, price in station_data['fuels'].items():
                fuel_price = FuelPrice(
                    gas_station_id=station.id,
                    fuel_type=fuel_type,
                    price=price,
                    last_updated=datetime.utcnow()
                )
                db.session.add(fuel_price)
        
        # Criar parceiro de exemplo
        partner = Partner(
            name="Rede Shell Brasil",
            contact_email="parceria@shell.com.br",
            contact_phone="+55 11 3000-0000",
            commission_rate=0.05,
            is_active=True
        )
        db.session.add(partner)
        db.session.flush()
        
        # Criar cupons de exemplo
        coupons_data = [
            {
                'code': 'SHELL10',
                'description': 'Desconto de 10% na gasolina Shell',
                'discount_type': 'percentage',
                'discount_value': 10.0,
                'fuel_type': 'gasoline',
                'valid_until': datetime.utcnow() + timedelta(days=30)
            },
            {
                'code': 'IPIRANGA5',
                'description': 'R$ 5,00 de desconto no Ipiranga',
                'discount_type': 'fixed',
                'discount_value': 5.0,
                'fuel_type': 'any',
                'valid_until': datetime.utcnow() + timedelta(days=15)
            }
        ]
        
        for coupon_data in coupons_data:
            coupon = Coupon(
                partner_id=partner.id,
                code=coupon_data['code'],
                description=coupon_data['description'],
                discount_type=coupon_data['discount_type'],
                discount_value=coupon_data['discount_value'],
                fuel_type=coupon_data['fuel_type'],
                valid_until=coupon_data['valid_until'],
                is_active=True
            )
            db.session.add(coupon)
        
        # Commit todas as mudanças
        db.session.commit()
        print("✅ Dados de exemplo criados com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao popular dados: {e}")
        db.session.rollback()

def get_db_stats():
    """Retorna estatísticas do banco de dados"""
    try:
        from models.user import User
        from models.gas_station import GasStation, FuelPrice
        from models.partner import Partner
        from models.coupon import Coupon
        
        stats = {
            'users': User.query.count(),
            'gas_stations': GasStation.query.count(),
            'fuel_prices': FuelPrice.query.count(),
            'partners': Partner.query.count(),
            'coupons': Coupon.query.count(),
            'database_url': os.environ.get('DATABASE_URL', 'postgresql://postgres:HXmzPSGlMEcjpzICIZphyTFuNLcGbAjL@postgres-admt.railway.internal:5432/railway')[:50] + '...'
        }
        return stats
    except Exception as e:
        return {'error': str(e)}

def test_connection():
    """Testa a conexão com o banco PostgreSQL"""
    try:
        from sqlalchemy import text
        # Tentar executar uma query simples
        result = db.session.execute(text('SELECT 1 as test'))
        row = result.fetchone()
        if row and row[0] == 1:
            return {
                'status': 'success',
                'message': 'Conexão PostgreSQL funcionando!',
                'database': 'PostgreSQL'
            }
        else:
            return {
                'status': 'error',
                'message': 'Query de teste falhou',
                'database': 'PostgreSQL'
            }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Erro de conexão: {str(e)}',
            'database': 'PostgreSQL'
        }

