from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.database import db
from src.models.user_profile import UserProfile, GPSTracking, Notification
from src.models.gas_station import GasStation
from datetime import datetime, timezone
import uuid

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/', methods=['GET'])
@jwt_required()
def get_profile():
    """Get user profile"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get user profile
        profile = UserProfile.find_by_user_id(current_user_id)
        if not profile:
            return jsonify({
                'success': False,
                'error': 'Perfil não encontrado'
            }), 404
        
        return jsonify({
            'success': True,
            'data': profile.to_dict()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get profile error: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro ao obter perfil'
        }), 500

@profile_bp.route('/', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user profile"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Get user profile
        profile = UserProfile.find_by_user_id(current_user_id)
        if not profile:
            return jsonify({
                'success': False,
                'error': 'Perfil não encontrado'
            }), 404
        
        # Update allowed fields
        allowed_fields = [
            'preferred_fuel_type', 'notification_enabled', 
            'notification_interval_km', 'notification_radius_km'
        ]
        
        for field in allowed_fields:
            if field in data:
                value = data[field]
                
                # Validate fuel type
                if field == 'preferred_fuel_type':
                    valid_types = ['gasoline', 'ethanol', 'gnv', 'diesel', 'diesel_s10']
                    if value not in valid_types:
                        return jsonify({
                            'success': False,
                            'error': f'Tipo de combustível inválido. Opções: {", ".join(valid_types)}'
                        }), 400
                
                # Validate numeric fields
                elif field in ['notification_interval_km', 'notification_radius_km']:
                    if not isinstance(value, (int, float)) or value <= 0:
                        return jsonify({
                            'success': False,
                            'error': f'{field} deve ser um número positivo'
                        }), 400
                
                # Validate boolean fields
                elif field == 'notification_enabled':
                    if not isinstance(value, bool):
                        return jsonify({
                            'success': False,
                            'error': f'{field} deve ser verdadeiro ou falso'
                        }), 400
                
                setattr(profile, field, value)
        
        profile.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Perfil atualizado com sucesso',
            'data': profile.to_dict()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Update profile error: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro ao atualizar perfil'
        }), 500

@profile_bp.route('/location', methods=['POST'])
@jwt_required()
def update_location():
    """Update user location and check for notifications"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        if not data.get('latitude') or not data.get('longitude'):
            return jsonify({
                'success': False,
                'error': 'Latitude e longitude são obrigatórias'
            }), 400
        
        latitude = float(data['latitude'])
        longitude = float(data['longitude'])
        accuracy = data.get('accuracy')
        speed = data.get('speed')
        heading = data.get('heading')
        trip_id = data.get('trip_id')
        
        # Validate coordinates
        if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
            return jsonify({
                'success': False,
                'error': 'Coordenadas inválidas'
            }), 400
        
        # Get user profile
        profile = UserProfile.find_by_user_id(current_user_id)
        if not profile:
            return jsonify({
                'success': False,
                'error': 'Perfil não encontrado'
            }), 404
        
        # Calculate distance from last location
        distance_from_last = 0.0
        if profile.last_latitude and profile.last_longitude:
            distance_from_last = UserProfile.calculate_distance(
                float(profile.last_latitude), float(profile.last_longitude),
                latitude, longitude
            )
        
        # Create GPS tracking record
        gps_record = GPSTracking(
            user_profile_id=profile.id,
            latitude=latitude,
            longitude=longitude,
            accuracy=accuracy,
            speed=speed,
            heading=heading,
            trip_id=trip_id,
            distance_from_last=distance_from_last
        )
        db.session.add(gps_record)
        
        # Update profile location
        profile.update_location(latitude, longitude)
        
        # Check if notification should be sent
        notification_sent = False
        recommended_station = None
        
        if profile.should_notify():
            # Find cheapest gas station nearby
            nearby_stations = GasStation.find_cheapest_nearby(
                latitude, longitude, 
                profile.preferred_fuel_type,
                profile.notification_radius_km,
                limit=1
            )
            
            if nearby_stations:
                station_data = nearby_stations[0]
                recommended_station = station_data
                
                # Create notification
                fuel_price = station_data.get('fuel_price', {})
                title = f"⛽ Posto mais barato encontrado!"
                message = (f"{station_data['name']} - {profile.get_fuel_type_display()}: "
                          f"R$ {fuel_price.get('price', 0):.2f}/L - "
                          f"Distância: {station_data['distance_km']:.1f}km")
                
                notification = Notification(
                    user_profile_id=profile.id,
                    title=title,
                    message=message,
                    notification_type='fuel_recommendation',
                    gas_station_id=station_data['id'],
                    fuel_price_id=fuel_price.get('id'),
                    user_latitude=latitude,
                    user_longitude=longitude
                )
                db.session.add(notification)
                
                # Mark notification as sent
                profile.mark_notification_sent()
                notification_sent = True
        
        db.session.commit()
        
        response_data = {
            'location_updated': True,
            'distance_traveled': float(profile.total_distance_km),
            'distance_until_next_notification': max(0, profile.notification_interval_km - 
                                                   (float(profile.total_distance_km) - float(profile.last_notification_km))),
            'notification_sent': notification_sent
        }
        
        if recommended_station:
            response_data['recommended_station'] = recommended_station
        
        return jsonify({
            'success': True,
            'message': 'Localização atualizada com sucesso',
            'data': response_data
        }), 200
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': f'Dados inválidos: {str(e)}'
        }), 400
    except Exception as e:
        current_app.logger.error(f"Update location error: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro ao atualizar localização'
        }), 500

