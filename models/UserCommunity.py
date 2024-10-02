from models import db

from datetime import datetime

class UserCommunity(db.Model):
    __tablename__ = 'user_communities'
    userId = db.Column(db.Integer, db.ForeignKey('users.userId'), primary_key=True)
    communityId = db.Column(db.Integer, db.ForeignKey('communities.communityId'), primary_key=True)
    joinedDate = db.Column(db.DateTime, default=datetime.utcnow)