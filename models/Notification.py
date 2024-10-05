from models import db

from datetime import datetime

class Notification(db.Model):
    __tablename__ = 'notifications'
    notificationId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    isRead = db.Column(db.Boolean, default=False)
    userId = db.Column(db.Integer, db.ForeignKey('users.userId'), nullable=False)