@profile_bp.route('/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    """Get user notifications"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get user profile
        profile = UserProfile.find_by_user_id(current_user_id)
        if not profile:
            return jsonify({
                'success': False,
                'error': 'Perfil não encontrado'
            }), 404
        
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        
        # Build query
        query = Notification.query.filter_by(user_profile_id=profile.id)
        
        if unread_only:
            query = query.filter(Notification.read_at.is_(None))
        
        # Paginate
        notifications_paginated = query.order_by(Notification.sent_at.desc())\
                                      .paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'success': True,
            'data': {
                'notifications': [notif.to_dict() for notif in notifications_paginated.items],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': notifications_paginated.total,
                    'pages': notifications_paginated.pages,
                    'has_next': notifications_paginated.has_next,
                    'has_prev': notifications_paginated.has_prev
                }
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get notifications error: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro ao obter notificações'
        }), 500

@profile_bp.route('/notifications/<notification_id>/read', methods=['POST'])
@jwt_required()
def mark_notification_read(notification_id):
    """Mark notification as read"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get user profile
        profile = UserProfile.find_by_user_id(current_user_id)
        if not profile:
            return jsonify({
                'success': False,
                'error': 'Perfil não encontrado'
            }), 404
        
        # Get notification
        notification = Notification.query.filter_by(
            id=notification_id,
            user_profile_id=profile.id
        ).first()
        
        if not notification:
            return jsonify({
                'success': False,
                'error': 'Notificação não encontrada'
            }), 404
        
        # Mark as read
        notification.mark_as_read()
        
        return jsonify({
            'success': True,
            'message': 'Notificação marcada como lida',
            'data': notification.to_dict()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Mark notification read error: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro ao marcar notificação como lida'
        }), 500

@profile_bp.route('/notifications/<notification_id>/click', methods=['POST'])
@jwt_required()
def mark_notification_clicked(notification_id):
    """Mark notification as clicked"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get user profile
        profile = UserProfile.find_by_user_id(current_user_id)
        if not profile:
            return jsonify({
                'success': False,
                'error': 'Perfil não encontrado'
            }), 404
        
        # Get notification
        notification = Notification.query.filter_by(
            id=notification_id,
            user_profile_id=profile.id
        ).first()
        
        if not notification:
            return jsonify({
                'success': False,
                'error': 'Notificação não encontrada'
            }), 404
        
        # Mark as clicked
        notification.mark_as_clicked()
        
        return jsonify({
            'success': True,
            'message': 'Notificação marcada como clicada',
            'data': notification.to_dict()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Mark notification clicked error: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro ao marcar notificação como clicada'
        }), 500

