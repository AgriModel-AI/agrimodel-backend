from models import db

from datetime import datetime
from sqlalchemy.orm import relationship

class User(db.Model):
    __tablename__ = 'users'
    userId = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), unique=True, nullable=False)
    profilePicture = db.Column(db.String(255))
    role = db.Column(db.String(50), nullable=False)  # Role can be 'farmer', 'admin', etc.
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    isVerified = db.Column(db.Boolean, default=False)
    isBlocked = db.Column(db.Boolean, default=False)

    # Relationships
    posts = relationship('Post', backref='user', lazy=True)
    diagnosisResults = relationship('DiagnosisResult', backref='user', lazy=True)
    notifications = relationship('Notification', backref='user', lazy=True)
    user_communities = relationship('UserCommunity', backref='user', lazy=True)