from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.database import db
from src.models.user_profile import UserProfile
from src.models.gas_station import GasStation, FuelPrice
from src.models.gps_tracking import GPSTracking, Notification
from src.models.coupon import Coupon
import math
from datetime import datetime, timezone
import uuid

gps_bp = Blueprint('gps', __name__)

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

@gps_bp.route('/start-trip', methods=['POST'])
@jwt_required()
def start_trip():
    """Inicia uma nova viagem com rastreamento GPS"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validar dados obrigatórios
        required_fields = ['latitude', 'longitude']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Campo {field} é obrigatório'}), 400
        
        # Criar novo trip_id
        trip_id = str(uuid.uuid4())
        
        # Registrar ponto inicial
        gps_point = GPSTracking(
            user_id=user_id,
            trip_id=trip_id,
            latitude=float(data['latitude']),
            longitude=float(data['longitude']),
            accuracy=data.get('accuracy', 10.0),
            speed=data.get('speed', 0.0),
            heading=data.get('heading', 0.0),
            is_trip_start=True
        )
        
        db.session.add(gps_point)
        
        # Atualizar perfil do usuário
        profile = UserProfile.query.filter_by(user_id=user_id).first()
        if profile:
            profile.last_latitude = float(data['latitude'])
            profile.last_longitude = float(data['longitude'])
            profile.last_location_update = datetime.now(timezone.utc)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'trip_id': trip_id,
            'message': 'Viagem iniciada com sucesso'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Erro interno do servidor'}), 500

@gps_bp.route('/update-location', methods=['POST'])
@jwt_required()
def update_location():
    """Atualiza localização GPS e verifica se deve enviar notificações"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validar dados obrigatórios
        required_fields = ['latitude', 'longitude', 'trip_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Campo {field} é obrigatório'}), 400
        
        # Registrar novo ponto GPS
        gps_point = GPSTracking(
            user_id=user_id,
            trip_id=data['trip_id'],
            latitude=float(data['latitude']),
            longitude=float(data['longitude']),
            accuracy=data.get('accuracy', 10.0),
            speed=data.get('speed', 0.0),
            heading=data.get('heading', 0.0)
        )
        
        db.session.add(gps_point)
        
        # Obter perfil do usuário
        profile = UserProfile.query.filter_by(user_id=user_id).first()
        if not profile:
            return jsonify({'success': False, 'error': 'Perfil não encontrado'}), 404
        
        # Calcular distância percorrida desde última localização
        if profile.last_latitude and profile.last_longitude:
            distance = calculate_distance(
                profile.last_latitude, profile.last_longitude,
                float(data['latitude']), float(data['longitude'])
            )
            profile.total_distance_traveled += distance
        
        # Atualizar localização atual
        profile.last_latitude = float(data['latitude'])
        profile.last_longitude = float(data['longitude'])
        profile.last_location_update = datetime.now(timezone.utc)
        
        # Verificar se deve enviar notificação
        notification_sent = False
        if profile.should_notify():
            # Buscar posto mais barato nas proximidades
            nearby_stations = find_nearby_gas_stations(
                float(data['latitude']), 
                float(data['longitude']),
                profile.preferred_fuel,
                radius_km=50
            )
            
            if nearby_stations:
                best_station = nearby_stations[0]  # Já ordenado por preço
                
                # Criar notificação
                notification = Notification(
                    user_id=user_id,
                    gas_station_id=best_station['id'],
                    fuel_type=profile.preferred_fuel,
                    price=best_station['price'],
                    distance_km=best_station['distance'],
                    message=f"🚨 Posto mais barato: {best_station['name']} - {profile.preferred_fuel.title()} R$ {best_station['price']:.2f} ({best_station['distance']:.1f}km)",
                    latitude=float(data['latitude']),
                    longitude=float(data['longitude'])
                )
                
                db.session.add(notification)
                
                # Reset contador de distância
                profile.distance_since_last_notification = 0
                notification_sent = True
        
        db.session.commit()
        
        response_data = {
            'success': True,
            'distance_traveled': profile.total_distance_traveled,
            'distance_since_notification': profile.distance_since_last_notification,
            'notification_sent': notification_sent
        }
        
        if notification_sent:
            response_data['notification'] = {
                'message': notification.message,
                'station_name': best_station['name'],
                'fuel_price': best_station['price'],
                'distance_km': best_station['distance']
            }
        
        return jsonify(response_data)
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Erro interno do servidor'}), 500

