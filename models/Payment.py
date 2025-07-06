from models import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON

class Payment(db.Model):
    __tablename__ = 'payment'

    paymentReference = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userId = db.Column(db.Integer, db.ForeignKey('users.userId'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='USD', nullable=False)
    paymentStatus = db.Column(db.String(20), nullable=False)
    paymentMethod = db.Column(db.String(50), nullable=False)
    transactionId = db.Column(db.String(255), nullable=True)
    paymentDate = db.Column(db.DateTime, default=datetime.utcnow)
    otherInfo = db.Column(JSON, nullable=True)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref='payments', lazy=True)
    subscriptions = db.relationship('UserSubscription', backref='payment', lazy=True)