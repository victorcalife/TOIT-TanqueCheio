from src.database import db
from datetime import datetime, timezone
import uuid
from werkzeug.security import generate_password_hash, check_password_hash

# Modelo User simplificado
class User(db.Model):
    __tablename__ = 'users'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.now)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Modelo UserProfile simplificado
class UserProfile(db.Model):
    __tablename__ = 'user_profiles'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, unique=True)
    preferred_fuel = db.Column(db.String(20), default='gasoline')
    notification_interval_km = db.Column(db.Integer, default=100)
    notifications_enabled = db.Column(db.Boolean, default=True)
    max_detour_km = db.Column(db.Numeric(4, 1), default=5.0)
    last_latitude = db.Column(db.Numeric(10, 8))
    last_longitude = db.Column(db.Numeric(11, 8))
    total_distance_traveled = db.Column(db.Numeric(10, 2), default=0)
    distance_since_last_notification = db.Column(db.Numeric(8, 2), default=0)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.now)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
    
    def should_notify(self):
        return (self.notifications_enabled and 
                self.distance_since_last_notification >= self.notification_interval_km)

# Modelo GasStation simplificado
class GasStation(db.Model):
    __tablename__ = 'gas_stations'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(200), nullable=False)
    brand = db.Column(db.String(100))
    address = db.Column(db.Text)
    latitude = db.Column(db.Numeric(10, 8), nullable=False, index=True)
    longitude = db.Column(db.Numeric(11, 8), nullable=False, index=True)
    phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.now)

# Modelo FuelPrice simplificado
class FuelPrice(db.Model):
    __tablename__ = 'fuel_prices'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    gas_station_id = db.Column(db.String(36), db.ForeignKey('gas_stations.id'), nullable=False)
    fuel_type = db.Column(db.String(20), nullable=False)
    price = db.Column(db.Numeric(6, 3), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)

# Modelo GPSTracking simplificado
class GPSTracking(db.Model):
    __tablename__ = 'gps_tracking'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    trip_id = db.Column(db.String(36), nullable=False)
    latitude = db.Column(db.Numeric(10, 8), nullable=False)
    longitude = db.Column(db.Numeric(11, 8), nullable=False)
    timestamp = db.Column(db.DateTime(timezone=True), default=datetime.now)

# Modelo Notification simplificado
class Notification(db.Model):
    __tablename__ = 'notifications'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    gas_station_id = db.Column(db.String(36), db.ForeignKey('gas_stations.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.now)

