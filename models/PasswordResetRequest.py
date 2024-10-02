from models import db

from datetime import datetime
from sqlalchemy.orm import relationship

class PasswordResetRequest(db.Model):
    __tablename__ = 'password_reset_requests'
    requestId = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey('users.userId'), nullable=False)
    token = db.Column(db.String(255), nullable=False)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    user = relationship('User', backref='password_reset_request', uselist=False)