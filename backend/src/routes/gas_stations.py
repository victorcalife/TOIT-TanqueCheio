from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.database import db
from src.models.gas_station import GasStation, FuelPrice, Coupon
from src.models.user_profile import UserProfile
from src.services.google_maps import google_maps_service
from src.services.fuel_scraper import fuel_scraper
from datetime import datetime, timezone, timedelta
import uuid

gas_stations_bp = Blueprint('gas_stations', __name__)

@gas_stations_bp.route('/', methods=['GET'])
def get_gas_stations():
    """Get gas stations with optional filtering"""
    try:
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        city = request.args.get('city')
        state = request.args.get('state')
        brand = request.args.get('brand')
        fuel_type = request.args.get('fuel_type')
        latitude = request.args.get('latitude', type=float)
        longitude = request.args.get('longitude', type=float)
        radius_km = request.args.get('radius_km', type=float, default=50)
        
        # Build query
        query = GasStation.query.filter_by(is_active=True)
        
        if city:
            query = query.filter(GasStation.city.ilike(f'%{city}%'))
        
        if state:
            query = query.filter_by(state=state.upper())
        
        if brand:
            query = query.filter(GasStation.brand.ilike(f'%{brand}%'))
        
        # Location-based filtering
        if latitude and longitude:
            # Use Google Maps service to find nearby stations
            nearby_stations = GasStation.find_nearby(
                latitude, longitude, radius_km, fuel_type, per_page * 2
            )
            
            # Convert to station objects for pagination
            station_ids = [station['id'] for station in nearby_stations]
            query = query.filter(GasStation.id.in_(station_ids))
        
        # Paginate
        stations_paginated = query.order_by(GasStation.name)\
                                 .paginate(page=page, per_page=per_page, error_out=False)
        
        # Include prices and coupons
        stations_data = []
        for station in stations_paginated.items:
            station_dict = station.to_dict(include_prices=True, include_coupons=True)
            
            # Add distance if location provided
            if latitude and longitude:
                station_dict['distance_km'] = round(
                    station.calculate_distance_to(latitude, longitude), 2
                )
            
            stations_data.append(station_dict)
        
        return jsonify({
            'success': True,
            'data': {
                'gas_stations': stations_data,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': stations_paginated.total,
                    'pages': stations_paginated.pages,
                    'has_next': stations_paginated.has_next,
                    'has_prev': stations_paginated.has_prev
                }
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get gas stations error: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro ao obter postos de combustível'
        }), 500

@gas_stations_bp.route('/<station_id>', methods=['GET'])
def get_gas_station(station_id):
    """Get specific gas station details"""
    try:
        station = GasStation.query.get(station_id)
        if not station:
            return jsonify({
                'success': False,
                'error': 'Posto não encontrado'
            }), 404
        
        # Get additional details from Google Maps if available
        google_details = None
        if google_maps_service.is_configured() and hasattr(station, 'google_place_id'):
            google_details = google_maps_service.get_place_details(station.google_place_id)
        
        station_data = station.to_dict(include_prices=True, include_coupons=True)
        
        if google_details:
            station_data['google_details'] = google_details
        
        return jsonify({
            'success': True,
            'data': station_data
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get gas station error: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro ao obter detalhes do posto'
        }), 500

