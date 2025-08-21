from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.database import db
from src.models.simple_models import User, Trip, GasStation, FuelPrice, Notification
from src.services.maps_service import GoogleMapsService
import math
from datetime import datetime, timedelta
import json

notifications_bp = Blueprint('notifications_advanced', __name__)

class NotificationService:
    def __init__(self):
        self.maps_service = GoogleMapsService()
    
    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calcular distância entre dois pontos usando fórmula de Haversine"""
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
    
    def find_cheapest_gas_station(self, current_lat, current_lng, fuel_type, max_radius=50):
        """Encontrar posto mais barato em um raio específico"""
        try:
            # Buscar todos os postos no raio
            gas_stations = GasStation.query.all()
            nearby_stations = []
            
            for station in gas_stations:
                distance = self.calculate_distance(
                    current_lat, current_lng,
                    float(station.latitude), float(station.longitude)
                )
                
                if distance <= max_radius:
                    # Buscar preço do combustível
                    fuel_price = FuelPrice.query.filter_by(
                        gas_station_id=station.id,
                        fuel_type=fuel_type
                    ).first()
                    
                    if fuel_price:
                        nearby_stations.append({
                            'station': station,
                            'price': fuel_price.price,
                            'distance': distance,
                            'fuel_price_id': fuel_price.id
                        })
            
            if not nearby_stations:
                return None
            
            # Ordenar por preço (mais barato primeiro)
            nearby_stations.sort(key=lambda x: x['price'])
            cheapest = nearby_stations[0]
            
            return {
                'station_id': cheapest['station'].id,
                'station_name': cheapest['station'].name,
                'station_brand': cheapest['station'].brand,
                'station_address': cheapest['station'].address,
                'fuel_type': fuel_type,
                'price': cheapest['price'],
                'distance': round(cheapest['distance'], 2),
                'latitude': cheapest['station'].latitude,
                'longitude': cheapest['station'].longitude,
                'fuel_price_id': cheapest['fuel_price_id']
            }
            
        except Exception as e:
            print(f"Erro ao buscar posto mais barato: {e}")
            return None
    
    def should_send_notification(self, user_id, trip_id, distance_traveled, notification_interval):
        """Verificar se deve enviar notificação baseado na distância"""
        try:
            # Verificar última notificação enviada
            last_notification = Notification.query.filter_by(
                user_id=user_id,
                trip_id=trip_id
            ).order_by(Notification.created_at.desc()).first()
            
            if not last_notification:
                # Primeira notificação - enviar quando atingir o intervalo
                return distance_traveled >= notification_interval
            
            # Calcular distância desde última notificação
            distance_since_last = distance_traveled - last_notification.distance_at_notification
            
            return distance_since_last >= notification_interval
            
        except Exception as e:
            print(f"Erro ao verificar notificação: {e}")
            return False
    
    def create_notification(self, user_id, trip_id, station_data, distance_traveled):
        """Criar notificação no banco de dados"""
        try:
            notification = Notification(
                user_id=user_id,
                trip_id=trip_id,
                gas_station_id=station_data['station_id'],
                fuel_price_id=station_data['fuel_price_id'],
                message=f"⛽ Posto mais barato encontrado!\n{station_data['station_name']} - R$ {station_data['price']:.2f}/L\nDistância: {station_data['distance']}km",
                notification_type='fuel_recommendation',
                distance_at_notification=distance_traveled,
                is_read=False,
                is_clicked=False
            )
            
            db.session.add(notification)
            db.session.commit()
            
            return notification
            
        except Exception as e:
            print(f"Erro ao criar notificação: {e}")
            db.session.rollback()
            return None

notification_service = NotificationService()

@notifications_bp.route('/check-notification', methods=['POST'])
@jwt_required()
def check_notification():
    """Verificar se deve enviar notificação baseado na localização atual"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validar dados recebidos
        required_fields = ['trip_id', 'current_latitude', 'current_longitude', 'distance_traveled']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo {field} é obrigatório'}), 400
        
        trip_id = data['trip_id']
        current_lat = float(data['current_latitude'])
        current_lng = float(data['current_longitude'])
        distance_traveled = float(data['distance_traveled'])
        
        # Buscar dados da viagem
        trip = Trip.query.filter_by(id=trip_id, user_id=user_id).first()
        if not trip:
            return jsonify({'error': 'Viagem não encontrada'}), 404
        
        # Buscar dados do usuário
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        # Verificar se deve enviar notificação
        should_notify = notification_service.should_send_notification(
            user_id, trip_id, distance_traveled, user.notification_interval_km
        )
        
        response_data = {
            'should_notify': should_notify,
            'distance_traveled': distance_traveled,
            'notification_interval': user.notification_interval_km,
            'fuel_type': user.preferred_fuel_type
        }
        
        if should_notify:
            # Buscar posto mais barato
            station_data = notification_service.find_cheapest_gas_station(
                current_lat, current_lng, user.preferred_fuel_type
            )
            
            if station_data:
                # Criar notificação
                notification = notification_service.create_notification(
                    user_id, trip_id, station_data, distance_traveled
                )
                
                if notification:
                    response_data.update({
                        'notification_sent': True,
                        'notification_id': notification.id,
                        'station_data': station_data,
                        'message': notification.message
                    })
                else:
                    response_data['notification_sent'] = False
                    response_data['error'] = 'Erro ao criar notificação'
            else:
                response_data.update({
                    'notification_sent': False,
                    'error': 'Nenhum posto encontrado na região'
                })
        
        return jsonify(response_data), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@notifications_bp.route('/user-notifications', methods=['GET'])
