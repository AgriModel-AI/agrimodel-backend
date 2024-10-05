from models import db

from datetime import datetime
from sqlalchemy.orm import relationship

class Community(db.Model):
    __tablename__ = 'communities'
    communityId = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    createdBy = db.Column(db.Integer, db.ForeignKey('users.userId'), nullable=False)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    posts = relationship('Post', backref='community', lazy=True)
    user_communities = relationship('UserCommunity', backref='community', lazy=True)