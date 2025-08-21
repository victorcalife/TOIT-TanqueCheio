from src.database import db
from datetime import datetime, timezone
import uuid
import math

class UserProfile(db.Model):
    __tablename__ = 'user_profiles'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    preferred_fuel_type = db.Column(db.String(20), nullable=False, default='gasoline')
    notification_enabled = db.Column(db.Boolean, default=True)
    notification_interval_km = db.Column(db.Integer, default=100)
    notification_radius_km = db.Column(db.Integer, default=50)
    last_latitude = db.Column(db.Numeric(10, 8))
    last_longitude = db.Column(db.Numeric(11, 8))
    last_location_update = db.Column(db.DateTime(timezone=True))
    total_distance_km = db.Column(db.Numeric(10, 2), default=0.0)
    last_notification_km = db.Column(db.Numeric(10, 2), default=0.0)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.now)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    gps_tracking = db.relationship('GPSTracking', backref='user_profile', cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user_profile', cascade='all, delete-orphan')
    routes = db.relationship('Route', backref='user_profile', cascade='all, delete-orphan')
    
    # Fuel type constraints
    __table_args__ = (
        db.CheckConstraint(preferred_fuel_type.in_(['gasoline', 'ethanol', 'gnv', 'diesel', 'diesel_s10'])),
        db.CheckConstraint(notification_interval_km > 0),
        db.CheckConstraint(notification_radius_km > 0),
    )
    
    def __init__(self, user_id, preferred_fuel_type='gasoline', notification_enabled=True, 
                 notification_interval_km=100, notification_radius_km=50):
        self.user_id = user_id
        self.preferred_fuel_type = preferred_fuel_type
        self.notification_enabled = notification_enabled
        self.notification_interval_km = notification_interval_km
        self.notification_radius_km = notification_radius_km
    
    def update_location(self, latitude, longitude):
        """Update user location and calculate distance"""
        # Calculate distance from last location if exists
        if self.last_latitude and self.last_longitude:
            distance = self.calculate_distance(
                float(self.last_latitude), float(self.last_longitude),
                latitude, longitude
            )
            self.total_distance_km = float(self.total_distance_km) + distance
        
        # Update location
        self.last_latitude = latitude
        self.last_longitude = longitude
        self.last_location_update = datetime.now(timezone.utc)
        
        db.session.commit()
    
    def should_notify(self):
        """Check if user should receive notification based on distance traveled"""
        if not self.notification_enabled:
            return False
        
        distance_since_last = float(self.total_distance_km) - float(self.last_notification_km)
        return distance_since_last >= self.notification_interval_km
    
    def mark_notification_sent(self):
        """Mark that notification was sent at current distance"""
        self.last_notification_km = self.total_distance_km
        db.session.commit()
    
    @staticmethod
    def calculate_distance(lat1, lon1, lat2, lon2):
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
    
    def get_fuel_type_display(self):
        """Get display name for fuel type"""
        fuel_types = {
            'gasoline': 'Gasolina',
            'ethanol': 'Etanol',
            'gnv': 'GNV',
            'diesel': 'Diesel',
            'diesel_s10': 'Diesel S10'
        }
        return fuel_types.get(self.preferred_fuel_type, self.preferred_fuel_type)
    
    def to_dict(self):
        """Convert profile to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'preferred_fuel_type': self.preferred_fuel_type,
            'fuel_type_display': self.get_fuel_type_display(),
            'notification_enabled': self.notification_enabled,
            'notification_interval_km': self.notification_interval_km,
            'notification_radius_km': self.notification_radius_km,
            'last_latitude': float(self.last_latitude) if self.last_latitude else None,
            'last_longitude': float(self.last_longitude) if self.last_longitude else None,
            'last_location_update': self.last_location_update.isoformat() if self.last_location_update else None,
            'total_distance_km': float(self.total_distance_km),
            'last_notification_km': float(self.last_notification_km),
            'distance_until_next_notification': max(0, self.notification_interval_km - (float(self.total_distance_km) - float(self.last_notification_km))),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def create_profile(user_id, **kwargs):
        """Create new user profile"""
        profile = UserProfile(user_id=user_id, **kwargs)
        db.session.add(profile)
        db.session.commit()
        return profile
    
    @staticmethod
    def find_by_user_id(user_id):
        """Find profile by user ID"""
        return UserProfile.query.filter_by(user_id=user_id).first()
    
    def __repr__(self):
        return f'<UserProfile {self.id} for User {self.user_id}>'

class GPSTracking(db.Model):
    __tablename__ = 'gps_tracking'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_profile_id = db.Column(db.String(36), db.ForeignKey('user_profiles.id'), nullable=False)
    latitude = db.Column(db.Numeric(10, 8), nullable=False)
    longitude = db.Column(db.Numeric(11, 8), nullable=False)
    accuracy = db.Column(db.Numeric(8, 2))
    speed = db.Column(db.Numeric(6, 2))
    heading = db.Column(db.Numeric(5, 2))
    trip_id = db.Column(db.String(36))
    distance_from_last = db.Column(db.Numeric(8, 3), default=0.0)
    recorded_at = db.Column(db.DateTime(timezone=True), default=datetime.now)
    
    def __init__(self, user_profile_id, latitude, longitude, accuracy=None, speed=None, 
                 heading=None, trip_id=None, distance_from_last=0.0):
        self.user_profile_id = user_profile_id
        self.latitude = latitude
        self.longitude = longitude
        self.accuracy = accuracy
        self.speed = speed
        self.heading = heading
        self.trip_id = trip_id
        self.distance_from_last = distance_from_last
    
    def to_dict(self):
        """Convert GPS tracking to dictionary"""
        return {
            'id': self.id,
            'user_profile_id': self.user_profile_id,
            'latitude': float(self.latitude),
            'longitude': float(self.longitude),
            'accuracy': float(self.accuracy) if self.accuracy else None,
            'speed': float(self.speed) if self.speed else None,
            'heading': float(self.heading) if self.heading else None,
            'trip_id': self.trip_id,
            'distance_from_last': float(self.distance_from_last),
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None
        }
    
    def __repr__(self):
        return f'<GPSTracking {self.id} at ({self.latitude}, {self.longitude})>'

class Notification(db.Model):
    __tablename__ = 'notifications'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_profile_id = db.Column(db.String(36), db.ForeignKey('user_profiles.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), default='fuel_recommendation')
    gas_station_id = db.Column(db.String(36), db.ForeignKey('gas_stations.id'))
    fuel_price_id = db.Column(db.String(36), db.ForeignKey('fuel_prices.id'))
    user_latitude = db.Column(db.Numeric(10, 8))
    user_longitude = db.Column(db.Numeric(11, 8))
    sent_at = db.Column(db.DateTime(timezone=True), default=datetime.now)
    read_at = db.Column(db.DateTime(timezone=True))
    clicked_at = db.Column(db.DateTime(timezone=True))
    delivery_status = db.Column(db.String(20), default='sent')
    
    def __init__(self, user_profile_id, title, message, **kwargs):
        self.user_profile_id = user_profile_id
        self.title = title
        self.message = message
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.read_at:
            self.read_at = datetime.now(timezone.utc)
            db.session.commit()
    
    def mark_as_clicked(self):
        """Mark notification as clicked"""
        if not self.clicked_at:
            self.clicked_at = datetime.now(timezone.utc)
            # Also mark as read if not already
            if not self.read_at:
                self.read_at = self.clicked_at
            db.session.commit()
    
    def is_read(self):
        """Check if notification is read"""
        return self.read_at is not None
    
    def is_clicked(self):
        """Check if notification is clicked"""
        return self.clicked_at is not None
    
    def to_dict(self):
        """Convert notification to dictionary"""
        return {
            'id': self.id,
            'user_profile_id': self.user_profile_id,
            'title': self.title,
            'message': self.message,
            'notification_type': self.notification_type,
            'gas_station_id': self.gas_station_id,
            'fuel_price_id': self.fuel_price_id,
            'user_latitude': float(self.user_latitude) if self.user_latitude else None,
            'user_longitude': float(self.user_longitude) if self.user_longitude else None,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'clicked_at': self.clicked_at.isoformat() if self.clicked_at else None,
            'delivery_status': self.delivery_status,
            'is_read': self.is_read(),
            'is_clicked': self.is_clicked()
        }
    
    def __repr__(self):
        return f'<Notification {self.id}: {self.title}>'

