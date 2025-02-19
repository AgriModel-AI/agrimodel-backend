from models import db
from datetime import datetime

class PostLike(db.Model):
    __tablename__ = 'post_likes'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    postId = db.Column(db.Integer, db.ForeignKey('posts.postId'), nullable=False)
    userId = db.Column(db.Integer, db.ForeignKey('users.userId'), nullable=False)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)

    # Ensure a user can only like once per post
    __table_args__ = (db.UniqueConstraint('postId', 'userId', name='unique_post_like'),)