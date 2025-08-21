from src.database import db
from datetime import datetime, timezone
import uuid
import math

class GasStation(db.Model):
    __tablename__ = 'gas_stations'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(255), nullable=False)
    brand = db.Column(db.String(100), index=True)
    address = db.Column(db.Text, nullable=False)
    city = db.Column(db.String(100), nullable=False, index=True)
    state = db.Column(db.String(2), nullable=False, index=True)
    postal_code = db.Column(db.String(10))
    latitude = db.Column(db.Numeric(10, 8), nullable=False, index=True)
    longitude = db.Column(db.Numeric(11, 8), nullable=False, index=True)
    phone = db.Column(db.String(20))
    operating_hours = db.Column(db.JSON)
    amenities = db.Column(db.JSON)
    partner_id = db.Column(db.String(36), db.ForeignKey('partners.id'))
    data_source = db.Column(db.String(50), default='manual')
    data_confidence = db.Column(db.Numeric(3, 2), default=0.5)
    is_active = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.now)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    fuel_prices = db.relationship('FuelPrice', backref='gas_station', cascade='all, delete-orphan')
    coupons = db.relationship('Coupon', backref='gas_station', cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='gas_station')
    
    # Constraints
    __table_args__ = (
        db.CheckConstraint(data_confidence >= 0),
        db.CheckConstraint(data_confidence <= 1),
        db.Index('idx_gas_stations_location', 'latitude', 'longitude'),
        db.Index('idx_gas_stations_city_state', 'city', 'state'),
    )
    
    def __init__(self, name, address, city, state, latitude, longitude, **kwargs):
        self.name = name
        self.address = address
        self.city = city
        self.state = state.upper()
        self.latitude = latitude
        self.longitude = longitude
        
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def calculate_distance_to(self, latitude, longitude):
        """Calculate distance to given coordinates"""
        return self._calculate_distance(
            float(self.latitude), float(self.longitude),
            latitude, longitude
        )
    
    @staticmethod
    def _calculate_distance(lat1, lon1, lat2, lon2):
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
    
    def get_current_prices(self):
        """Get current active fuel prices"""
        from datetime import timedelta
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)
        
        return FuelPrice.query.filter(
            FuelPrice.gas_station_id == self.id,
            FuelPrice.is_active == True,
            FuelPrice.reported_at > cutoff_date
        ).order_by(FuelPrice.reported_at.desc()).all()
    
    def get_price_for_fuel(self, fuel_type):
        """Get current price for specific fuel type"""
        from datetime import timedelta
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)
        
        return FuelPrice.query.filter(
            FuelPrice.gas_station_id == self.id,
            FuelPrice.fuel_type == fuel_type,
            FuelPrice.is_active == True,
            FuelPrice.reported_at > cutoff_date
        ).order_by(FuelPrice.reported_at.desc()).first()
    
    def get_active_coupons(self, fuel_type=None):
        """Get active coupons for this station"""
        query = Coupon.query.filter(
            Coupon.gas_station_id == self.id,
            Coupon.is_active == True,
            Coupon.valid_until > datetime.now(timezone.utc)
        )
        
        if fuel_type:
            # Filter by fuel type if specified
            query = query.filter(
                db.or_(
                    Coupon.fuel_types.is_(None),
                    Coupon.fuel_types.contains([fuel_type])
                )
            )
        
        return query.all()
    
    def to_dict(self, include_prices=False, include_coupons=False):
        """Convert gas station to dictionary"""
        data = {
            'id': self.id,
            'name': self.name,
            'brand': self.brand,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'postal_code': self.postal_code,
            'latitude': float(self.latitude),
            'longitude': float(self.longitude),
            'phone': self.phone,
            'operating_hours': self.operating_hours,
            'amenities': self.amenities,
            'partner_id': self.partner_id,
            'data_source': self.data_source,
            'data_confidence': float(self.data_confidence),
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_prices:
            data['current_prices'] = [price.to_dict() for price in self.get_current_prices()]
        
        if include_coupons:
            data['active_coupons'] = [coupon.to_dict() for coupon in self.get_active_coupons()]
        
        return data
    
    @staticmethod
    def find_nearby(latitude, longitude, radius_km=50, fuel_type=None, limit=20):
        """Find gas stations within radius"""
        # Simple bounding box calculation for performance
        lat_delta = radius_km / 111.0  # Approximate km per degree latitude
        lon_delta = radius_km / (111.0 * math.cos(math.radians(latitude)))
        
        query = GasStation.query.filter(
            GasStation.is_active == True,
            GasStation.latitude.between(latitude - lat_delta, latitude + lat_delta),
            GasStation.longitude.between(longitude - lon_delta, longitude + lon_delta)
        )
        
        stations = query.limit(limit * 2).all()  # Get more to filter by exact distance
        
        # Calculate exact distances and filter
        nearby_stations = []
        for station in stations:
            distance = station.calculate_distance_to(latitude, longitude)
            if distance <= radius_km:
                station_dict = station.to_dict(include_prices=True)
                station_dict['distance_km'] = round(distance, 2)
                nearby_stations.append(station_dict)
        
        # Sort by distance and limit results
        nearby_stations.sort(key=lambda x: x['distance_km'])
        return nearby_stations[:limit]
    
    @staticmethod
    def find_cheapest_nearby(latitude, longitude, fuel_type, radius_km=50, limit=10):
        """Find cheapest gas stations for fuel type within radius"""
        nearby_stations = GasStation.find_nearby(latitude, longitude, radius_km, fuel_type, limit * 2)
        
        # Filter stations that have the requested fuel type and add price info
        stations_with_prices = []
        for station_data in nearby_stations:
            station = GasStation.query.get(station_data['id'])
            price = station.get_price_for_fuel(fuel_type)
            
            if price:
                station_data['fuel_price'] = price.to_dict()
                station_data['price_per_liter'] = float(price.price)
                stations_with_prices.append(station_data)
        
        # Sort by price and return top results
        stations_with_prices.sort(key=lambda x: x['price_per_liter'])
        return stations_with_prices[:limit]
    
    def __repr__(self):
        return f'<GasStation {self.name} in {self.city}, {self.state}>'

class FuelPrice(db.Model):
    __tablename__ = 'fuel_prices'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    gas_station_id = db.Column(db.String(36), db.ForeignKey('gas_stations.id'), nullable=False)
    fuel_type = db.Column(db.String(20), nullable=False, index=True)
    price = db.Column(db.Numeric(6, 3), nullable=False)
    source = db.Column(db.String(50), nullable=False)
    source_confidence = db.Column(db.Numeric(3, 2), default=0.5)
    reported_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    verified_at = db.Column(db.DateTime(timezone=True))
    verified_by = db.Column(db.String(36), db.ForeignKey('users.id'))
    is_active = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.now)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    notifications = db.relationship('Notification', backref='fuel_price')
    price_reports = db.relationship('PriceReport', backref='fuel_price', cascade='all, delete-orphan')
    
    # Constraints
    __table_args__ = (
        db.CheckConstraint(fuel_type.in_(['gasoline', 'ethanol', 'gnv', 'diesel', 'diesel_s10'])),
        db.CheckConstraint(price > 0),
        db.CheckConstraint(source_confidence >= 0),
        db.CheckConstraint(source_confidence <= 1),
        db.Index('idx_fuel_prices_station_fuel', 'gas_station_id', 'fuel_type'),
    )
    
    def __init__(self, gas_station_id, fuel_type, price, source, reported_at=None, **kwargs):
        self.gas_station_id = gas_station_id
        self.fuel_type = fuel_type
        self.price = price
        self.source = source
        self.reported_at = reported_at or datetime.now(timezone.utc)
        
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def get_fuel_type_display(self):
        """Get display name for fuel type"""
        fuel_types = {
            'gasoline': 'Gasolina',
            'ethanol': 'Etanol',
            'gnv': 'GNV',
            'diesel': 'Diesel',
            'diesel_s10': 'Diesel S10'
        }
        return fuel_types.get(self.fuel_type, self.fuel_type)
    
    def is_recent(self, hours=24):
        """Check if price is recent"""
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        return self.reported_at > cutoff
    
    def verify(self, verified_by_user_id):
        """Mark price as verified"""
        self.verified_at = datetime.now(timezone.utc)
        self.verified_by = verified_by_user_id
        db.session.commit()
    
    def to_dict(self):
        """Convert fuel price to dictionary"""
        return {
            'id': self.id,
            'gas_station_id': self.gas_station_id,
            'fuel_type': self.fuel_type,
            'fuel_type_display': self.get_fuel_type_display(),
            'price': float(self.price),
            'source': self.source,
            'source_confidence': float(self.source_confidence),
            'reported_at': self.reported_at.isoformat() if self.reported_at else None,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'verified_by': self.verified_by,
            'is_active': self.is_active,
            'is_recent': self.is_recent(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<FuelPrice {self.fuel_type} at {self.price} for Station {self.gas_station_id}>'

class Coupon(db.Model):
    __tablename__ = 'coupons'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    gas_station_id = db.Column(db.String(36), db.ForeignKey('gas_stations.id'), nullable=False)
    code = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    discount_type = db.Column(db.String(20), nullable=False)
    discount_value = db.Column(db.Numeric(6, 2), nullable=False)
    fuel_types = db.Column(db.JSON)  # Array of fuel types, null means all types
    min_liters = db.Column(db.Numeric(6, 2))
    min_amount = db.Column(db.Numeric(8, 2))
    valid_from = db.Column(db.DateTime(timezone=True), default=datetime.now)
    valid_until = db.Column(db.DateTime(timezone=True), nullable=False)
    max_uses = db.Column(db.Integer)
    current_uses = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.now)
    
    # Constraints
    __table_args__ = (
        db.CheckConstraint(discount_type.in_(['percentage', 'fixed_amount'])),
        db.CheckConstraint(discount_value > 0),
        db.Index('idx_coupons_station_active', 'gas_station_id', 'is_active'),
        db.Index('idx_coupons_valid_period', 'valid_from', 'valid_until'),
    )
    
    def __init__(self, gas_station_id, code, title, discount_type, discount_value, valid_until, **kwargs):
        self.gas_station_id = gas_station_id
        self.code = code.upper()
        self.title = title
        self.discount_type = discount_type
        self.discount_value = discount_value
        self.valid_until = valid_until
        
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def is_valid(self, fuel_type=None, liters=None, amount=None):
        """Check if coupon is valid for given conditions"""
        now = datetime.now(timezone.utc)
        
        # Check basic validity
        if not self.is_active:
            return False, "Cupom inativo"
        
        if now < self.valid_from:
            return False, "Cupom ainda não válido"
        
        if now > self.valid_until:
            return False, "Cupom expirado"
        
        if self.max_uses and self.current_uses >= self.max_uses:
            return False, "Cupom esgotado"
        
        # Check fuel type
        if fuel_type and self.fuel_types:
            if fuel_type not in self.fuel_types:
                return False, f"Cupom não válido para {fuel_type}"
        
        # Check minimum requirements
        if self.min_liters and liters and liters < float(self.min_liters):
            return False, f"Mínimo de {self.min_liters}L necessário"
        
        if self.min_amount and amount and amount < float(self.min_amount):
            return False, f"Valor mínimo de R$ {self.min_amount:.2f} necessário"
        
        return True, "Cupom válido"
    
    def calculate_discount(self, amount):
        """Calculate discount amount"""
        if self.discount_type == 'percentage':
            return amount * (float(self.discount_value) / 100)
        else:  # fixed_amount
            return min(float(self.discount_value), amount)
    
    def use_coupon(self):
        """Mark coupon as used"""
        self.current_uses += 1
        db.session.commit()
    
    def to_dict(self):
        """Convert coupon to dictionary"""
        return {
            'id': self.id,
            'gas_station_id': self.gas_station_id,
            'code': self.code,
            'title': self.title,
            'description': self.description,
            'discount_type': self.discount_type,
            'discount_value': float(self.discount_value),
            'fuel_types': self.fuel_types,
            'min_liters': float(self.min_liters) if self.min_liters else None,
            'min_amount': float(self.min_amount) if self.min_amount else None,
            'valid_from': self.valid_from.isoformat() if self.valid_from else None,
            'valid_until': self.valid_until.isoformat() if self.valid_until else None,
            'max_uses': self.max_uses,
            'current_uses': self.current_uses,
            'remaining_uses': (self.max_uses - self.current_uses) if self.max_uses else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Coupon {self.code} for Station {self.gas_station_id}>'

class PriceReport(db.Model):
    __tablename__ = 'price_reports'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    fuel_price_id = db.Column(db.String(36), db.ForeignKey('fuel_prices.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    reported_price = db.Column(db.Numeric(6, 3), nullable=False)
    report_type = db.Column(db.String(20), nullable=False)
    confidence_level = db.Column(db.Integer)
    photo_url = db.Column(db.String(500))
    notes = db.Column(db.Text)
    latitude = db.Column(db.Numeric(10, 8))
    longitude = db.Column(db.Numeric(11, 8))
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.now)
    
    # Constraints
    __table_args__ = (
        db.CheckConstraint(report_type.in_(['confirm', 'dispute', 'update'])),
        db.CheckConstraint(confidence_level >= 1),
        db.CheckConstraint(confidence_level <= 5),
        db.CheckConstraint(reported_price > 0),
    )
    
    def to_dict(self):
        """Convert price report to dictionary"""
        return {
            'id': self.id,
            'fuel_price_id': self.fuel_price_id,
            'user_id': self.user_id,
            'reported_price': float(self.reported_price),
            'report_type': self.report_type,
            'confidence_level': self.confidence_level,
            'photo_url': self.photo_url,
            'notes': self.notes,
            'latitude': float(self.latitude) if self.latitude else None,
            'longitude': float(self.longitude) if self.longitude else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<PriceReport {self.report_type} for Price {self.fuel_price_id}>'

