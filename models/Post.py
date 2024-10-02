from models import db

from datetime import datetime
from sqlalchemy.orm import relationship

class Post(db.Model):
    __tablename__ = 'posts'
    postId = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    likes = db.Column(db.Integer, default=0)
    imageUrl = db.Column(db.String(255))
    userId = db.Column(db.Integer, db.ForeignKey('users.userId'), nullable=False)
    communityId = db.Column(db.Integer, db.ForeignKey('communities.communityId'), nullable=False)

    # Relationships
    comments = relationship('Comment', backref='post', lazy=True)