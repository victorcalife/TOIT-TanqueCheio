from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.database import db
from src.models.user_profile import UserProfile
from src.models.gps_tracking import Notification
from src.models.gas_station import GasStation
from src.models.coupon import Coupon
from datetime import datetime, timezone
import json

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/send-test-notification', methods=['POST'])
@jwt_required()
def send_test_notification():
    """Envia notificação de teste para o usuário"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Buscar posto mais próximo para teste
        profile = UserProfile.query.filter_by(user_id=user_id).first()
        if not profile:
            return jsonify({'success': False, 'error': 'Perfil não encontrado'}), 404
        
        # Buscar primeiro posto disponível
        station = GasStation.query.first()
        if not station:
            return jsonify({'success': False, 'error': 'Nenhum posto encontrado'}), 404
        
        # Criar notificação de teste
        notification = Notification(
            user_id=user_id,
            gas_station_id=station.id,
            fuel_type=profile.preferred_fuel,
            price=5.89,
            distance_km=2.5,
            message=f"🚨 Teste: {station.name} - {profile.preferred_fuel.title()} R$ 5,89 (2.5km)",
            latitude=profile.last_latitude or -23.5505,
            longitude=profile.last_longitude or -46.6333
        )
        
        db.session.add(notification)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Notificação de teste enviada',
            'notification': {
                'id': notification.id,
                'message': notification.message,
                'station_name': station.name,
                'fuel_price': 5.89,
                'distance_km': 2.5
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Erro interno do servidor'}), 500

@notifications_bp.route('/settings', methods=['GET'])
@jwt_required()
def get_notification_settings():
    """Obtém configurações de notificação do usuário"""
    try:
        user_id = get_jwt_identity()
        
        profile = UserProfile.query.filter_by(user_id=user_id).first()
        if not profile:
            return jsonify({'success': False, 'error': 'Perfil não encontrado'}), 404
        
        return jsonify({
            'success': True,
            'settings': {
                'notifications_enabled': profile.notifications_enabled,
                'notification_interval_km': profile.notification_interval_km,
                'preferred_fuel': profile.preferred_fuel,
                'max_detour_km': profile.max_detour_km,
                'distance_since_last_notification': profile.distance_since_last_notification,
                'total_distance_traveled': profile.total_distance_traveled
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': 'Erro interno do servidor'}), 500

@notifications_bp.route('/settings', methods=['PUT'])
@jwt_required()
def update_notification_settings():
    """Atualiza configurações de notificação"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        profile = UserProfile.query.filter_by(user_id=user_id).first()
        if not profile:
            return jsonify({'success': False, 'error': 'Perfil não encontrado'}), 404
        
        # Atualizar configurações
        if 'notifications_enabled' in data:
            profile.notifications_enabled = bool(data['notifications_enabled'])
        
        if 'notification_interval_km' in data:
            interval = int(data['notification_interval_km'])
            if interval < 50 or interval > 500:
                return jsonify({'success': False, 'error': 'Intervalo deve ser entre 50 e 500 km'}), 400
            profile.notification_interval_km = interval
        
        if 'preferred_fuel' in data:
            fuel_types = ['gasoline', 'ethanol', 'diesel', 'diesel_s10', 'gnv']
            if data['preferred_fuel'] not in fuel_types:
                return jsonify({'success': False, 'error': 'Tipo de combustível inválido'}), 400
            profile.preferred_fuel = data['preferred_fuel']
        
        if 'max_detour_km' in data:
            detour = float(data['max_detour_km'])
            if detour < 1 or detour > 50:
                return jsonify({'success': False, 'error': 'Desvio máximo deve ser entre 1 e 50 km'}), 400
            profile.max_detour_km = detour
        
        profile.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Configurações atualizadas com sucesso',
            'settings': {
                'notifications_enabled': profile.notifications_enabled,
                'notification_interval_km': profile.notification_interval_km,
                'preferred_fuel': profile.preferred_fuel,
                'max_detour_km': profile.max_detour_km
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Erro interno do servidor'}), 500

@notifications_bp.route('/history', methods=['GET'])
@jwt_required()
def get_notification_history():
    """Obtém histórico completo de notificações"""
    try:
        user_id = get_jwt_identity()
        
        # Parâmetros de paginação
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Filtros
        fuel_type = request.args.get('fuel_type')
        is_read = request.args.get('is_read')
        
        query = Notification.query.filter_by(user_id=user_id)
        
        if fuel_type:
            query = query.filter_by(fuel_type=fuel_type)
        
        if is_read is not None:
            query = query.filter_by(is_read=is_read.lower() == 'true')
        
        notifications = query.order_by(
            Notification.created_at.desc()
        ).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        notification_list = []
        for notif in notifications.items:
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
                'read_at': notif.read_at.isoformat() if notif.read_at else None,
                'clicked_at': notif.clicked_at.isoformat() if notif.clicked_at else None,
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
                    'code': coupon.code,
                    'valid_until': coupon.valid_until.isoformat() if coupon.valid_until else None
                }
            
            notification_list.append(notification_data)
        
        return jsonify({
            'success': True,
            'notifications': notification_list,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': notifications.total,
                'pages': notifications.pages,
                'has_next': notifications.has_next,
                'has_prev': notifications.has_prev
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': 'Erro interno do servidor'}), 500

@notifications_bp.route('/<notification_id>/click', methods=['POST'])
@jwt_required()
def mark_notification_clicked(notification_id):
    """Marca notificação como clicada"""
    try:
        user_id = get_jwt_identity()
        
        notification = Notification.query.filter_by(
            id=notification_id, 
            user_id=user_id
        ).first()
        
        if not notification:
            return jsonify({'success': False, 'error': 'Notificação não encontrada'}), 404
        
        notification.is_clicked = True
        notification.clicked_at = datetime.now(timezone.utc)
        
        # Marcar como lida também se ainda não foi
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.now(timezone.utc)
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Notificação marcada como clicada'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Erro interno do servidor'}), 500

