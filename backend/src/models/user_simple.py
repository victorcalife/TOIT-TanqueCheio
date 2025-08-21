from src.database import db
from datetime import datetime, timezone
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token

class User(db.Model):
    __tablename__ = 'users'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))
    email_verified = db.Column(db.Boolean, default=False)
    email_verification_token = db.Column(db.String(255))
    password_reset_token = db.Column(db.String(255))
    password_reset_expires = db.Column(db.DateTime(timezone=True))
    last_login = db.Column(db.DateTime(timezone=True))
    is_active = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.now)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    profile = db.relationship('UserProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    sessions = db.relationship('UserSession', backref='user', cascade='all, delete-orphan')
    
    def __init__(self, email, password, name, phone=None):
        self.email = email.lower().strip()
        self.name = name.strip()
        self.phone = phone
        self.set_password(password)
    
    def set_password(self, password):
        """Hash and set password"""
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    def generate_tokens(self):
        """Generate JWT access and refresh tokens"""
        additional_claims = {
            'user_id': self.id,
            'email': self.email,
            'name': self.name
        }
        
        access_token = create_access_token(
            identity=self.id,
            additional_claims=additional_claims,
            expires_delta=datetime.timedelta(hours=1)
        )
        
        refresh_token = create_refresh_token(
            identity=self.id,
            expires_delta=datetime.timedelta(days=30)
        )
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': 3600
        }
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.now(timezone.utc)
        db.session.commit()
    
    def to_dict(self, include_sensitive=False):
        """Convert user to dictionary"""
        data = {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'phone': self.phone,
            'email_verified': self.email_verified,
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_sensitive:
            data.update({
                'email_verification_token': self.email_verification_token,
                'password_reset_token': self.password_reset_token,
                'password_reset_expires': self.password_reset_expires.isoformat() if self.password_reset_expires else None
            })
        
        return data
    
    @staticmethod
    def find_by_email(email):
        """Find user by email"""
        return User.query.filter_by(email=email.lower().strip()).first()
    
    @staticmethod
    def find_by_id(user_id):
        """Find user by ID"""
        return User.query.get(user_id)
    
    def __repr__(self):
        return f'<User {self.email}>'


class UserSession(db.Model):
    __tablename__ = 'user_sessions'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    refresh_token_jti = db.Column(db.String(36), unique=True, nullable=False, index=True)
    device_info = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, index=True)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.now)
    last_used_at = db.Column(db.DateTime(timezone=True), default=datetime.now)
    
    def __init__(self, user_id, refresh_token_jti, expires_at, device_info=None, ip_address=None, user_agent=None):
        self.user_id = user_id
        self.refresh_token_jti = refresh_token_jti
        self.expires_at = expires_at
        self.device_info = device_info
        self.ip_address = ip_address
        self.user_agent = user_agent
    
    def is_expired(self):
        """Check if session is expired"""
        return datetime.now(timezone.utc) > self.expires_at
    
    def revoke(self):
        """Revoke session"""
        self.is_active = False
        db.session.commit()
    
    def update_last_used(self):
        """Update last used timestamp"""
        self.last_used_at = datetime.now(timezone.utc)
        db.session.commit()
    
    def to_dict(self):
        """Convert session to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'device_info': self.device_info,
            'ip_address': self.ip_address,
            'is_active': self.is_active,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None
        }
    
    @staticmethod
    def find_by_jti(jti):
        """Find session by refresh token JTI"""
        return UserSession.query.filter_by(refresh_token_jti=jti, is_active=True).first()
    
    @staticmethod
    def revoke_all_for_user(user_id):
        """Revoke all sessions for a user"""
        UserSession.query.filter_by(user_id=user_id).update({'is_active': False})
        db.session.commit()
    
    def __repr__(self):
        return f'<UserSession {self.id} for User {self.user_id}>'

