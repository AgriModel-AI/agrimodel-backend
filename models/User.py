from models import db
from datetime import datetime
from sqlalchemy.orm import relationship

class User(db.Model):
    __tablename__ = 'users'
    
    userId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.Text, nullable=True)  # Allow null for Google signups
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), unique=True, nullable=True)
    profilePicture = db.Column(db.String(255))
    role = db.Column(db.String(50), nullable=False)  # Role can be 'farmer', 'admin', etc.
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    isVerified = db.Column(db.Boolean, default=False)
    isBlocked = db.Column(db.Boolean, default=False)

    # New fields for Google login
    googleId = db.Column("googleid", db.String(255), unique=True, nullable=True)  # Ensure this matches the DB
    authProvider = db.Column(db.String(50), default='local')  # Can be 'local' or 'google'

    # Relationships
    posts = relationship('Post', backref='user', lazy=True)
    diagnosisResults = relationship('DiagnosisResult', backref='user', lazy=True)
    notifications = relationship('Notification', backref='user', lazy=True)
    user_communities = relationship('UserCommunity', backref='user', lazy=True)
    details = relationship('UserDetails', backref='user', lazy=True)

    def __init__(self, username=None, password=None, email=None, phone_number=None, profilePicture=None, 
                 role='user', googleId=None, authProvider='local', isVerified=False, isBlocked=False):
        self.username = username
        self.password = password
        self.email = email
        self.phone_number = phone_number
        self.profilePicture = profilePicture
        self.role = role
        self.googleId = googleId
        self.authProvider = authProvider
        self.isVerified = isVerified
        self.isBlocked = isBlocked