@profile_bp.route('/gps-history', methods=['GET'])
@jwt_required()
def get_gps_history():
    """Get GPS tracking history"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get user profile
        profile = UserProfile.find_by_user_id(current_user_id)
        if not profile:
            return jsonify({
                'success': False,
                'error': 'Perfil não encontrado'
            }), 404
        
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 50)), 200)
        trip_id = request.args.get('trip_id')
        
        # Build query
        query = GPSTracking.query.filter_by(user_profile_id=profile.id)
        
        if trip_id:
            query = query.filter_by(trip_id=trip_id)
        
        # Paginate
        gps_paginated = query.order_by(GPSTracking.recorded_at.desc())\
                            .paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'success': True,
            'data': {
                'gps_history': [gps.to_dict() for gps in gps_paginated.items],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': gps_paginated.total,
                    'pages': gps_paginated.pages,
                    'has_next': gps_paginated.has_next,
                    'has_prev': gps_paginated.has_prev
                }
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get GPS history error: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro ao obter histórico GPS'
        }), 500

@profile_bp.route('/trips', methods=['GET'])
@jwt_required()
def get_trips():
    """Get user trips"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get user profile
        profile = UserProfile.find_by_user_id(current_user_id)
        if not profile:
            return jsonify({
                'success': False,
                'error': 'Perfil não encontrado'
            }), 404
        
        # Get distinct trip IDs with statistics
        trips_query = db.session.query(
            GPSTracking.trip_id,
            db.func.count(GPSTracking.id).label('points_count'),
            db.func.min(GPSTracking.recorded_at).label('start_time'),
            db.func.max(GPSTracking.recorded_at).label('end_time'),
            db.func.sum(GPSTracking.distance_from_last).label('total_distance')
        ).filter(
            GPSTracking.user_profile_id == profile.id,
            GPSTracking.trip_id.isnot(None)
        ).group_by(GPSTracking.trip_id).order_by(db.func.max(GPSTracking.recorded_at).desc())
        
        trips = trips_query.all()
        
        trips_data = []
        for trip in trips:
            trip_data = {
                'trip_id': trip.trip_id,
                'points_count': trip.points_count,
                'start_time': trip.start_time.isoformat() if trip.start_time else None,
                'end_time': trip.end_time.isoformat() if trip.end_time else None,
                'total_distance_km': float(trip.total_distance) if trip.total_distance else 0.0,
                'duration_minutes': None
            }
            
            # Calculate duration
            if trip.start_time and trip.end_time:
                duration = trip.end_time - trip.start_time
                trip_data['duration_minutes'] = int(duration.total_seconds() / 60)
            
            trips_data.append(trip_data)
        
        return jsonify({
            'success': True,
            'data': {
                'trips': trips_data,
                'total_trips': len(trips_data)
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get trips error: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro ao obter viagens'
        }), 500

@profile_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_user_stats():
    """Get user statistics"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get user profile
        profile = UserProfile.find_by_user_id(current_user_id)
        if not profile:
            return jsonify({
                'success': False,
                'error': 'Perfil não encontrado'
            }), 404
        
        # Get statistics
        total_notifications = Notification.query.filter_by(user_profile_id=profile.id).count()
        unread_notifications = Notification.query.filter_by(
            user_profile_id=profile.id
        ).filter(Notification.read_at.is_(None)).count()
        
        clicked_notifications = Notification.query.filter_by(
            user_profile_id=profile.id
        ).filter(Notification.clicked_at.isnot(None)).count()
        
        total_gps_points = GPSTracking.query.filter_by(user_profile_id=profile.id).count()
        
        unique_trips = db.session.query(GPSTracking.trip_id).filter(
            GPSTracking.user_profile_id == profile.id,
            GPSTracking.trip_id.isnot(None)
        ).distinct().count()
        
        return jsonify({
            'success': True,
            'data': {
                'profile': profile.to_dict(),
                'notifications': {
                    'total': total_notifications,
                    'unread': unread_notifications,
                    'clicked': clicked_notifications,
                    'click_rate': round((clicked_notifications / total_notifications * 100), 2) if total_notifications > 0 else 0
                },
                'tracking': {
                    'total_distance_km': float(profile.total_distance_km),
                    'total_gps_points': total_gps_points,
                    'unique_trips': unique_trips,
                    'last_location_update': profile.last_location_update.isoformat() if profile.last_location_update else None
                }
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get user stats error: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro ao obter estatísticas'
        }), 500