@gas_stations_bp.route('/nearby', methods=['GET'])
def get_nearby_stations():
    """Get gas stations near a location"""
    try:
        # Get required parameters
        latitude = request.args.get('latitude', type=float)
        longitude = request.args.get('longitude', type=float)
        
        if not latitude or not longitude:
            return jsonify({
                'success': False,
                'error': 'Latitude e longitude são obrigatórias'
            }), 400
        
        # Get optional parameters
        radius_km = request.args.get('radius_km', type=float, default=10)
        fuel_type = request.args.get('fuel_type')
        limit = min(int(request.args.get('limit', 20)), 50)
        include_google_data = request.args.get('include_google_data', 'false').lower() == 'true'
        
        # Find nearby stations in database
        nearby_stations = GasStation.find_nearby(latitude, longitude, radius_km, fuel_type, limit)
        
        # Optionally include Google Maps data
        if include_google_data and google_maps_service.is_configured():
            google_stations = google_maps_service.find_gas_stations_nearby(
                latitude, longitude, int(radius_km * 1000)
            )
            
            # Merge Google data with database stations
            for station in nearby_stations:
                # Try to match with Google Places data
                for google_station in google_stations:
                    if (abs(station['latitude'] - google_station['latitude']) < 0.001 and
                        abs(station['longitude'] - google_station['longitude']) < 0.001):
                        station['google_data'] = google_station
                        break
        
        return jsonify({
            'success': True,
            'data': {
                'stations': nearby_stations,
                'search_center': {
                    'latitude': latitude,
                    'longitude': longitude
                },
                'radius_km': radius_km,
                'total_found': len(nearby_stations)
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get nearby stations error: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro ao buscar postos próximos'
        }), 500

@gas_stations_bp.route('/cheapest', methods=['GET'])
def get_cheapest_stations():
    """Get cheapest gas stations for fuel type"""
    try:
        # Get required parameters
        fuel_type = request.args.get('fuel_type')
        if not fuel_type:
            return jsonify({
                'success': False,
                'error': 'Tipo de combustível é obrigatório'
            }), 400
        
        # Validate fuel type
        valid_types = ['gasoline', 'ethanol', 'gnv', 'diesel', 'diesel_s10']
        if fuel_type not in valid_types:
            return jsonify({
                'success': False,
                'error': f'Tipo de combustível inválido. Opções: {", ".join(valid_types)}'
            }), 400
        
        # Get optional parameters
        latitude = request.args.get('latitude', type=float)
        longitude = request.args.get('longitude', type=float)
        radius_km = request.args.get('radius_km', type=float, default=50)
        limit = min(int(request.args.get('limit', 10)), 20)
        
        if latitude and longitude:
            # Find cheapest nearby stations
            cheapest_stations = GasStation.find_cheapest_nearby(
                latitude, longitude, fuel_type, radius_km, limit
            )
        else:
            # Find cheapest stations globally
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)
            
            cheapest_prices = db.session.query(FuelPrice)\
                .join(GasStation)\
                .filter(
                    FuelPrice.fuel_type == fuel_type,
                    FuelPrice.is_active == True,
                    FuelPrice.reported_at > cutoff_date,
                    GasStation.is_active == True
                )\
                .order_by(FuelPrice.price.asc())\
                .limit(limit).all()
            
            cheapest_stations = []
            for price in cheapest_prices:
                station_data = price.gas_station.to_dict()
                station_data['fuel_price'] = price.to_dict()
                station_data['price_per_liter'] = float(price.price)
                cheapest_stations.append(station_data)
        
        return jsonify({
            'success': True,
            'data': {
                'stations': cheapest_stations,
                'fuel_type': fuel_type,
                'search_params': {
                    'latitude': latitude,
                    'longitude': longitude,
                    'radius_km': radius_km if latitude and longitude else None
                },
                'total_found': len(cheapest_stations)
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get cheapest stations error: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro ao buscar postos mais baratos'
        }), 500

@gas_stations_bp.route('/along-route', methods=['POST'])
@jwt_required()
def get_stations_along_route():
    """Get gas stations along a route"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        origin = data.get('origin')
        destination = data.get('destination')
        
        if not origin or not destination:
            return jsonify({
                'success': False,
                'error': 'Origem e destino são obrigatórios'
            }), 400
        
        # Extract coordinates
        origin_coords = (origin.get('latitude'), origin.get('longitude'))
        dest_coords = (destination.get('latitude'), destination.get('longitude'))
        
        if not all(origin_coords) or not all(dest_coords):
            return jsonify({
                'success': False,
                'error': 'Coordenadas de origem e destino são obrigatórias'
            }), 400
        
        # Get user preferences
        profile = UserProfile.find_by_user_id(current_user_id)
        fuel_type = data.get('fuel_type', profile.preferred_fuel_type if profile else 'gasoline')
        search_radius = data.get('search_radius', 5000)  # 5km radius
        
        # Get route and stations using Google Maps
        stations_along_route = []
        route_info = None
        
        if google_maps_service.is_configured():
            # Get route information
            route_info = google_maps_service.get_directions(origin_coords, dest_coords)
            
            # Find stations along route
            google_stations = google_maps_service.find_gas_stations_along_route(
                origin_coords, dest_coords, search_radius
            )
            
            # Match with database stations and get prices
            for google_station in google_stations:
                # Try to find matching station in database
                db_station = GasStation.query.filter(
                    GasStation.latitude.between(
                        google_station['latitude'] - 0.001,
                        google_station['latitude'] + 0.001
                    ),
                    GasStation.longitude.between(
                        google_station['longitude'] - 0.001,
                        google_station['longitude'] + 0.001
                    ),
                    GasStation.is_active == True
                ).first()
                
                station_data = google_station.copy()
                
                if db_station:
                    # Use database data with prices
                    station_data.update(db_station.to_dict(include_prices=True, include_coupons=True))
                    
                    # Get specific fuel price
                    fuel_price = db_station.get_price_for_fuel(fuel_type)
                    if fuel_price:
                        station_data['current_fuel_price'] = fuel_price.to_dict()
                
                stations_along_route.append(station_data)
        
        else:
            # Fallback: use simple database search along route
            # Create waypoints along the route (simplified)
            stations_along_route = GasStation.find_nearby(
                (origin_coords[0] + dest_coords[0]) / 2,  # Midpoint
                (origin_coords[1] + dest_coords[1]) / 2,
                search_radius / 1000,  # Convert to km
                fuel_type,
                20
            )
        
        # Sort by position on route or distance
        if route_info:
            stations_along_route.sort(key=lambda x: x.get('position_on_route', 0))
        else:
            stations_along_route.sort(key=lambda x: x.get('distance_km', 0))
        
        return jsonify({
            'success': True,
            'data': {
                'route': route_info,
                'stations': stations_along_route,
                'fuel_type': fuel_type,
                'search_radius_meters': search_radius,
                'total_stations': len(stations_along_route)
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get stations along route error: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro ao buscar postos na rota'
        }), 500

@gas_stations_bp.route('/prices/update', methods=['POST'])
@jwt_required()
def update_fuel_prices():
    """Trigger fuel price update via scraping"""
    try:
        current_user_id = get_jwt_identity()
        
        # Check if user has permission (could be admin only)
        # For now, allow any authenticated user
        
        # Run scraping in background (in production, use Celery or similar)
        scraping_result = fuel_scraper.run_full_scraping_cycle()
        
        return jsonify({
            'success': True,
            'message': 'Atualização de preços iniciada',
            'data': scraping_result
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Update fuel prices error: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro ao atualizar preços'
        }), 500

@gas_stations_bp.route('/<station_id>/prices', methods=['GET'])
def get_station_prices(station_id):
    """Get price history for a gas station"""
    try:
        station = GasStation.query.get(station_id)
        if not station:
            return jsonify({
                'success': False,
                'error': 'Posto não encontrado'
            }), 404
        
        # Get query parameters
        fuel_type = request.args.get('fuel_type')
        days = int(request.args.get('days', 30))
        
        # Build query
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        query = FuelPrice.query.filter(
            FuelPrice.gas_station_id == station_id,
            FuelPrice.reported_at > cutoff_date
        )
        
        if fuel_type:
            query = query.filter_by(fuel_type=fuel_type)
        
        prices = query.order_by(FuelPrice.reported_at.desc()).all()
        
        return jsonify({
            'success': True,
            'data': {
                'station': station.to_dict(),
                'prices': [price.to_dict() for price in prices],
                'period_days': days,
                'fuel_type_filter': fuel_type
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get station prices error: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro ao obter histórico de preços'
        }), 500

@gas_stations_bp.route('/<station_id>/coupons', methods=['GET'])
def get_station_coupons(station_id):
    """Get active coupons for a gas station"""
    try:
        station = GasStation.query.get(station_id)
        if not station:
            return jsonify({
                'success': False,
                'error': 'Posto não encontrado'
            }), 404
        
        fuel_type = request.args.get('fuel_type')
        coupons = station.get_active_coupons(fuel_type)
        
        return jsonify({
            'success': True,
            'data': {
                'station': station.to_dict(),
                'coupons': [coupon.to_dict() for coupon in coupons],
                'fuel_type_filter': fuel_type
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get station coupons error: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro ao obter cupons'
        }), 500

