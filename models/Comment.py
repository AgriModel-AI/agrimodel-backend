from models import db

from datetime import datetime

class Comment(db.Model):
    __tablename__ = 'comments'
    commentId = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    postId = db.Column(db.Integer, db.ForeignKey('posts.postId'), nullable=False)
    userId = db.Column(db.Integer, db.ForeignKey('users.userId'), nullable=False)