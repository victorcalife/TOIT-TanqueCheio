import googlemaps
import requests
from flask import current_app
from typing import List, Dict, Optional, Tuple
import math

class GoogleMapsService:
    """Service for Google Maps API integration"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or current_app.config.get('GOOGLE_MAPS_API_KEY')
        if self.api_key and self.api_key != 'your-google-maps-api-key-here':
            try:
                self.client = googlemaps.Client(key=self.api_key)
            except Exception as e:
                current_app.logger.warning(f"Google Maps API initialization failed: {e}")
                self.client = None
        else:
            self.client = None
            current_app.logger.warning("Google Maps API key not configured")
    
    def is_configured(self) -> bool:
        """Check if Google Maps API is properly configured"""
        return self.client is not None
    
    def geocode_address(self, address: str) -> Optional[Dict]:
        """Convert address to coordinates"""
        if not self.is_configured():
            return None
        
        try:
            result = self.client.geocode(address)
            if result:
                location = result[0]['geometry']['location']
                return {
                    'latitude': location['lat'],
                    'longitude': location['lng'],
                    'formatted_address': result[0]['formatted_address'],
                    'place_id': result[0]['place_id']
                }
        except Exception as e:
            current_app.logger.error(f"Geocoding error: {e}")
        
        return None
    
    def reverse_geocode(self, latitude: float, longitude: float) -> Optional[Dict]:
        """Convert coordinates to address"""
        if not self.is_configured():
            return None
        
        try:
            result = self.client.reverse_geocode((latitude, longitude))
            if result:
                return {
                    'formatted_address': result[0]['formatted_address'],
                    'place_id': result[0]['place_id'],
                    'address_components': result[0]['address_components']
                }
        except Exception as e:
            current_app.logger.error(f"Reverse geocoding error: {e}")
        
        return None
    
    def get_directions(self, origin: Tuple[float, float], destination: Tuple[float, float], 
                      mode: str = 'driving') -> Optional[Dict]:
        """Get directions between two points"""
        if not self.is_configured():
            return None
        
        try:
            result = self.client.directions(
                origin=origin,
                destination=destination,
                mode=mode,
                departure_time='now',
                traffic_model='best_guess'
            )
            
            if result:
                route = result[0]
                leg = route['legs'][0]
                
                return {
                    'distance_km': leg['distance']['value'] / 1000,
                    'duration_minutes': leg['duration']['value'] / 60,
                    'duration_in_traffic_minutes': leg.get('duration_in_traffic', {}).get('value', 0) / 60,
                    'start_address': leg['start_address'],
                    'end_address': leg['end_address'],
                    'polyline': route['overview_polyline']['points'],
                    'steps': [
                        {
                            'instruction': step['html_instructions'],
                            'distance_km': step['distance']['value'] / 1000,
                            'duration_minutes': step['duration']['value'] / 60,
                            'start_location': step['start_location'],
                            'end_location': step['end_location']
                        }
                        for step in leg['steps']
                    ]
                }
        except Exception as e:
            current_app.logger.error(f"Directions error: {e}")
        
        return None
    
    def find_gas_stations_nearby(self, latitude: float, longitude: float, 
                                radius: int = 5000) -> List[Dict]:
        """Find gas stations near a location using Places API"""
        if not self.is_configured():
            return []
        
        try:
            result = self.client.places_nearby(
                location=(latitude, longitude),
                radius=radius,
                type='gas_station'
            )
            
            stations = []
            for place in result.get('results', []):
                station = {
                    'place_id': place['place_id'],
                    'name': place['name'],
                    'latitude': place['geometry']['location']['lat'],
                    'longitude': place['geometry']['location']['lng'],
                    'vicinity': place.get('vicinity', ''),
                    'rating': place.get('rating'),
                    'price_level': place.get('price_level'),
                    'opening_hours': place.get('opening_hours', {}).get('open_now'),
                    'types': place.get('types', [])
                }
                
                # Calculate distance
                station['distance_km'] = self.calculate_distance(
                    latitude, longitude,
                    station['latitude'], station['longitude']
                )
                
                stations.append(station)
            
            # Sort by distance
            stations.sort(key=lambda x: x['distance_km'])
            return stations
            
        except Exception as e:
            current_app.logger.error(f"Places search error: {e}")
            return []
    
    def get_place_details(self, place_id: str) -> Optional[Dict]:
        """Get detailed information about a place"""
        if not self.is_configured():
            return None
        
        try:
            result = self.client.place(
                place_id=place_id,
                fields=['name', 'formatted_address', 'formatted_phone_number',
                       'opening_hours', 'website', 'rating', 'reviews']
            )
            
            if result and 'result' in result:
                place = result['result']
                return {
                    'name': place.get('name'),
                    'address': place.get('formatted_address'),
                    'phone': place.get('formatted_phone_number'),
                    'website': place.get('website'),
                    'rating': place.get('rating'),
                    'opening_hours': place.get('opening_hours', {}).get('weekday_text', []),
                    'reviews': [
                        {
                            'author': review.get('author_name'),
                            'rating': review.get('rating'),
                            'text': review.get('text'),
                            'time': review.get('time')
                        }
                        for review in place.get('reviews', [])[:5]  # Limit to 5 reviews
                    ]
                }
        except Exception as e:
            current_app.logger.error(f"Place details error: {e}")
        
        return None
    
    def find_gas_stations_along_route(self, origin: Tuple[float, float], 
                                    destination: Tuple[float, float],
                                    search_radius: int = 2000) -> List[Dict]:
        """Find gas stations along a route"""
        if not self.is_configured():
            return []
        
        # Get route directions
        directions = self.get_directions(origin, destination)
        if not directions:
            return []
        
        # Extract waypoints along the route
        waypoints = []
        steps = directions.get('steps', [])
        
        # Sample points along the route (every ~10km)
        total_distance = directions['distance_km']
        sample_interval = min(10, total_distance / 5)  # At least 5 samples
        
        current_distance = 0
        for step in steps:
            if current_distance >= sample_interval:
                waypoints.append((
                    step['start_location']['lat'],
                    step['start_location']['lng']
                ))
                current_distance = 0
            current_distance += step['distance_km']
        
        # Add destination
        waypoints.append(destination)
        
        # Find gas stations near each waypoint
        all_stations = []
        seen_place_ids = set()
        
        for waypoint in waypoints:
            stations = self.find_gas_stations_nearby(
                waypoint[0], waypoint[1], search_radius
            )
            
            for station in stations:
                if station['place_id'] not in seen_place_ids:
                    # Calculate position on route (0.0 to 1.0)
                    station['position_on_route'] = self.calculate_route_position(
                        station['latitude'], station['longitude'],
                        origin, destination, directions
                    )
                    
                    all_stations.append(station)
                    seen_place_ids.add(station['place_id'])
        
        # Sort by position on route
        all_stations.sort(key=lambda x: x['position_on_route'])
        return all_stations
    
    def calculate_route_position(self, station_lat: float, station_lng: float,
                               origin: Tuple[float, float], destination: Tuple[float, float],
                               directions: Dict) -> float:
        """Calculate relative position of a point along a route (0.0 to 1.0)"""
        # Simple approximation: calculate distance from origin and destination
        distance_from_origin = self.calculate_distance(
            origin[0], origin[1], station_lat, station_lng
        )
        
        distance_from_destination = self.calculate_distance(
            destination[0], destination[1], station_lat, station_lng
        )
        
        total_route_distance = directions['distance_km']
        
        # Estimate position based on distances
        if total_route_distance == 0:
            return 0.0
        
        position = distance_from_origin / total_route_distance
        return min(1.0, max(0.0, position))
    
    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points using Haversine formula"""
        # Convert latitude and longitude from degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of earth in kilometers
        r = 6371
        
        return c * r
    
    def get_travel_time_matrix(self, origins: List[Tuple[float, float]], 
                              destinations: List[Tuple[float, float]]) -> Optional[Dict]:
        """Get travel times and distances between multiple origins and destinations"""
        if not self.is_configured():
            return None
        
        try:
            result = self.client.distance_matrix(
                origins=origins,
                destinations=destinations,
                mode='driving',
                departure_time='now',
                traffic_model='best_guess'
            )
            
            if result and result['status'] == 'OK':
                matrix = []
                for i, row in enumerate(result['rows']):
                    matrix_row = []
                    for j, element in enumerate(row['elements']):
                        if element['status'] == 'OK':
                            matrix_row.append({
                                'distance_km': element['distance']['value'] / 1000,
                                'duration_minutes': element['duration']['value'] / 60,
                                'duration_in_traffic_minutes': element.get('duration_in_traffic', {}).get('value', 0) / 60
                            })
                        else:
                            matrix_row.append(None)
                    matrix.append(matrix_row)
                
                return {
                    'origins': result['origin_addresses'],
                    'destinations': result['destination_addresses'],
                    'matrix': matrix
                }
        except Exception as e:
            current_app.logger.error(f"Distance matrix error: {e}")
        
        return None

# Global service instance - will be initialized in app context
google_maps_service = None

def init_google_maps_service(app):
    """Initialize Google Maps service with app context"""
    global google_maps_service
    with app.app_context():
        google_maps_service = GoogleMapsService()

