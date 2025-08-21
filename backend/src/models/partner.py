from src.database import db
from datetime import datetime, timezone
import uuid
import secrets

class Partner(db.Model):
    __tablename__ = 'partners'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_name = db.Column(db.String(255), nullable=False)
    contact_name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    api_key = db.Column(db.String(255), unique=True, nullable=False, index=True)
    api_key_expires = db.Column(db.DateTime(timezone=True))
    is_active = db.Column(db.Boolean, default=True, index=True)
    rate_limit_per_hour = db.Column(db.Integer, default=1000)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.now)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    gas_stations = db.relationship('GasStation', backref='partner')
    
    def __init__(self, company_name, contact_name, email, phone=None, rate_limit_per_hour=1000):
        self.company_name = company_name
        self.contact_name = contact_name
        self.email = email.lower().strip()
        self.phone = phone
        self.rate_limit_per_hour = rate_limit_per_hour
        self.api_key = self.generate_api_key()
    
    def generate_api_key(self):
        """Generate secure API key"""
        return f"sk_{secrets.token_urlsafe(32)}"
    
    def regenerate_api_key(self):
        """Regenerate API key"""
        self.api_key = self.generate_api_key()
        db.session.commit()
        return self.api_key
    
    def is_api_key_valid(self):
        """Check if API key is still valid"""
        if not self.is_active:
            return False
        
        if self.api_key_expires:
            return datetime.now(timezone.utc) < self.api_key_expires
        
        return True
    
    def deactivate(self):
        """Deactivate partner account"""
        self.is_active = False
        db.session.commit()
    
    def activate(self):
        """Activate partner account"""
        self.is_active = True
        db.session.commit()
    
    def update_rate_limit(self, new_limit):
        """Update rate limit"""
        self.rate_limit_per_hour = new_limit
        db.session.commit()
    
    def to_dict(self, include_sensitive=False):
        """Convert partner to dictionary"""
        data = {
            'id': self.id,
            'company_name': self.company_name,
            'contact_name': self.contact_name,
            'email': self.email,
            'phone': self.phone,
            'is_active': self.is_active,
            'rate_limit_per_hour': self.rate_limit_per_hour,
            'api_key_expires': self.api_key_expires.isoformat() if self.api_key_expires else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'gas_stations_count': len(self.gas_stations)
        }
        
        if include_sensitive:
            data['api_key'] = self.api_key
        else:
            # Show only last 8 characters for security
            data['api_key_preview'] = f"...{self.api_key[-8:]}" if self.api_key else None
        
        return data
    
    @staticmethod
    def find_by_api_key(api_key):
        """Find partner by API key"""
        return Partner.query.filter_by(api_key=api_key, is_active=True).first()
    
    @staticmethod
    def find_by_email(email):
        """Find partner by email"""
        return Partner.query.filter_by(email=email.lower().strip()).first()
    
    @staticmethod
    def create_partner(company_name, contact_name, email, **kwargs):
        """Create new partner"""
        # Check if email already exists
        if Partner.find_by_email(email):
            raise ValueError("Email already registered")
        
        partner = Partner(
            company_name=company_name,
            contact_name=contact_name,
            email=email,
            **kwargs
        )
        db.session.add(partner)
        db.session.commit()
        
        return partner
    
    def __repr__(self):
        return f'<Partner {self.company_name}>'

