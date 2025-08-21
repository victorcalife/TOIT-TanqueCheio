from src.database import db
from datetime import datetime, timezone
import uuid

class GPSTracking(db.Model):
    __tablename__ = 'gps_tracking'
    __table_args__ = {'extend_existing': True}
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    trip_id = db.Column(db.String(36), nullable=False, index=True)
    latitude = db.Column(db.Numeric(10, 8), nullable=False)
    longitude = db.Column(db.Numeric(11, 8), nullable=False)
    accuracy = db.Column(db.Numeric(6, 2))  # GPS accuracy in meters
    speed = db.Column(db.Numeric(6, 2))     # Speed in km/h
    heading = db.Column(db.Numeric(6, 2))   # Direction in degrees (0-360)
    altitude = db.Column(db.Numeric(8, 2))  # Altitude in meters
    is_trip_start = db.Column(db.Boolean, default=False)
    is_trip_end = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime(timezone=True), default=datetime.now, index=True)
    
    def __init__(self, user_id, trip_id, latitude, longitude, **kwargs):
        self.user_id = user_id
        self.trip_id = trip_id
        self.latitude = latitude
        self.longitude = longitude
        
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def to_dict(self):
        """Convert GPS tracking point to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'trip_id': self.trip_id,
            'latitude': float(self.latitude),
            'longitude': float(self.longitude),
            'accuracy': float(self.accuracy) if self.accuracy else None,
            'speed': float(self.speed) if self.speed else None,
            'heading': float(self.heading) if self.heading else None,
            'altitude': float(self.altitude) if self.altitude else None,
            'is_trip_start': self.is_trip_start,
            'is_trip_end': self.is_trip_end,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
    
    @staticmethod
    def get_trip_points(user_id, trip_id):
        """Get all GPS points for a specific trip"""
        return GPSTracking.query.filter_by(
            user_id=user_id, 
            trip_id=trip_id
        ).order_by(GPSTracking.timestamp).all()
    
    @staticmethod
    def get_user_trips(user_id, limit=50):
        """Get all trips for a user"""
        return db.session.query(GPSTracking.trip_id).filter_by(
            user_id=user_id
        ).distinct().limit(limit).all()
    
    def __repr__(self):
        return f'<GPSTracking {self.id} ({self.latitude}, {self.longitude})>'


class Notification(db.Model):
    __tablename__ = 'notifications'
    __table_args__ = {'extend_existing': True}
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    gas_station_id = db.Column(db.String(36), db.ForeignKey('gas_stations.id'), nullable=False)
    fuel_type = db.Column(db.String(20), nullable=False)
    price = db.Column(db.Numeric(6, 2), nullable=False)
    distance_km = db.Column(db.Numeric(6, 2), nullable=False)
    message = db.Column(db.Text, nullable=False)
    latitude = db.Column(db.Numeric(10, 8), nullable=False)
    longitude = db.Column(db.Numeric(11, 8), nullable=False)
    is_read = db.Column(db.Boolean, default=False, index=True)
    is_clicked = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime(timezone=True))
    clicked_at = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.now, index=True)
    
    def __init__(self, user_id, gas_station_id, fuel_type, price, distance_km, message, latitude, longitude, **kwargs):
        self.user_id = user_id
        self.gas_station_id = gas_station_id
        self.fuel_type = fuel_type
        self.price = price
        self.distance_km = distance_km
        self.message = message
        self.latitude = latitude
        self.longitude = longitude
        
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = datetime.now(timezone.utc)
            db.session.commit()
    
    def mark_as_clicked(self):
        """Mark notification as clicked"""
        if not self.is_clicked:
            self.is_clicked = True
            self.clicked_at = datetime.now(timezone.utc)
            
            # Also mark as read if not already
            if not self.is_read:
                self.is_read = True
                self.read_at = datetime.now(timezone.utc)
            
            db.session.commit()
    
    def to_dict(self):
        """Convert notification to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'gas_station_id': self.gas_station_id,
            'fuel_type': self.fuel_type,
            'price': float(self.price),
            'distance_km': float(self.distance_km),
            'message': self.message,
            'latitude': float(self.latitude),
            'longitude': float(self.longitude),
            'is_read': self.is_read,
            'is_clicked': self.is_clicked,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'clicked_at': self.clicked_at.isoformat() if self.clicked_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @staticmethod
    def get_unread_count(user_id):
        """Get count of unread notifications for user"""
        return Notification.query.filter_by(user_id=user_id, is_read=False).count()
    
    @staticmethod
    def get_recent_notifications(user_id, limit=10):
        """Get recent notifications for user"""
        return Notification.query.filter_by(user_id=user_id).order_by(
            Notification.created_at.desc()
        ).limit(limit).all()
    
    def __repr__(self):
        return f'<Notification {self.id} for User {self.user_id}>'