@jwt_required()
def get_user_notifications():
    """Obter todas as notificações do usuário"""
    try:
        user_id = get_jwt_identity()
        
        notifications = Notification.query.filter_by(user_id=user_id)\
            .order_by(Notification.created_at.desc()).all()
        
        notifications_data = []
        for notification in notifications:
            station = GasStation.query.get(notification.gas_station_id)
            fuel_price = FuelPrice.query.get(notification.fuel_price_id)
            
            notifications_data.append({
                'id': notification.id,
                'message': notification.message,
                'notification_type': notification.notification_type,
                'distance_at_notification': notification.distance_at_notification,
                'is_read': notification.is_read,
                'is_clicked': notification.is_clicked,
                'created_at': notification.created_at.isoformat(),
                'station': {
                    'name': station.name if station else None,
                    'brand': station.brand if station else None,
                    'address': station.address if station else None
                },
                'fuel_price': fuel_price.price if fuel_price else None
            })
        
        return jsonify({
            'notifications': notifications_data,
            'total': len(notifications_data)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@notifications_bp.route('/mark-read/<int:notification_id>', methods=['POST'])
@jwt_required()
def mark_notification_read(notification_id):
    """Marcar notificação como lida"""
    try:
        user_id = get_jwt_identity()
        
        notification = Notification.query.filter_by(
            id=notification_id, user_id=user_id
        ).first()
        
        if not notification:
            return jsonify({'error': 'Notificação não encontrada'}), 404
        
        notification.is_read = True
        notification.read_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'message': 'Notificação marcada como lida'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@notifications_bp.route('/mark-clicked/<int:notification_id>', methods=['POST'])
@jwt_required()
def mark_notification_clicked(notification_id):
    """Marcar notificação como clicada"""
    try:
        user_id = get_jwt_identity()
        
        notification = Notification.query.filter_by(
            id=notification_id, user_id=user_id
        ).first()
        
        if not notification:
            return jsonify({'error': 'Notificação não encontrada'}), 404
        
        notification.is_clicked = True
        notification.clicked_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'message': 'Notificação marcada como clicada'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@notifications_bp.route('/notification-stats', methods=['GET'])
@jwt_required()
def get_notification_stats():
    """Obter estatísticas das notificações do usuário"""
    try:
        user_id = get_jwt_identity()
        
        total_notifications = Notification.query.filter_by(user_id=user_id).count()
        read_notifications = Notification.query.filter_by(user_id=user_id, is_read=True).count()
        clicked_notifications = Notification.query.filter_by(user_id=user_id, is_clicked=True).count()
        
        recent_notifications = Notification.query.filter_by(user_id=user_id)\
            .filter(Notification.created_at >= datetime.utcnow() - timedelta(days=7))\
            .count()
        
        return jsonify({
            'total_notifications': total_notifications,
            'read_notifications': read_notifications,
            'clicked_notifications': clicked_notifications,
            'recent_notifications': recent_notifications,
            'read_rate': round((read_notifications / total_notifications * 100) if total_notifications > 0 else 0, 2),
            'click_rate': round((clicked_notifications / total_notifications * 100) if total_notifications > 0 else 0, 2)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

