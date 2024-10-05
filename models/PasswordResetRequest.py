from models import db

from datetime import datetime
from sqlalchemy.orm import relationship

class PasswordResetRequest(db.Model):
    __tablename__ = 'password_reset_requests'
    requestId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userId = db.Column(db.Integer, db.ForeignKey('users.userId'), nullable=False)
    token = db.Column(db.String(255), nullable=False)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    expiresAt = db.Column(db.DateTime, nullable=False)

    # Relationship
    user = relationship('User', backref='password_reset_request', uselist=False)

    def is_expired(self):
        """Check if the password reset request has expired."""
        return datetime.utcnow() > self.expiresAt