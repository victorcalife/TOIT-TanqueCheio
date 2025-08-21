from src.database import db
from datetime import datetime, timezone
import uuid

class Route(db.Model):
    __tablename__ = 'routes'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_profile_id = db.Column(db.String(36), db.ForeignKey('user_profiles.id'), nullable=False)
    origin_latitude = db.Column(db.Numeric(10, 8), nullable=False)
    origin_longitude = db.Column(db.Numeric(11, 8), nullable=False)
    destination_latitude = db.Column(db.Numeric(10, 8), nullable=False)
    destination_longitude = db.Column(db.Numeric(11, 8), nullable=False)
    origin_address = db.Column(db.Text)
    destination_address = db.Column(db.Text)
    distance_km = db.Column(db.Numeric(8, 2), nullable=False)
    estimated_duration_minutes = db.Column(db.Integer)
    estimated_fuel_needed = db.Column(db.Numeric(6, 2))
    route_polyline = db.Column(db.Text)  # Encoded polyline from Google Maps
    preferences = db.Column(db.JSON)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.now)
    
    # Relationships
    recommendations = db.relationship('RouteRecommendation', backref='route', cascade='all, delete-orphan')
    
    def __init__(self, user_profile_id, origin_latitude, origin_longitude, 
                 destination_latitude, destination_longitude, distance_km, **kwargs):
        self.user_profile_id = user_profile_id
        self.origin_latitude = origin_latitude
        self.origin_longitude = origin_longitude
        self.destination_latitude = destination_latitude
        self.destination_longitude = destination_longitude
        self.distance_km = distance_km
        
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def calculate_fuel_consumption(self, vehicle_efficiency=12.0):
        """Calculate estimated fuel consumption (L/100km)"""
        if not self.estimated_fuel_needed:
            self.estimated_fuel_needed = float(self.distance_km) * (vehicle_efficiency / 100)
            db.session.commit()
        
        return float(self.estimated_fuel_needed)
    
    def get_recommendations_by_score(self, limit=10):
        """Get route recommendations ordered by score"""
        return RouteRecommendation.query.filter_by(route_id=self.id)\
                                       .order_by(RouteRecommendation.recommendation_score.desc())\
                                       .limit(limit).all()
    
    def to_dict(self, include_recommendations=False):
        """Convert route to dictionary"""
        data = {
            'id': self.id,
            'user_profile_id': self.user_profile_id,
            'origin': {
                'latitude': float(self.origin_latitude),
                'longitude': float(self.origin_longitude),
                'address': self.origin_address
            },
            'destination': {
                'latitude': float(self.destination_latitude),
                'longitude': float(self.destination_longitude),
                'address': self.destination_address
            },
            'distance_km': float(self.distance_km),
            'estimated_duration_minutes': self.estimated_duration_minutes,
            'estimated_fuel_needed': float(self.estimated_fuel_needed) if self.estimated_fuel_needed else None,
            'route_polyline': self.route_polyline,
            'preferences': self.preferences,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        if include_recommendations:
            data['recommendations'] = [rec.to_dict() for rec in self.get_recommendations_by_score()]
        
        return data
    
    def __repr__(self):
        return f'<Route {self.id} ({self.distance_km}km)>'

class RouteRecommendation(db.Model):
    __tablename__ = 'route_recommendations'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    route_id = db.Column(db.String(36), db.ForeignKey('routes.id'), nullable=False)
    gas_station_id = db.Column(db.String(36), db.ForeignKey('gas_stations.id'), nullable=False)
    fuel_price_id = db.Column(db.String(36), db.ForeignKey('fuel_prices.id'), nullable=False)
    detour_distance_km = db.Column(db.Numeric(6, 2), nullable=False)
    detour_time_minutes = db.Column(db.Integer)
    savings_amount = db.Column(db.Numeric(6, 2))
    recommendation_score = db.Column(db.Numeric(4, 2))
    position_on_route = db.Column(db.Numeric(4, 2))  # 0.0 to 1.0
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.now)
    
    # Relationships
    gas_station = db.relationship('GasStation', backref='route_recommendations')
    fuel_price = db.relationship('FuelPrice', backref='route_recommendations')
    
    def __init__(self, route_id, gas_station_id, fuel_price_id, detour_distance_km, **kwargs):
        self.route_id = route_id
        self.gas_station_id = gas_station_id
        self.fuel_price_id = fuel_price_id
        self.detour_distance_km = detour_distance_km
        
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def calculate_score(self, price_weight=0.4, distance_weight=0.3, time_weight=0.2, reliability_weight=0.1):
        """Calculate recommendation score based on multiple factors"""
        # Get fuel price and gas station data
        fuel_price = self.fuel_price
        gas_station = self.gas_station
        
        if not fuel_price or not gas_station:
            return 0.0
        
        # Price score (lower price = higher score)
        # Normalize price between 0-10 (assuming price range 3.00-8.00)
        price_score = max(0, 10 - (float(fuel_price.price) - 3.0) * 2)
        
        # Distance score (shorter detour = higher score)
        # Normalize detour distance (0-5km range)
        distance_score = max(0, 10 - float(self.detour_distance_km) * 2)
        
        # Time score (less time = higher score)
        time_score = 10
        if self.detour_time_minutes:
            time_score = max(0, 10 - (self.detour_time_minutes / 5))
        
        # Reliability score based on data confidence and source
        reliability_score = float(fuel_price.source_confidence) * 10
        if gas_station.data_confidence:
            reliability_score = (reliability_score + float(gas_station.data_confidence) * 10) / 2
        
        # Calculate weighted score
        total_score = (
            price_score * price_weight +
            distance_score * distance_weight +
            time_score * time_weight +
            reliability_score * reliability_weight
        )
        
        self.recommendation_score = round(total_score, 2)
        return self.recommendation_score
    
    def calculate_savings(self, reference_price, fuel_needed):
        """Calculate potential savings compared to reference price"""
        if not fuel_needed or not reference_price:
            return 0.0
        
        current_price = float(self.fuel_price.price)
        savings_per_liter = reference_price - current_price
        
        if savings_per_liter > 0:
            self.savings_amount = round(savings_per_liter * fuel_needed, 2)
        else:
            self.savings_amount = 0.0
        
        return float(self.savings_amount)
    
    def to_dict(self):
        """Convert route recommendation to dictionary"""
        data = {
            'id': self.id,
            'route_id': self.route_id,
            'gas_station_id': self.gas_station_id,
            'fuel_price_id': self.fuel_price_id,
            'detour_distance_km': float(self.detour_distance_km),
            'detour_time_minutes': self.detour_time_minutes,
            'savings_amount': float(self.savings_amount) if self.savings_amount else None,
            'recommendation_score': float(self.recommendation_score) if self.recommendation_score else None,
            'position_on_route': float(self.position_on_route) if self.position_on_route else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        # Include gas station and fuel price data
        if self.gas_station:
            data['gas_station'] = self.gas_station.to_dict()
        
        if self.fuel_price:
            data['fuel_price'] = self.fuel_price.to_dict()
        
        return data
    
    @staticmethod
    def create_recommendation(route_id, gas_station_id, fuel_price_id, detour_distance_km, **kwargs):
        """Create new route recommendation with calculated score"""
        recommendation = RouteRecommendation(
            route_id=route_id,
            gas_station_id=gas_station_id,
            fuel_price_id=fuel_price_id,
            detour_distance_km=detour_distance_km,
            **kwargs
        )
        
        # Calculate score
        recommendation.calculate_score()
        
        db.session.add(recommendation)
        db.session.commit()
        
        return recommendation
    
    def __repr__(self):
        return f'<RouteRecommendation {self.id} (Score: {self.recommendation_score})>'

