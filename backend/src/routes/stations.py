from flask import Blueprint, request, jsonify
from ..models.gas_station import GasStation, FuelPrice

stations_bp = Blueprint('stations_bp', __name__, url_prefix='/api')

@stations_bp.route('/gas-stations', methods=['GET'])
def get_gas_stations():
    try:
        stations = GasStation.query.filter_by(is_active=True).all()
        
        result = []
        for station in stations:
            fuel_prices = FuelPrice.query.filter_by(gas_station_id=station.id).all()
            
            prices = {}
            for price in fuel_prices:
                prices[price.fuel_type] = {
                    'price': price.price,
                    'last_updated': price.last_updated.isoformat() if price.last_updated else None
                }
            
            result.append({
                'id': station.id,
                'name': station.name,
                'brand': station.brand,
                'address': station.address,
                'latitude': station.latitude,
                'longitude': station.longitude,
                'fuel_prices': prices,
                'is_active': station.is_active
            })
        
        return jsonify({
            'success': True,
            'gas_stations': result,
            'total': len(result)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        }), 500

@stations_bp.route('/recommendations', methods=['POST'])
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
        
        # TODO: Isolar esta lógica em um serviço de recomendação
        fuel_prices = FuelPrice.query.filter_by(fuel_type=fuel_type).all()
        
        recommendations = []
        for fuel_price in fuel_prices:
            station = fuel_price.gas_station
            if not station.is_active:
                continue
            
            distance_from_route = abs(hash(station.name)) % 10 + 1  # Simulado
            savings_per_liter = max(0, 5.75 - fuel_price.price) # Simulado
            score = max(0, (savings_per_liter * 10) - (distance_from_route * 0.5))
            
            recommendations.append({
                'station': {
                    'id': station.id,
                    'name': station.name,
                    'brand': station.brand,
                    'address': station.address,
                },
                'fuel': {
                    'type': fuel_type,
                    'price': fuel_price.price,
                },
                'score': score,
                'estimated_savings': savings_per_liter * 50 # Simulado
            })
        
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        
        return jsonify({
            'success': True,
            'recommendations': recommendations[:5]
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        }), 500
