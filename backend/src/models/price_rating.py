from src.database import db
from datetime import datetime, timezone

class PriceRating(db.Model):
    __tablename__ = 'price_ratings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    price_id = db.Column(db.Integer, db.ForeignKey('fuel_prices.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # 'correct', 'incorrect', 'outdated'
    validated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref=db.backref('price_ratings', lazy=True))
    price = db.relationship('FuelPrice', backref=db.backref('ratings', lazy=True, cascade="all, delete-orphan"))

    __table_args__ = (db.UniqueConstraint('user_id', 'price_id', name='_user_price_uc'),)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'price_id': self.price_id,
            'status': self.status,
            'validated_at': self.validated_at.isoformat()
        }

    def __repr__(self):
        return f'<PriceRating {self.id} - Price {self.price_id} by User {self.user_id}>'