@notifications_bp.route('/mark-all-read', methods=['POST'])
@jwt_required()
def mark_all_notifications_read():
    """Marca todas as notificações como lidas"""
    try:
        user_id = get_jwt_identity()
        
        # Atualizar todas as notificações não lidas
        updated = Notification.query.filter_by(
            user_id=user_id, 
            is_read=False
        ).update({
            'is_read': True,
            'read_at': datetime.now(timezone.utc)
        })
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{updated} notificações marcadas como lidas'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Erro interno do servidor'}), 500

@notifications_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_notification_stats():
    """Obtém estatísticas de notificações do usuário"""
    try:
        user_id = get_jwt_identity()
        
        # Contar notificações por status
        total_notifications = Notification.query.filter_by(user_id=user_id).count()
        unread_notifications = Notification.query.filter_by(user_id=user_id, is_read=False).count()
        clicked_notifications = Notification.query.filter_by(user_id=user_id, is_clicked=True).count()
        
        # Estatísticas por tipo de combustível
        fuel_stats = db.session.query(
            Notification.fuel_type,
            db.func.count(Notification.id).label('count'),
            db.func.avg(Notification.price).label('avg_price'),
            db.func.min(Notification.price).label('min_price'),
            db.func.max(Notification.price).label('max_price')
        ).filter_by(user_id=user_id).group_by(Notification.fuel_type).all()
        
        fuel_statistics = {}
        for stat in fuel_stats:
            fuel_statistics[stat.fuel_type] = {
                'count': stat.count,
                'average_price': round(float(stat.avg_price), 2),
                'min_price': float(stat.min_price),
                'max_price': float(stat.max_price)
            }
        
        # Obter perfil para estatísticas de viagem
        profile = UserProfile.query.filter_by(user_id=user_id).first()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_notifications': total_notifications,
                'unread_notifications': unread_notifications,
                'clicked_notifications': clicked_notifications,
                'click_rate': round((clicked_notifications / total_notifications * 100), 2) if total_notifications > 0 else 0,
                'fuel_statistics': fuel_statistics,
                'travel_stats': {
                    'total_distance_km': profile.total_distance_traveled if profile else 0,
                    'distance_since_last_notification': profile.distance_since_last_notification if profile else 0,
                    'notification_interval_km': profile.notification_interval_km if profile else 100
                }
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': 'Erro interno do servidor'}), 500

