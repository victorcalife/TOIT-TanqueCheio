import asyncio
import websockets
import json
import threading
import time
from datetime import datetime
from typing import Dict, Set, Optional
import math
import uuid

class RealTimeGPSService:
    """Serviço de GPS em tempo real com WebSocket"""
    
    def __init__(self):
        self.active_connections: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.user_locations: Dict[str, Dict] = {}
        self.active_trips: Dict[str, Dict] = {}
        self.is_running = False
        self.server = None
        
    async def register_connection(self, websocket, user_id: str):
        """Registrar nova conexão WebSocket"""
        self.active_connections[user_id] = websocket
        print(f"📱 Usuário {user_id} conectado ao GPS em tempo real")
        
        # Enviar status inicial
        await self.send_to_user(user_id, {
            'type': 'connection_established',
            'message': 'GPS em tempo real conectado',
            'timestamp': datetime.utcnow().isoformat()
        })
    
    async def unregister_connection(self, user_id: str):
        """Remover conexão WebSocket"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            print(f"📱 Usuário {user_id} desconectado do GPS")
    
    async def send_to_user(self, user_id: str, data: Dict):
        """Enviar dados para usuário específico"""
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send(json.dumps(data))
                return True
            except websockets.exceptions.ConnectionClosed:
                await self.unregister_connection(user_id)
                return False
        return False
    
    async def broadcast_to_all(self, data: Dict):
        """Enviar dados para todos os usuários conectados"""
        if not self.active_connections:
            return
        
        disconnected_users = []
        for user_id, websocket in self.active_connections.items():
            try:
                await websocket.send(json.dumps(data))
            except websockets.exceptions.ConnectionClosed:
                disconnected_users.append(user_id)
        
        # Remover conexões fechadas
        for user_id in disconnected_users:
            await self.unregister_connection(user_id)
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calcular distância entre dois pontos GPS"""
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
    
    async def update_user_location(self, user_id: str, location_data: Dict):
        """Atualizar localização do usuário"""
        current_time = datetime.utcnow()
        
        # Armazenar localização atual
        previous_location = self.user_locations.get(user_id)
        
        self.user_locations[user_id] = {
            'latitude': location_data['latitude'],
            'longitude': location_data['longitude'],
            'accuracy': location_data.get('accuracy', 10),
            'speed': location_data.get('speed', 0),
            'timestamp': current_time.isoformat(),
            'heading': location_data.get('heading', 0)
        }
        
        # Calcular distância percorrida se há localização anterior
        distance_increment = 0.0
        if previous_location and user_id in self.active_trips:
            distance_increment = self.calculate_distance(
                previous_location['latitude'], previous_location['longitude'],
                location_data['latitude'], location_data['longitude']
            )
            
            # Atualizar distância total da viagem
            self.active_trips[user_id]['distance_traveled'] += distance_increment
        
        # Preparar dados para envio
        response_data = {
            'type': 'location_update',
            'location': self.user_locations[user_id],
            'distance_increment': round(distance_increment, 3),
            'trip_data': self.active_trips.get(user_id, {})
        }
        
        # Verificar se deve enviar notificação
        if user_id in self.active_trips:
            trip = self.active_trips[user_id]
            notification_check = await self.check_notification_needed(user_id, trip)
            
            if notification_check['should_notify']:
                response_data['notification'] = notification_check
        
        # Enviar atualização para o usuário
        await self.send_to_user(user_id, response_data)
        
        return response_data
    
    async def start_trip(self, user_id: str, trip_data: Dict):
        """Iniciar nova viagem"""
        trip_id = str(uuid.uuid4())
        
        self.active_trips[user_id] = {
            'trip_id': trip_id,
            'origin': trip_data.get('origin', ''),
            'destination': trip_data.get('destination', ''),
            'fuel_type': trip_data.get('fuel_type', 'gasoline'),
            'notification_interval': trip_data.get('notification_interval', 100),
            'distance_traveled': 0.0,
            'start_time': datetime.utcnow().isoformat(),
            'status': 'active',
            'last_notification_distance': 0.0
        }
        
        # Notificar usuário sobre início da viagem
        await self.send_to_user(user_id, {
            'type': 'trip_started',
            'trip': self.active_trips[user_id],
            'message': f'Viagem iniciada! Notificações a cada {trip_data.get("notification_interval", 100)}km'
        })
        
        return self.active_trips[user_id]
    
    async def stop_trip(self, user_id: str):
        """Finalizar viagem"""
        if user_id not in self.active_trips:
            return None
        
        trip = self.active_trips[user_id]
        trip['status'] = 'completed'
        trip['end_time'] = datetime.utcnow().isoformat()
        
        # Calcular estatísticas da viagem
        trip_summary = {
            'trip_id': trip['trip_id'],
            'distance_traveled': round(trip['distance_traveled'], 2),
            'duration': self.calculate_trip_duration(trip),
            'fuel_type': trip['fuel_type'],
            'origin': trip['origin'],
            'destination': trip['destination']
        }
        
        # Notificar usuário sobre fim da viagem
        await self.send_to_user(user_id, {
            'type': 'trip_completed',
            'trip_summary': trip_summary,
            'message': 'Viagem finalizada com sucesso!'
        })
        
        # Remover viagem ativa
        del self.active_trips[user_id]
        
        return trip_summary
    
    def calculate_trip_duration(self, trip: Dict) -> str:
        """Calcular duração da viagem"""
        try:
            start_time = datetime.fromisoformat(trip['start_time'].replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(trip['end_time'].replace('Z', '+00:00'))
            duration = end_time - start_time
            
            hours = duration.seconds // 3600
            minutes = (duration.seconds % 3600) // 60
            
            return f"{hours}h {minutes}min"
        except:
            return "N/A"
    
    async def check_notification_needed(self, user_id: str, trip: Dict) -> Dict:
        """Verificar se deve enviar notificação"""
        distance_traveled = trip['distance_traveled']
        notification_interval = trip['notification_interval']
        last_notification_distance = trip['last_notification_distance']
        
        # Calcular quantas notificações deveriam ter sido enviadas
        expected_notifications = int(distance_traveled // notification_interval)
        sent_notifications = int(last_notification_distance // notification_interval)
        
        should_notify = expected_notifications > sent_notifications
        
        notification_data = {
            'should_notify': should_notify,
            'distance_traveled': round(distance_traveled, 2),
            'notification_interval': notification_interval,
            'next_notification_at': ((expected_notifications + 1) * notification_interval)
        }
        
        if should_notify:
            # Simular busca de posto mais barato
            station_data = self.find_cheapest_station(user_id)
            
            notification_data.update({
                'station': station_data,
                'message': f"⛽ {station_data['name']} - R$ {station_data['price']:.2f}/L",
                'notification_id': str(uuid.uuid4())
            })
            
            # Atualizar última notificação
            self.active_trips[user_id]['last_notification_distance'] = distance_traveled
        
        return notification_data
    
    def find_cheapest_station(self, user_id: str) -> Dict:
        """Simular busca do posto mais barato"""
        stations = [
            {
                'id': 'station_1',
                'name': 'Posto Shell BR-101',
                'brand': 'Shell',
                'price': 5.75,
                'distance': 2.5,
                'address': 'BR-101, Km 145',
                'coupon': 'SHELL10 - 10% desconto'
            },
            {
                'id': 'station_2',
                'name': 'Petrobras Itajaí',
                'brand': 'Petrobras',
                'price': 5.82,
                'distance': 4.1,
                'address': 'Av. Marcos Konder, 1234',
                'coupon': None
            },
            {
                'id': 'station_3',
                'name': 'Ipiranga Centro',
                'brand': 'Ipiranga',
                'price': 5.69,
                'distance': 6.2,
                'address': 'Rua Central, 567',
                'coupon': 'IPIRANGA15 - R$ 0,15/litro'
            }
        ]
        
        # Retornar o mais barato
        return min(stations, key=lambda x: x['price'])
    
    async def handle_websocket(self, websocket, path):
        """Gerenciar conexões WebSocket"""
        user_id = None
        try:
            # Aguardar mensagem de autenticação
            auth_message = await websocket.recv()
            auth_data = json.loads(auth_message)
            
            if auth_data.get('type') == 'authenticate':
                user_id = auth_data.get('user_id')
                if user_id:
                    await self.register_connection(websocket, user_id)
                    
                    # Loop principal de comunicação
                    async for message in websocket:
                        try:
                            data = json.loads(message)
                            await self.process_message(user_id, data)
                        except json.JSONDecodeError:
                            await self.send_to_user(user_id, {
                                'type': 'error',
                                'message': 'Formato de mensagem inválido'
                            })
                        except Exception as e:
                            await self.send_to_user(user_id, {
                                'type': 'error',
                                'message': f'Erro ao processar mensagem: {str(e)}'
                            })
            
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            print(f"Erro na conexão WebSocket: {e}")
        finally:
            if user_id:
                await self.unregister_connection(user_id)
    
    async def process_message(self, user_id: str, data: Dict):
        """Processar mensagem recebida do cliente"""
        message_type = data.get('type')
        
        if message_type == 'location_update':
            await self.update_user_location(user_id, data.get('location', {}))
        
        elif message_type == 'start_trip':
            await self.start_trip(user_id, data.get('trip_data', {}))
        
        elif message_type == 'stop_trip':
            await self.stop_trip(user_id)
        
        elif message_type == 'get_trip_status':
            trip = self.active_trips.get(user_id)
            await self.send_to_user(user_id, {
                'type': 'trip_status',
                'trip': trip,
                'has_active_trip': trip is not None
            })
        
        elif message_type == 'ping':
            await self.send_to_user(user_id, {
                'type': 'pong',
                'timestamp': datetime.utcnow().isoformat()
            })
        
        else:
            await self.send_to_user(user_id, {
                'type': 'error',
                'message': f'Tipo de mensagem desconhecido: {message_type}'
            })
    
    async def start_server(self, host='localhost', port=8765):
        """Iniciar servidor WebSocket"""
        print(f"🚀 Iniciando servidor GPS WebSocket em {host}:{port}")
        
        self.server = await websockets.serve(
            self.handle_websocket,
            host,
            port,
            ping_interval=30,
            ping_timeout=10
        )
        
        self.is_running = True
        print(f"✅ Servidor GPS WebSocket rodando em ws://{host}:{port}")
        
        return self.server
    
    async def stop_server(self):
        """Parar servidor WebSocket"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self.is_running = False
            print("🛑 Servidor GPS WebSocket parado")
    
    def get_service_stats(self) -> Dict:
        """Obter estatísticas do serviço"""
        return {
            'active_connections': len(self.active_connections),
            'active_trips': len(self.active_trips),
            'total_users_tracked': len(self.user_locations),
            'server_running': self.is_running,
            'uptime': datetime.utcnow().isoformat()
        }

# Instância global do serviço
gps_service = RealTimeGPSService()

def start_gps_server_thread(host='0.0.0.0', port=8765):
    """Iniciar servidor GPS em thread separada"""
    def run_server():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(gps_service.start_server(host, port))
            loop.run_forever()
        except KeyboardInterrupt:
            print("🛑 Parando servidor GPS...")
        finally:
            loop.run_until_complete(gps_service.stop_server())
            loop.close()
    
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    return thread

if __name__ == "__main__":
    # Teste do servidor GPS
    async def main():
        await gps_service.start_server('localhost', 8765)
        
        try:
            # Manter servidor rodando
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await gps_service.stop_server()
    
    asyncio.run(main())

