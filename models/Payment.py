from models import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON

class Payment(db.Model):
    __tablename__ = 'payment'
    
    paymentReference = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userId = db.Column(db.Integer, db.ForeignKey('users.userId'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='USD', nullable=False)
    paymentStatus = db.Column(db.String(20), nullable=False)  # 'pending', 'completed', 'failed', 'refunded'
    paymentMethod = db.Column(db.String(50), nullable=False)  # 'credit_card', 'paypal', 'bank_transfer', etc.
    transactionId = db.Column(db.String(255), nullable=True)  # External payment processor transaction ID
    paymentDate = db.Column(db.DateTime, default=datetime.utcnow)
    otherInfo = db.Column(JSON, nullable=True)  # Additional payment details
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='payments', lazy=True)
    subscriptions = db.relationship('UserSubscription', backref='payment', lazy=True)