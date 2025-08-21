from src.database import db
from datetime import datetime

class Coupon(db.Model):
    """Modelo para cupons de desconto"""
    __tablename__ = 'coupons'
    __table_args__ = {'extend_existing': True}
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    gas_station_id = db.Column(db.Integer, db.ForeignKey('gas_stations.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    discount_type = db.Column(db.String(20), nullable=False)  # 'percentage' ou 'fixed'
    discount_value = db.Column(db.Float, nullable=False)
    fuel_type = db.Column(db.String(20))  # Tipo de combustível específico (opcional)
    minimum_amount = db.Column(db.Float, default=0)  # Valor mínimo para usar o cupom
    valid_from = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    valid_until = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    usage_limit = db.Column(db.Integer)  # Limite de uso (opcional)
    usage_count = db.Column(db.Integer, default=0)  # Quantas vezes foi usado
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    gas_station = db.relationship('GasStation', backref='coupons')
    
    def to_dict(self):
        return {
            'id': self.id,
            'gas_station_id': self.gas_station_id,
            'title': self.title,
            'description': self.description,
            'discount_type': self.discount_type,
            'discount_value': self.discount_value,
            'fuel_type': self.fuel_type,
            'minimum_amount': self.minimum_amount,
            'valid_from': self.valid_from.isoformat() if self.valid_from else None,
            'valid_until': self.valid_until.isoformat() if self.valid_until else None,
            'is_active': self.is_active,
            'usage_limit': self.usage_limit,
            'usage_count': self.usage_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @property
    def is_valid(self):
        """Verifica se o cupom está válido"""
        now = datetime.utcnow()
        return (
            self.is_active and
            self.valid_from <= now <= self.valid_until and
            (self.usage_limit is None or self.usage_count < self.usage_limit)
        )
    
    def calculate_discount(self, amount):
        """Calcula o desconto baseado no valor"""
        if not self.is_valid or amount < self.minimum_amount:
            return 0
        
        if self.discount_type == 'percentage':
            return amount * (self.discount_value / 100)
        elif self.discount_type == 'fixed':
            return min(self.discount_value, amount)
        
        return 0