@gps_bp.route('/stop-trip', methods=['POST'])
@jwt_required()
def stop_trip():
    """Finaliza viagem atual"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        required_fields = ['latitude', 'longitude', 'trip_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Campo {field} é obrigatório'}), 400
        
        # Registrar ponto final
        gps_point = GPSTracking(
            user_id=user_id,
            trip_id=data['trip_id'],
            latitude=float(data['latitude']),
            longitude=float(data['longitude']),
            accuracy=data.get('accuracy', 10.0),
            speed=data.get('speed', 0.0),
            heading=data.get('heading', 0.0),
            is_trip_end=True
        )
        
        db.session.add(gps_point)
        
        # Calcular estatísticas da viagem
        trip_points = GPSTracking.query.filter_by(
            user_id=user_id, 
            trip_id=data['trip_id']
        ).order_by(GPSTracking.timestamp).all()
        
        total_distance = 0
        if len(trip_points) > 1:
            for i in range(1, len(trip_points)):
                prev_point = trip_points[i-1]
                curr_point = trip_points[i]
                distance = calculate_distance(
                    prev_point.latitude, prev_point.longitude,
                    curr_point.latitude, curr_point.longitude
                )
                total_distance += distance
        
        trip_duration = (trip_points[-1].timestamp - trip_points[0].timestamp).total_seconds() / 3600  # em horas
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'trip_stats': {
                'total_distance_km': round(total_distance, 2),
                'duration_hours': round(trip_duration, 2),
                'points_recorded': len(trip_points),
                'average_speed_kmh': round(total_distance / trip_duration, 2) if trip_duration > 0 else 0
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Erro interno do servidor'}), 500

@gps_bp.route('/trip-history', methods=['GET'])
@jwt_required()
def get_trip_history():
    """Obtém histórico de viagens do usuário"""
    try:
        user_id = get_jwt_identity()
        
        # Buscar todas as viagens
        trips = db.session.query(GPSTracking.trip_id).filter_by(user_id=user_id).distinct().all()
        
        trip_list = []
        for trip in trips:
            trip_id = trip[0]
            
            # Obter pontos da viagem
            points = GPSTracking.query.filter_by(
                user_id=user_id, 
                trip_id=trip_id
            ).order_by(GPSTracking.timestamp).all()
            
            if len(points) >= 2:
                start_point = points[0]
                end_point = points[-1]
                
                # Calcular distância total
                total_distance = 0
                for i in range(1, len(points)):
                    prev_point = points[i-1]
                    curr_point = points[i]
                    distance = calculate_distance(
                        prev_point.latitude, prev_point.longitude,
                        curr_point.latitude, curr_point.longitude
                    )
                    total_distance += distance
                
                duration = (end_point.timestamp - start_point.timestamp).total_seconds() / 3600
                
                trip_list.append({
                    'trip_id': trip_id,
                    'start_time': start_point.timestamp.isoformat(),
                    'end_time': end_point.timestamp.isoformat(),
                    'start_location': {
                        'latitude': start_point.latitude,
                        'longitude': start_point.longitude
                    },
                    'end_location': {
                        'latitude': end_point.latitude,
                        'longitude': end_point.longitude
                    },
                    'total_distance_km': round(total_distance, 2),
                    'duration_hours': round(duration, 2),
                    'points_count': len(points)
                })
        
        return jsonify({
            'success': True,
            'trips': sorted(trip_list, key=lambda x: x['start_time'], reverse=True)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': 'Erro interno do servidor'}), 500

@gps_bp.route('/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    """Obtém notificações do usuário"""
    try:
        user_id = get_jwt_identity()
        
        notifications = Notification.query.filter_by(user_id=user_id).order_by(
            Notification.created_at.desc()
        ).limit(50).all()
        
        notification_list = []
        for notif in notifications:
            # Buscar informações do posto
            station = GasStation.query.get(notif.gas_station_id)
            
            notification_data = {
                'id': notif.id,
                'message': notif.message,
                'fuel_type': notif.fuel_type,
                'price': notif.price,
                'distance_km': notif.distance_km,
                'is_read': notif.is_read,
                'is_clicked': notif.is_clicked,
                'created_at': notif.created_at.isoformat(),
                'station': {
                    'id': station.id,
                    'name': station.name,
                    'brand': station.brand,
                    'address': station.address,
                    'latitude': station.latitude,
                    'longitude': station.longitude
                } if station else None
            }
            
            # Verificar se há cupom disponível
            coupon = Coupon.query.filter_by(
                gas_station_id=notif.gas_station_id,
                fuel_type=notif.fuel_type,
                is_active=True
            ).first()
            
            if coupon and coupon.is_valid():
                notification_data['coupon'] = {
                    'id': coupon.id,
                    'discount_type': coupon.discount_type,
                    'discount_value': coupon.discount_value,
                    'description': coupon.description,
                    'valid_until': coupon.valid_until.isoformat() if coupon.valid_until else None
                }
            
            notification_list.append(notification_data)
        
        return jsonify({
            'success': True,
            'notifications': notification_list
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': 'Erro interno do servidor'}), 500

@gps_bp.route('/notifications/<notification_id>/read', methods=['POST'])
@jwt_required()
def mark_notification_read(notification_id):
    """Marca notificação como lida"""
    try:
        user_id = get_jwt_identity()
        
        notification = Notification.query.filter_by(
            id=notification_id, 
            user_id=user_id
        ).first()
        
        if not notification:
            return jsonify({'success': False, 'error': 'Notificação não encontrada'}), 404
        
        notification.is_read = True
        notification.read_at = datetime.now(timezone.utc)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Notificação marcada como lida'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Erro interno do servidor'}), 500

def find_nearby_gas_stations(latitude, longitude, fuel_type, radius_km=50):
    """Busca postos de combustível próximos ordenados por preço"""
    try:
        # Buscar todos os postos com preços do combustível especificado
        stations_query = db.session.query(
            GasStation, FuelPrice
        ).join(
            FuelPrice, GasStation.id == FuelPrice.gas_station_id
        ).filter(
            FuelPrice.fuel_type == fuel_type
        ).all()
        
        nearby_stations = []
        
        for station, fuel_price in stations_query:
            # Calcular distância
            distance = calculate_distance(
                latitude, longitude,
                station.latitude, station.longitude
            )
            
            # Filtrar por raio
            if distance <= radius_km:
                nearby_stations.append({
                    'id': station.id,
                    'name': station.name,
                    'brand': station.brand,
                    'address': station.address,
                    'latitude': station.latitude,
                    'longitude': station.longitude,
                    'price': fuel_price.price,
                    'distance': distance,
                    'fuel_type': fuel_type
                })
        
        # Ordenar por preço (mais barato primeiro)
        nearby_stations.sort(key=lambda x: x['price'])
        
        return nearby_stations
        
    except Exception as e:
        return []

