from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.database import db
from src.models.simple_models import User, Trip, GPSPoint, Notification
import math
from datetime import datetime, timedelta
import random

gps_bp = Blueprint('gps', __name__)

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calcular distância entre dois pontos GPS usando fórmula de Haversine"""
    R = 6371  # Raio da Terra em km
    
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c

def find_cheapest_gas_station(latitude, longitude, fuel_type):
    """Simular busca do posto mais barato nas proximidades"""
    # Simulação de postos próximos
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
    
    # Retornar o mais barato
    cheapest = min(stations, key=lambda x: x['price'])
    return cheapest

@gps_bp.route('/start-trip', methods=['POST'])
@jwt_required()
def start_trip():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Verificar se já existe viagem ativa
        active_trip = Trip.query.filter_by(user_id=user_id, status='active').first()
        if active_trip:
            return jsonify({
                'success': False,
                'error': 'Já existe uma viagem ativa'
            }), 400
        
        # Criar nova viagem
        trip = Trip(
            user_id=user_id,
            origin_address=data.get('origin_address', 'Balneário Camboriú, SC'),
            destination_address=data.get('destination_address', 'São Paulo, SP'),
            fuel_type=data.get('fuel_type', 'gasoline'),
            notification_interval=data.get('notification_interval', 100),
            status='active',
            start_time=datetime.utcnow(),
            distance_traveled=0.0
        )
        
        db.session.add(trip)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'trip_id': trip.id,
            'message': f'Viagem iniciada! Notificações a cada {trip.notification_interval}km'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@gps_bp.route('/update-location', methods=['POST'])
@jwt_required()
def update_location():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Buscar viagem ativa
        trip = Trip.query.filter_by(user_id=user_id, status='active').first()
        if not trip:
            return jsonify({
                'success': False,
                'error': 'Nenhuma viagem ativa encontrada'
            }), 400
        
        latitude = float(data.get('latitude'))
        longitude = float(data.get('longitude'))
        accuracy = data.get('accuracy', 10)
        speed = data.get('speed', 0)
        
        # Buscar último ponto GPS
        last_point = GPSPoint.query.filter_by(trip_id=trip.id).order_by(GPSPoint.timestamp.desc()).first()
        
        # Calcular distância percorrida
        distance_increment = 0.0
        if last_point:
            distance_increment = calculate_distance(
                last_point.latitude, last_point.longitude,
                latitude, longitude
            )
        
        # Atualizar distância total da viagem
        trip.distance_traveled += distance_increment
        
        # Salvar novo ponto GPS
        gps_point = GPSPoint(
            trip_id=trip.id,
            latitude=latitude,
            longitude=longitude,
            accuracy=accuracy,
            speed=speed,
            timestamp=datetime.utcnow()
        )
        
        db.session.add(gps_point)
        
        # Verificar se deve enviar notificação
        notification_sent = False
        notification_message = None
        
        # Calcular quantas notificações já foram enviadas
        notifications_sent = Notification.query.filter_by(trip_id=trip.id).count()
        expected_notifications = int(trip.distance_traveled // trip.notification_interval)
        
        if expected_notifications > notifications_sent:
            # Buscar posto mais barato
            station = find_cheapest_gas_station(latitude, longitude, trip.fuel_type)
            
            # Criar notificação
            notification = Notification(
                trip_id=trip.id,
                user_id=user_id,
                title='⛽ Posto Mais Barato Encontrado!',
                message=f'{station["name"]} - R$ {station["price"]:.2f}/L - {station["distance"]:.1f}km de distância',
                station_name=station['name'],
                fuel_price=station['price'],
                coupon_code=station.get('coupon'),
                distance_traveled=trip.distance_traveled,
                timestamp=datetime.utcnow()
            )
            
            db.session.add(notification)
            notification_sent = True
            notification_message = f"⛽ {station['name']} - R$ {station['price']:.2f}/L"
            
            if station.get('coupon'):
                notification_message += f" | Cupom: {station['coupon']}"
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'distance_traveled': round(trip.distance_traveled, 2),
            'notification_sent': notification_sent,
            'notification_message': notification_message,
            'current_location': {
                'latitude': latitude,
                'longitude': longitude
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@gps_bp.route('/stop-trip', methods=['POST'])
@jwt_required()
def stop_trip():
    try:
        user_id = get_jwt_identity()
        
        # Buscar viagem ativa
        trip = Trip.query.filter_by(user_id=user_id, status='active').first()
        if not trip:
            return jsonify({
                'success': False,
                'error': 'Nenhuma viagem ativa encontrada'
            }), 400
        
        # Finalizar viagem
        trip.status = 'completed'
        trip.end_time = datetime.utcnow()
        
        # Calcular estatísticas
        duration = trip.end_time - trip.start_time
        notifications_count = Notification.query.filter_by(trip_id=trip.id).count()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'trip_summary': {
                'distance_traveled': round(trip.distance_traveled, 2),
                'duration_minutes': int(duration.total_seconds() / 60),
                'notifications_sent': notifications_count,
                'fuel_type': trip.fuel_type,
                'origin': trip.origin_address,
                'destination': trip.destination_address
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@gps_bp.route('/trip-status', methods=['GET'])
@jwt_required()
def get_trip_status():
    try:
        user_id = get_jwt_identity()
        
        # Buscar viagem ativa
        trip = Trip.query.filter_by(user_id=user_id, status='active').first()
        
        if trip:
            return jsonify({
                'success': True,
                'has_active_trip': True,
                'trip': {
                    'id': trip.id,
                    'origin': trip.origin_address,
                    'destination': trip.destination_address,
                    'fuel_type': trip.fuel_type,
                    'distance_traveled': round(trip.distance_traveled, 2),
                    'notification_interval': trip.notification_interval,
                    'start_time': trip.start_time.isoformat()
                }
            })
        else:
            return jsonify({
                'success': True,
                'has_active_trip': False
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@gps_bp.route('/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    try:
        user_id = get_jwt_identity()
        
        notifications = Notification.query.filter_by(user_id=user_id)\
            .order_by(Notification.timestamp.desc())\
            .limit(20).all()
        
        notifications_data = []
        for notif in notifications:
            notifications_data.append({
                'id': notif.id,
                'title': notif.title,
                'message': notif.message,
                'station_name': notif.station_name,
                'fuel_price': notif.fuel_price,
                'coupon_code': notif.coupon_code,
                'distance_traveled': notif.distance_traveled,
                'timestamp': notif.timestamp.isoformat(),
                'read': notif.read
            })
        
        return jsonify({
            'success': True,
            'notifications': notifications_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

