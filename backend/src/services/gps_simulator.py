import math
import time
import requests
import json
from datetime import datetime
import threading

class GPSSimulator:
    def __init__(self, api_base_url, access_token):
        self.api_base_url = api_base_url
        self.access_token = access_token
        self.is_running = False
        self.current_lat = -26.9906  # Balneário Camboriú
        self.current_lng = -48.6356
        self.target_lat = -23.5505   # São Paulo
        self.target_lng = -46.6333
        self.speed_kmh = 80  # Velocidade simulada em km/h
        self.update_interval = 10  # Atualizar a cada 10 segundos
        
    def calculate_distance(self, lat1, lon1, lat2, lon2):
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
    
    def calculate_next_position(self):
        """Calcular próxima posição baseada na velocidade"""
        # Distância total até o destino
        total_distance = self.calculate_distance(
            self.current_lat, self.current_lng,
            self.target_lat, self.target_lng
        )
        
        if total_distance < 0.1:  # Chegou ao destino
            return False
        
        # Distância a percorrer em 10 segundos
        distance_per_update = (self.speed_kmh / 3600) * self.update_interval  # km
        
        # Calcular direção (bearing)
        lat1_rad = math.radians(self.current_lat)
        lat2_rad = math.radians(self.target_lat)
        dlon_rad = math.radians(self.target_lng - self.current_lng)
        
        y = math.sin(dlon_rad) * math.cos(lat2_rad)
        x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon_rad)
        bearing = math.atan2(y, x)
        
        # Calcular nova posição
        R = 6371  # Raio da Terra em km
        lat1_rad = math.radians(self.current_lat)
        lon1_rad = math.radians(self.current_lng)
        
        lat2_rad = math.asin(
            math.sin(lat1_rad) * math.cos(distance_per_update / R) +
            math.cos(lat1_rad) * math.sin(distance_per_update / R) * math.cos(bearing)
        )
        
        lon2_rad = lon1_rad + math.atan2(
            math.sin(bearing) * math.sin(distance_per_update / R) * math.cos(lat1_rad),
            math.cos(distance_per_update / R) - math.sin(lat1_rad) * math.sin(lat2_rad)
        )
        
        self.current_lat = math.degrees(lat2_rad)
        self.current_lng = math.degrees(lon2_rad)
        
        return True
    
    def update_location(self):
        """Enviar atualização de localização para API"""
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'latitude': self.current_lat,
                'longitude': self.current_lng,
                'accuracy': 10,
                'speed': self.speed_kmh
            }
            
            response = requests.post(
                f'{self.api_base_url}/gps/update-location',
                headers=headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"📍 GPS atualizado: {self.current_lat:.6f}, {self.current_lng:.6f}")
                
                if result.get('notification_sent'):
                    print(f"🔔 NOTIFICAÇÃO ENVIADA: {result.get('notification_message')}")
                    print(f"📊 Distância percorrida: {result.get('distance_traveled')}km")
                
                return result
            else:
                print(f"❌ Erro ao atualizar GPS: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Erro na requisição GPS: {e}")
            return None
    
    def start_simulation(self):
        """Iniciar simulação GPS"""
        print("🚀 Iniciando simulação GPS...")
        print(f"📍 Origem: {self.current_lat:.6f}, {self.current_lng:.6f}")
        print(f"🎯 Destino: {self.target_lat:.6f}, {self.target_lng:.6f}")
        print(f"⚡ Velocidade: {self.speed_kmh} km/h")
        print(f"🔄 Atualização: a cada {self.update_interval} segundos")
        print("=" * 50)
        
        self.is_running = True
        
        while self.is_running:
            # Atualizar localização na API
            result = self.update_location()
            
            # Calcular próxima posição
            if not self.calculate_next_position():
                print("🏁 Chegou ao destino!")
                break
            
            # Aguardar próxima atualização
            time.sleep(self.update_interval)
        
        print("✅ Simulação GPS finalizada")
    
    def stop_simulation(self):
        """Parar simulação GPS"""
        self.is_running = False
        print("🛑 Parando simulação GPS...")

def run_gps_simulation(api_base_url, access_token):
    """Executar simulação GPS em thread separada"""
    simulator = GPSSimulator(api_base_url, access_token)
    simulator.start_simulation()

if __name__ == "__main__":
    # Configurações para teste
    API_BASE_URL = "https://j6h5i7cpj5zy.manus.space/api"
    ACCESS_TOKEN = "seu_token_jwt_aqui"
    
    # Executar simulação
    simulator = GPSSimulator(API_BASE_URL, ACCESS_TOKEN)
    
    try:
        simulator.start_simulation()
    except KeyboardInterrupt:
        simulator.stop_simulation()
        print("👋 Simulação interrompida pelo usuário")

