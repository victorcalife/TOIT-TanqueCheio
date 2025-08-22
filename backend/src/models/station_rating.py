from src.database import db
from datetime import datetime, timezone

class StationRating(db.Model):
    __tablename__ = 'station_ratings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    station_id = db.Column(db.Integer, db.ForeignKey('gas_stations.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref=db.backref('station_ratings', lazy=True))
    station = db.relationship('GasStation', backref=db.backref('ratings', lazy=True, cascade="all, delete-orphan"))

    __table_args__ = (db.UniqueConstraint('user_id', 'station_id', name='_user_station_uc'),)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'station_id': self.station_id,
            'rating': self.rating,
            'comment': self.comment,
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f'<StationRating {self.id} - Station {self.station_id} by User {self.user_id}>'
