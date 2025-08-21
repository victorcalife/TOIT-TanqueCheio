import sqlite3
import uuid
import json
from datetime import datetime
from typing import Dict, List, Optional

class Trip:
    def __init__(self, db_path="/tmp/tanque_cheio.db"):
        self.db_path = db_path
        self._init_tables()
    
    def _init_tables(self):
        """Inicializa tabelas relacionadas a viagens"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        # Tabela de viagens
        cur.execute('''
            CREATE TABLE IF NOT EXISTS trips (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                origin_address TEXT NOT NULL,
                destination_address TEXT NOT NULL,
                origin_latitude REAL NOT NULL,
                origin_longitude REAL NOT NULL,
                destination_latitude REAL NOT NULL,
                destination_longitude REAL NOT NULL,
                fuel_type TEXT NOT NULL DEFAULT 'gasoline',
                notification_interval INTEGER NOT NULL DEFAULT 100,
                distance_traveled REAL DEFAULT 0,
                last_notification_km REAL DEFAULT 0,
                status TEXT DEFAULT 'active',
                route_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                ended_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Tabela de pontos GPS
        cur.execute('''
            CREATE TABLE IF NOT EXISTS gps_points (
                id TEXT PRIMARY KEY,
                trip_id TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                accuracy REAL,
                speed REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (trip_id) REFERENCES trips (id)
            )
        ''')
        
        # Tabela de notificações enviadas
        cur.execute('''
            CREATE TABLE IF NOT EXISTS trip_notifications (
                id TEXT PRIMARY KEY,
                trip_id TEXT NOT NULL,
                gas_station_id TEXT,
                notification_type TEXT DEFAULT 'fuel_recommendation',
                message TEXT NOT NULL,
                distance_km REAL,
                fuel_price REAL,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                clicked BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (trip_id) REFERENCES trips (id),
                FOREIGN KEY (gas_station_id) REFERENCES gas_stations (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_trip(self, user_id: str, origin_address: str, destination_address: str,
                   origin_lat: float, origin_lng: float, dest_lat: float, dest_lng: float,
                   fuel_type: str = 'gasoline', notification_interval: int = 100,
                   route_data: Dict = None) -> str:
        """Cria uma nova viagem"""
        trip_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        cur.execute('''
            INSERT INTO trips 
            (id, user_id, origin_address, destination_address, origin_latitude, origin_longitude,
             destination_latitude, destination_longitude, fuel_type, notification_interval, 
             route_data, started_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            trip_id, user_id, origin_address, destination_address,
            origin_lat, origin_lng, dest_lat, dest_lng,
            fuel_type, notification_interval,
            json.dumps(route_data) if route_data else None,
            datetime.now()
        ))
        
        conn.commit()
        conn.close()
        
        return trip_id
    
    def get_trip(self, trip_id: str) -> Optional[Dict]:
        """Obtém dados de uma viagem"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        cur.execute("SELECT * FROM trips WHERE id = ?", (trip_id,))
        trip = cur.fetchone()
        
        if trip:
            trip_dict = dict(trip)
            if trip_dict['route_data']:
                trip_dict['route_data'] = json.loads(trip_dict['route_data'])
            
            conn.close()
            return trip_dict
        
        conn.close()
        return None
    
    def get_active_trip(self, user_id: str) -> Optional[Dict]:
        """Obtém viagem ativa do usuário"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        cur.execute(
            "SELECT * FROM trips WHERE user_id = ? AND status = 'active' ORDER BY created_at DESC LIMIT 1",
            (user_id,)
        )
        trip = cur.fetchone()
        
        if trip:
            trip_dict = dict(trip)
            if trip_dict['route_data']:
                trip_dict['route_data'] = json.loads(trip_dict['route_data'])
            
            conn.close()
            return trip_dict
        
        conn.close()
        return None
    
    def update_trip_distance(self, trip_id: str, distance_traveled: float) -> bool:
        """Atualiza distância percorrida na viagem"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        cur.execute(
            "UPDATE trips SET distance_traveled = ? WHERE id = ?",
            (distance_traveled, trip_id)
        )
        
        success = cur.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def add_gps_point(self, trip_id: str, latitude: float, longitude: float,
                     accuracy: float = None, speed: float = None) -> str:
        """Adiciona ponto GPS à viagem"""
        point_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        cur.execute('''
            INSERT INTO gps_points (id, trip_id, latitude, longitude, accuracy, speed)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (point_id, trip_id, latitude, longitude, accuracy, speed))
        
        conn.commit()
        conn.close()
        
        return point_id
    
    def get_gps_history(self, trip_id: str, limit: int = 100) -> List[Dict]:
        """Obtém histórico de pontos GPS da viagem"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        cur.execute('''
            SELECT * FROM gps_points 
            WHERE trip_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (trip_id, limit))
        
        points = [dict(row) for row in cur.fetchall()]
        conn.close()
        
        return points
    
    def calculate_distance_traveled(self, trip_id: str) -> float:
        """Calcula distância total percorrida baseada nos pontos GPS"""
        points = self.get_gps_history(trip_id, limit=1000)
        
        if len(points) < 2:
            return 0.0
        
        # Ordenar por timestamp
        points.sort(key=lambda p: p['timestamp'])
        
        total_distance = 0.0
        
        for i in range(1, len(points)):
            prev_point = points[i-1]
            curr_point = points[i]
            
            distance = self._calculate_haversine_distance(
                prev_point['latitude'], prev_point['longitude'],
                curr_point['latitude'], curr_point['longitude']
            )
            
            total_distance += distance
        
        return total_distance
    
    def _calculate_haversine_distance(self, lat1: float, lon1: float, 
                                    lat2: float, lon2: float) -> float:
        """Calcula distância entre dois pontos usando fórmula de Haversine"""
        import math
        
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
    
    def should_send_notification(self, trip_id: str) -> bool:
        """Verifica se deve enviar notificação baseado na distância percorrida"""
        trip = self.get_trip(trip_id)
        if not trip:
            return False
        
        current_distance = self.calculate_distance_traveled(trip_id)
        last_notification = trip['last_notification_km']
        interval = trip['notification_interval']
        
        # Verificar se passou do intervalo configurado
        return (current_distance - last_notification) >= interval
    
    def mark_notification_sent(self, trip_id: str, gas_station_id: str = None,
                              message: str = "", distance_km: float = 0,
                              fuel_price: float = 0) -> str:
        """Marca que uma notificação foi enviada"""
        notification_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        # Inserir notificação
        cur.execute('''
            INSERT INTO trip_notifications 
            (id, trip_id, gas_station_id, message, distance_km, fuel_price)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (notification_id, trip_id, gas_station_id, message, distance_km, fuel_price))
        
        # Atualizar último km de notificação
        current_distance = self.calculate_distance_traveled(trip_id)
        cur.execute(
            "UPDATE trips SET last_notification_km = ? WHERE id = ?",
            (current_distance, trip_id)
        )
        
        conn.commit()
        conn.close()
        
        return notification_id
    
    def end_trip(self, trip_id: str) -> bool:
        """Finaliza uma viagem"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        cur.execute(
            "UPDATE trips SET status = 'completed', ended_at = ? WHERE id = ?",
            (datetime.now(), trip_id)
        )
        
        success = cur.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def get_user_trips(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Obtém histórico de viagens do usuário"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        cur.execute('''
            SELECT * FROM trips 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (user_id, limit))
        
        trips = []
        for row in cur.fetchall():
            trip_dict = dict(row)
            if trip_dict['route_data']:
                trip_dict['route_data'] = json.loads(trip_dict['route_data'])
            trips.append(trip_dict)
        
        conn.close()
        return trips

# Instância global
trip_manager = Trip()

