from src.database import db
from datetime import datetime, timezone
import uuid
from werkzeug.security import generate_password_hash, check_password_hash

class CleanUser(db.Model):
    __tablename__ = 'clean_users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.String(255), nullable=False)
    preferred_fuel = db.Column(db.String(20), default='gasoline')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.now)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'preferred_fuel': self.preferred_fuel,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class CleanGasStation(db.Model):
    __tablename__ = 'clean_gas_stations'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(200), nullable=False)
    brand = db.Column(db.String(100))
    address = db.Column(db.Text)
    latitude = db.Column(db.Numeric(10, 8), nullable=False)
    longitude = db.Column(db.Numeric(11, 8), nullable=False)
    gasoline_price = db.Column(db.Numeric(6, 3))
    ethanol_price = db.Column(db.Numeric(6, 3))
    diesel_price = db.Column(db.Numeric(6, 3))
    diesel_s10_price = db.Column(db.Numeric(6, 3))
    gnv_price = db.Column(db.Numeric(6, 3))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.now)
    
    def get_fuel_price(self, fuel_type):
        price_map = {
            'gasoline': self.gasoline_price,
            'ethanol': self.ethanol_price,
            'diesel': self.diesel_price,
            'diesel_s10': self.diesel_s10_price,
            'gnv': self.gnv_price
        }
        return float(price_map.get(fuel_type, 0)) if price_map.get(fuel_type) else None
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'brand': self.brand,
            'address': self.address,
            'latitude': float(self.latitude),
            'longitude': float(self.longitude),
            'prices': {
                'gasoline': float(self.gasoline_price) if self.gasoline_price else None,
                'ethanol': float(self.ethanol_price) if self.ethanol_price else None,
                'diesel': float(self.diesel_price) if self.diesel_price else None,
                'diesel_s10': float(self.diesel_s10_price) if self.diesel_s10_price else None,
                'gnv': float(self.gnv_price) if self.gnv_price else None
            },
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

