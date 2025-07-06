from models import db
from datetime import date

class UserDailyUsage(db.Model):
    __tablename__ = 'user_daily_usage'

    usageId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userId = db.Column(db.Integer, db.ForeignKey('users.userId'), nullable=False)
    date = db.Column(db.Date, default=date.today, nullable=False)
    attemptsUsed = db.Column(db.Integer, default=0)

    __table_args__ = (db.UniqueConstraint('userId', 'date', name='unique_user_daily'),)