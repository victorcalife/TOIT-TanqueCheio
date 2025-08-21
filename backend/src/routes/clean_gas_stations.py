from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.database import db
from src.models.clean_models import CleanGasStation
import math
import traceback

clean_gas_stations_bp = Blueprint('clean_gas_stations', __name__)

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calcula distância entre dois pontos usando fórmula de Haversine"""
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

@clean_gas_stations_bp.route('/', methods=['GET'])
def get_gas_stations():
    """Lista todos os postos de combustível"""
    try:
        stations = CleanGasStation.query.filter_by(is_active=True).all()
        
        return jsonify({
            'success': True,
            'stations': [station.to_dict() for station in stations],
            'count': len(stations)
        }), 200
        
    except Exception as e:
        print(f"Erro ao listar postos: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500

@clean_gas_stations_bp.route('/', methods=['POST'])
def create_gas_station():
    """Cria novo posto de combustível"""
    try:
        data = request.get_json()
        
        # Validar dados obrigatórios
        required_fields = ['name', 'latitude', 'longitude']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Campo {field} é obrigatório'
                }), 400
        
        # Criar posto
        station = CleanGasStation(
            name=data['name'],
            brand=data.get('brand'),
            address=data.get('address'),
            latitude=float(data['latitude']),
            longitude=float(data['longitude']),
            gasoline_price=data.get('gasoline_price'),
            ethanol_price=data.get('ethanol_price'),
            diesel_price=data.get('diesel_price'),
            diesel_s10_price=data.get('diesel_s10_price'),
            gnv_price=data.get('gnv_price')
        )
        
        db.session.add(station)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Posto criado com sucesso',
            'station': station.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao criar posto: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500

@clean_gas_stations_bp.route('/nearby', methods=['GET'])
def get_nearby_stations():
    """Busca postos próximos a uma localização"""
    try:
        # Parâmetros de busca
        latitude = request.args.get('latitude', type=float)
        longitude = request.args.get('longitude', type=float)
        radius_km = request.args.get('radius', 10, type=float)
        fuel_type = request.args.get('fuel_type', 'gasoline')
        
        if not latitude or not longitude:
            return jsonify({
                'success': False,
                'error': 'Latitude e longitude são obrigatórias'
            }), 400
        
        # Buscar todos os postos ativos
        stations = CleanGasStation.query.filter_by(is_active=True).all()
        
        nearby_stations = []
        for station in stations:
            # Calcular distância
            distance = calculate_distance(
                latitude, longitude,
                float(station.latitude), float(station.longitude)
            )
            
            # Filtrar por raio
            if distance <= radius_km:
                station_data = station.to_dict()
                station_data['distance_km'] = round(distance, 2)
                station_data['fuel_price'] = station.get_fuel_price(fuel_type)
                
                # Só incluir se tem preço do combustível
                if station_data['fuel_price']:
                    nearby_stations.append(station_data)
        
        # Ordenar por distância
        nearby_stations.sort(key=lambda x: x['distance_km'])
        
        return jsonify({
            'success': True,
            'stations': nearby_stations,
            'count': len(nearby_stations),
            'search_params': {
                'latitude': latitude,
                'longitude': longitude,
                'radius_km': radius_km,
                'fuel_type': fuel_type
            }
        }), 200
        
    except Exception as e:
        print(f"Erro na busca de postos próximos: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500

@clean_gas_stations_bp.route('/cheapest', methods=['GET'])
def get_cheapest_fuel():
    """Busca combustível mais barato em uma região"""
    try:
        # Parâmetros de busca
        latitude = request.args.get('latitude', type=float)
        longitude = request.args.get('longitude', type=float)
        radius_km = request.args.get('radius', 50, type=float)
        fuel_type = request.args.get('fuel_type', 'gasoline')
        limit = request.args.get('limit', 10, type=int)
        
        if not latitude or not longitude:
            return jsonify({
                'success': False,
                'error': 'Latitude e longitude são obrigatórias'
            }), 400
        
        # Buscar postos próximos
        stations = CleanGasStation.query.filter_by(is_active=True).all()
        
        stations_with_price = []
        for station in stations:
            # Calcular distância
            distance = calculate_distance(
                latitude, longitude,
                float(station.latitude), float(station.longitude)
            )
            
            # Filtrar por raio
            if distance <= radius_km:
                fuel_price = station.get_fuel_price(fuel_type)
                
                if fuel_price:
                    station_data = station.to_dict()
                    station_data['distance_km'] = round(distance, 2)
                    station_data['fuel_price'] = fuel_price
                    stations_with_price.append(station_data)
        
        # Ordenar por preço (mais barato primeiro)
        stations_with_price.sort(key=lambda x: x['fuel_price'])
        
        # Limitar resultados
        cheapest_stations = stations_with_price[:limit]
        
        return jsonify({
            'success': True,
            'stations': cheapest_stations,
            'count': len(cheapest_stations),
            'search_params': {
                'latitude': latitude,
                'longitude': longitude,
                'radius_km': radius_km,
                'fuel_type': fuel_type,
                'limit': limit
            }
        }), 200
        
    except Exception as e:
        print(f"Erro na busca de combustível mais barato: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500

@clean_gas_stations_bp.route('/<station_id>', methods=['GET'])
def get_gas_station(station_id):
    """Obtém detalhes de um posto específico"""
    try:
        station = CleanGasStation.query.get(station_id)
        
        if not station:
            return jsonify({
                'success': False,
                'error': 'Posto não encontrado'
            }), 404
        
        return jsonify({
            'success': True,
            'station': station.to_dict()
        }), 200
        
    except Exception as e:
        print(f"Erro ao obter posto: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500

