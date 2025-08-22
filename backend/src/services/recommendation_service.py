from ..models.gas_station import FuelPrice, GasStation
from .google_maps_service import GoogleMapsService
from googlemaps.convert import decode_polyline
from haversine import haversine, Unit
import math

class RecommendationService:

    @staticmethod
    def _distance_point_to_segment(point, seg_start, seg_end):
        """Calcula a distância perpendicular de um ponto a um segmento de linha (em km)."""
        px, py = point
        x1, y1 = seg_start
        x2, y2 = seg_end

        line_mag = haversine(seg_start, seg_end)
        if line_mag < 0.00000001:
            return haversine(point, seg_start)

        u = ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / (line_mag ** 2)

        if u < 0.0:
            return haversine(point, seg_start)
        elif u > 1.0:
            return haversine(point, seg_end)
        else:
            ix = x1 + u * (x2 - x1)
            iy = y1 + u * (y2 - y1)
            return haversine(point, (ix, iy))

    @staticmethod
    def get_recommendations_for_route(origin: str, destination: str, fuel_type: str) -> list:
        maps_service = GoogleMapsService()
        directions = maps_service.get_directions(origin, destination)

        if not directions or 'overview_polyline' not in directions:
            return [] # Retorna vazio se não encontrar rota

        route_polyline = decode_polyline(directions['overview_polyline']['points'])
        route_coords = [(p['lat'], p['lng']) for p in route_polyline]

        # Busca postos com o tipo de combustível especificado
        fuel_prices = FuelPrice.query.filter_by(fuel_type=fuel_type, is_active=True).join(GasStation).filter(GasStation.is_active==True).all()
        
        recommendations = []
        for fuel_price in fuel_prices:
            station = fuel_price.gas_station
            station_coords = (station.latitude, station.longitude)

            # Calcula o desvio mínimo do posto até a rota
            min_distance_km = min(
                RecommendationService._distance_point_to_segment(station_coords, route_coords[i], route_coords[i+1])
                for i in range(len(route_coords) - 1)
            )

            # Considera apenas postos a até 5km da rota
            if min_distance_km > 5:
                continue

            avg_market_price = 5.75  # Simulado: idealmente viria de uma análise de mercado
            savings_per_liter = max(0, avg_market_price - fuel_price.price)
            
            # Heurística de pontuação: prioriza economia e penaliza desvio
            score = max(0, (savings_per_liter * 10) - (min_distance_km * 0.8))
            
            if score > 0:
                recommendations.append({
                    'station': station.to_dict(),
                    'fuel': {
                        'type': fuel_type,
                        'price': fuel_price.price,
                    },
                    'route_info': {
                        'detour_km': round(min_distance_km, 2),
                    },
                    'score': round(score, 2),
                    'estimated_savings': round(savings_per_liter * 40, 2) # Simulado para um tanque de 40L
                })
        
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        
        return recommendations[:10]
