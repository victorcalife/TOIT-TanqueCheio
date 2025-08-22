import os
import googlemaps
from datetime import datetime
from functools import lru_cache

class GoogleMapsService:
    """Encapsula a comunicação com a API do Google Maps."""

    def __init__(self):
        self.api_key = os.environ.get('GOOGLE_MAPS_API_KEY')
        if not self.api_key:
            raise ValueError("A variável de ambiente GOOGLE_MAPS_API_KEY não foi definida.")
        self.client = googlemaps.Client(key=self.api_key)

    @lru_cache(maxsize=128)
    def get_directions(self, origin: str, destination: str, mode: str = "driving") -> dict:
        """
        Busca direções entre uma origem e um destino.

        Args:
            origin (str): O endereço ou coordenadas do ponto de partida.
            destination (str): O endereço ou coordenadas do ponto de chegada.
            mode (str): O modo de transporte (ex: 'driving', 'walking').

        Returns:
            dict: O resultado da API de direções, incluindo a polilinha da rota.
                  Retorna um dicionário vazio em caso de erro.
        """
        try:
            now = datetime.now()
            directions_result = self.client.directions(origin, destination, mode=mode, departure_time=now)
            
            if not directions_result:
                return {}

            return directions_result[0]  # Retorna a primeira rota encontrada
        except googlemaps.exceptions.ApiError as e:
            print(f"[GoogleMapsService] Erro na API do Google Maps: {e}")
            return {}
        except Exception as e:
            print(f"[GoogleMapsService] Erro inesperado: {e}")
            return {}
