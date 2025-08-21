import googlemaps
import os
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class MapsService:
    def __init__(self):
        # Para desenvolvimento, usar uma chave de exemplo ou simulação
        self.api_key = os.getenv('GOOGLE_MAPS_API_KEY', 'demo_key')
        self.use_simulation = self.api_key == 'demo_key'
        
        if not self.use_simulation:
            self.gmaps = googlemaps.Client(key=self.api_key)
        else:
            self.gmaps = None
            logger.info("Google Maps em modo simulação - usando dados mock")
    
    def geocode_address(self, address: str) -> Optional[Dict]:
        """Converte endereço em coordenadas lat/lng"""
        if self.use_simulation:
            return self._simulate_geocode(address)
        
        try:
            geocode_result = self.gmaps.geocode(address)
            if geocode_result:
                location = geocode_result[0]['geometry']['location']
                return {
                    'latitude': location['lat'],
                    'longitude': location['lng'],
                    'formatted_address': geocode_result[0]['formatted_address']
                }
        except Exception as e:
            logger.error(f"Erro no geocoding: {e}")
            return self._simulate_geocode(address)
        
        return None
    
    def get_route(self, origin: str, destination: str) -> Optional[Dict]:
        """Obtém rota detalhada entre dois pontos"""
        if self.use_simulation:
            return self._simulate_route(origin, destination)
        
        try:
            directions_result = self.gmaps.directions(
                origin, destination,
                mode="driving",
                alternatives=False,
                optimize_waypoints=True
            )
            
            if directions_result:
                route = directions_result[0]
                leg = route['legs'][0]
                
                # Extrair pontos da rota
                route_points = []
                for step in leg['steps']:
                    start_location = step['start_location']
                    route_points.append({
                        'latitude': start_location['lat'],
                        'longitude': start_location['lng']
                    })
                
                # Adicionar ponto final
                end_location = leg['end_location']
                route_points.append({
                    'latitude': end_location['lat'],
                    'longitude': end_location['lng']
                })
                
                return {
                    'distance_km': leg['distance']['value'] / 1000,
                    'duration_minutes': leg['duration']['value'] / 60,
                    'route_points': route_points,
                    'polyline': route['overview_polyline']['points'],
                    'start_address': leg['start_address'],
                    'end_address': leg['end_address']
                }
        except Exception as e:
            logger.error(f"Erro ao obter rota: {e}")
            return self._simulate_route(origin, destination)
        
        return None
    
    def get_route_coordinates(self, origin_lat: float, origin_lng: float, 
                            dest_lat: float, dest_lng: float) -> Optional[Dict]:
        """Obtém rota usando coordenadas"""
        if self.use_simulation:
            return self._simulate_route_coordinates(origin_lat, origin_lng, dest_lat, dest_lng)
        
        try:
            directions_result = self.gmaps.directions(
                (origin_lat, origin_lng),
                (dest_lat, dest_lng),
                mode="driving"
            )
            
            if directions_result:
                route = directions_result[0]
                leg = route['legs'][0]
                
                route_points = []
                for step in leg['steps']:
                    start_location = step['start_location']
                    route_points.append({
                        'latitude': start_location['lat'],
                        'longitude': start_location['lng']
                    })
                
                end_location = leg['end_location']
                route_points.append({
                    'latitude': end_location['lat'],
                    'longitude': end_location['lng']
                })
                
                return {
                    'distance_km': leg['distance']['value'] / 1000,
                    'duration_minutes': leg['duration']['value'] / 60,
                    'route_points': route_points,
                    'polyline': route['overview_polyline']['points']
                }
        except Exception as e:
            logger.error(f"Erro ao obter rota por coordenadas: {e}")
            return self._simulate_route_coordinates(origin_lat, origin_lng, dest_lat, dest_lng)
        
        return None
    
    def _simulate_geocode(self, address: str) -> Dict:
        """Simulação de geocoding para desenvolvimento"""
        # Coordenadas conhecidas para testes
        locations = {
            'balneário camboriú': {'latitude': -26.9906, 'longitude': -48.6356},
            'balneario camboriu': {'latitude': -26.9906, 'longitude': -48.6356},
            'são paulo': {'latitude': -23.5505, 'longitude': -46.6333},
            'sao paulo': {'latitude': -23.5505, 'longitude': -46.6333},
            'vila olímpia': {'latitude': -23.5955, 'longitude': -46.6890},
            'vila olimpia': {'latitude': -23.5955, 'longitude': -46.6890},
            'república': {'latitude': -23.5431, 'longitude': -46.6291},
            'republica': {'latitude': -23.5431, 'longitude': -46.6291},
            'moema': {'latitude': -23.5893, 'longitude': -46.6658}
        }
        
        address_lower = address.lower()
        for key, coords in locations.items():
            if key in address_lower:
                return {
                    'latitude': coords['latitude'],
                    'longitude': coords['longitude'],
                    'formatted_address': address
                }
        
        # Default para São Paulo se não encontrar
        return {
            'latitude': -23.5505,
            'longitude': -46.6333,
            'formatted_address': address
        }
    
    def _simulate_route(self, origin: str, destination: str) -> Dict:
        """Simulação de rota para desenvolvimento"""
        origin_coords = self._simulate_geocode(origin)
        dest_coords = self._simulate_geocode(destination)
        
        return self._simulate_route_coordinates(
            origin_coords['latitude'], origin_coords['longitude'],
            dest_coords['latitude'], dest_coords['longitude']
        )
    
    def _simulate_route_coordinates(self, origin_lat: float, origin_lng: float,
                                  dest_lat: float, dest_lng: float) -> Dict:
        """Simulação de rota por coordenadas"""
        import math
        
        # Calcular distância aproximada
        R = 6371  # Raio da Terra em km
        lat1_rad = math.radians(origin_lat)
        lon1_rad = math.radians(origin_lng)
        lat2_rad = math.radians(dest_lat)
        lon2_rad = math.radians(dest_lng)
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance_km = R * c
        
        # Simular pontos da rota (interpolação linear simples)
        route_points = []
        num_points = max(5, int(distance_km / 50))  # Um ponto a cada ~50km
        
        for i in range(num_points + 1):
            ratio = i / num_points
            lat = origin_lat + (dest_lat - origin_lat) * ratio
            lng = origin_lng + (dest_lng - origin_lng) * ratio
            route_points.append({
                'latitude': lat,
                'longitude': lng
            })
        
        return {
            'distance_km': round(distance_km, 2),
            'duration_minutes': round(distance_km * 1.2, 0),  # ~50km/h média
            'route_points': route_points,
            'polyline': 'simulated_polyline',
            'start_address': f"{origin_lat}, {origin_lng}",
            'end_address': f"{dest_lat}, {dest_lng}"
        }
    
    def find_gas_stations_along_route(self, route_points: List[Dict], 
                                    radius_km: float = 5) -> List[Dict]:
        """Encontra postos ao longo da rota"""
        # Para simulação, retornar postos conhecidos próximos à rota
        # Em produção, usar Google Places API
        
        known_stations = [
            {
                'name': 'Posto Shell BR-101',
                'latitude': -26.9500,
                'longitude': -48.6200,
                'brand': 'Shell',
                'address': 'BR-101, Km 145 - Balneário Camboriú, SC'
            },
            {
                'name': 'Posto Petrobras Tijucas',
                'latitude': -27.2400,
                'longitude': -48.6300,
                'brand': 'Petrobras',
                'address': 'BR-101, Km 180 - Tijucas, SC'
            },
            {
                'name': 'Posto Ipiranga Garuva',
                'latitude': -26.0300,
                'longitude': -48.8500,
                'brand': 'Ipiranga',
                'address': 'BR-101, Km 50 - Garuva, SC'
            },
            {
                'name': 'Posto Shell Registro',
                'latitude': -24.4900,
                'longitude': -47.8400,
                'brand': 'Shell',
                'address': 'BR-116, Km 350 - Registro, SP'
            }
        ]
        
        return known_stations

# Instância global do serviço
maps_service = MapsService()

