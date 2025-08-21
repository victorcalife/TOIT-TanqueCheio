import json
import requests
from datetime import datetime
import threading
import time
from typing import Dict, List, Optional

class PushNotificationService:
    """Serviço para envio de notificações push em tempo real"""
    
    def __init__(self):
        self.active_subscriptions = {}  # user_id -> subscription_data
        self.notification_queue = []
        self.is_running = False
        
    def subscribe_user(self, user_id: str, subscription_data: Dict):
        """Registrar usuário para receber notificações push"""
        self.active_subscriptions[user_id] = {
            'subscription': subscription_data,
            'created_at': datetime.utcnow(),
            'last_notification': None
        }
        print(f"📱 Usuário {user_id} inscrito para notificações push")
    
    def unsubscribe_user(self, user_id: str):
        """Cancelar inscrição de notificações push"""
        if user_id in self.active_subscriptions:
            del self.active_subscriptions[user_id]
            print(f"📱 Usuário {user_id} desinscrito das notificações push")
    
    def queue_notification(self, user_id: str, notification_data: Dict):
        """Adicionar notificação à fila de envio"""
        notification = {
            'user_id': user_id,
            'data': notification_data,
            'created_at': datetime.utcnow(),
            'attempts': 0,
            'max_attempts': 3
        }
        
        self.notification_queue.append(notification)
        print(f"🔔 Notificação adicionada à fila para usuário {user_id}")
    
    def send_fuel_notification(self, user_id: str, station_data: Dict, distance_traveled: float):
        """Enviar notificação específica de combustível"""
        notification_data = {
            'type': 'fuel_recommendation',
            'title': '⛽ Posto Mais Barato Encontrado!',
            'body': f'{station_data["station_name"]} - R$ {station_data["price"]:.2f}/L',
            'data': {
                'station_id': station_data.get('station_id'),
                'station_name': station_data['station_name'],
                'station_brand': station_data.get('station_brand', ''),
                'station_address': station_data.get('station_address', ''),
                'fuel_type': station_data.get('fuel_type'),
                'price': station_data['price'],
                'distance': station_data.get('distance', 0),
                'distance_traveled': distance_traveled,
                'coupon_code': station_data.get('coupon_code'),
                'latitude': station_data.get('latitude'),
                'longitude': station_data.get('longitude'),
                'timestamp': datetime.utcnow().isoformat()
            },
            'actions': [
                {
                    'action': 'view_station',
                    'title': 'Ver Posto',
                    'icon': '⛽'
                },
                {
                    'action': 'navigate',
                    'title': 'Navegar',
                    'icon': '🗺️'
                }
            ]
        }
        
        self.queue_notification(user_id, notification_data)
    
    def send_trip_notification(self, user_id: str, message: str, trip_data: Dict):
        """Enviar notificação relacionada à viagem"""
        notification_data = {
            'type': 'trip_update',
            'title': '🚗 Atualização da Viagem',
            'body': message,
            'data': {
                'trip_id': trip_data.get('trip_id'),
                'distance_traveled': trip_data.get('distance_traveled', 0),
                'fuel_type': trip_data.get('fuel_type'),
                'origin': trip_data.get('origin'),
                'destination': trip_data.get('destination'),
                'timestamp': datetime.utcnow().isoformat()
            }
        }
        
        self.queue_notification(user_id, notification_data)
    
    def process_notification_queue(self):
        """Processar fila de notificações em thread separada"""
        while self.is_running:
            if self.notification_queue:
                notification = self.notification_queue.pop(0)
                self._send_notification(notification)
            
            time.sleep(1)  # Verificar fila a cada segundo
    
    def _send_notification(self, notification: Dict):
        """Enviar notificação individual"""
        try:
            user_id = notification['user_id']
            
            if user_id not in self.active_subscriptions:
                print(f"⚠️ Usuário {user_id} não tem inscrição ativa")
                return False
            
            subscription = self.active_subscriptions[user_id]['subscription']
            
            # Simular envio de notificação push
            # Em produção, aqui seria integrado com Firebase, OneSignal, etc.
            print(f"📤 Enviando notificação push para {user_id}:")
            print(f"   📱 Título: {notification['data']['title']}")
            print(f"   💬 Mensagem: {notification['data']['body']}")
            
            if notification['data']['type'] == 'fuel_recommendation':
                station_data = notification['data']['data']
                print(f"   ⛽ Posto: {station_data['station_name']}")
                print(f"   💰 Preço: R$ {station_data['price']:.2f}/L")
                print(f"   📍 Distância: {station_data['distance']:.1f}km")
                
                if station_data.get('coupon_code'):
                    print(f"   🎟️ Cupom: {station_data['coupon_code']}")
            
            # Atualizar timestamp da última notificação
            self.active_subscriptions[user_id]['last_notification'] = datetime.utcnow()
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao enviar notificação: {e}")
            
            # Tentar novamente se não excedeu tentativas
            notification['attempts'] += 1
            if notification['attempts'] < notification['max_attempts']:
                print(f"🔄 Tentativa {notification['attempts']}/{notification['max_attempts']}")
                self.notification_queue.append(notification)
            
            return False
    
    def start_service(self):
        """Iniciar serviço de notificações"""
        if not self.is_running:
            self.is_running = True
            self.notification_thread = threading.Thread(target=self.process_notification_queue)
            self.notification_thread.daemon = True
            self.notification_thread.start()
            print("🚀 Serviço de notificações push iniciado")
    
    def stop_service(self):
        """Parar serviço de notificações"""
        self.is_running = False
        print("🛑 Serviço de notificações push parado")
    
    def get_user_stats(self, user_id: str) -> Optional[Dict]:
        """Obter estatísticas de notificações do usuário"""
        if user_id not in self.active_subscriptions:
            return None
        
        subscription = self.active_subscriptions[user_id]
        
        return {
            'subscribed_at': subscription['created_at'].isoformat(),
            'last_notification': subscription['last_notification'].isoformat() if subscription['last_notification'] else None,
            'is_active': True
        }
    
    def get_service_stats(self) -> Dict:
        """Obter estatísticas gerais do serviço"""
        return {
            'active_subscriptions': len(self.active_subscriptions),
            'queued_notifications': len(self.notification_queue),
            'service_running': self.is_running,
            'uptime': datetime.utcnow().isoformat()
        }

