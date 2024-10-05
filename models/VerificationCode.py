from models import db

from datetime import datetime
from sqlalchemy.orm import relationship

class VerificationCode(db.Model):
    __tablename__ = 'verification_codes'
    codeId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userId = db.Column(db.Integer, db.ForeignKey('users.userId'), nullable=False)
    code = db.Column(db.String(6), nullable=False)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    expiresAt = db.Column(db.DateTime, nullable=False)
    isUsed = db.Column(db.Boolean, default=False)

    # Relationship
    user = relationship('User', backref='verification_code', uselist=False)