# Instância global do serviço
push_service = PushNotificationService()

class WebhookNotificationService:
    """Serviço para envio de notificações via webhook"""
    
    def __init__(self):
        self.webhook_urls = {}  # user_id -> webhook_url
    
    def register_webhook(self, user_id: str, webhook_url: str):
        """Registrar webhook para usuário"""
        self.webhook_urls[user_id] = webhook_url
        print(f"🔗 Webhook registrado para usuário {user_id}: {webhook_url}")
    
    def send_webhook_notification(self, user_id: str, notification_data: Dict):
        """Enviar notificação via webhook"""
        if user_id not in self.webhook_urls:
            return False
        
        webhook_url = self.webhook_urls[user_id]
        
        try:
            payload = {
                'user_id': user_id,
                'timestamp': datetime.utcnow().isoformat(),
                'notification': notification_data
            }
            
            response = requests.post(
                webhook_url,
                json=payload,
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                print(f"✅ Webhook enviado com sucesso para {user_id}")
                return True
            else:
                print(f"❌ Erro no webhook para {user_id}: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao enviar webhook para {user_id}: {e}")
            return False

# Instância global do serviço de webhook
webhook_service = WebhookNotificationService()

def send_fuel_alert(user_id: str, station_data: Dict, distance_traveled: float):
    """Função helper para enviar alerta de combustível"""
    # Enviar via push notification
    push_service.send_fuel_notification(user_id, station_data, distance_traveled)
    
    # Enviar via webhook se configurado
    webhook_service.send_webhook_notification(user_id, {
        'type': 'fuel_recommendation',
        'station_data': station_data,
        'distance_traveled': distance_traveled
    })

def send_trip_alert(user_id: str, message: str, trip_data: Dict):
    """Função helper para enviar alerta de viagem"""
    # Enviar via push notification
    push_service.send_trip_notification(user_id, message, trip_data)
    
    # Enviar via webhook se configurado
    webhook_service.send_webhook_notification(user_id, {
        'type': 'trip_update',
        'message': message,
        'trip_data': trip_data
    })

# Inicializar serviço automaticamente
push_service.start_service()

