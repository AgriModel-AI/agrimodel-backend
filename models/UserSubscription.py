from models import db
from datetime import datetime, timedelta

class UserSubscription(db.Model):
    __tablename__ = 'user_subscriptions'

    subscriptionId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userId = db.Column(db.Integer, db.ForeignKey('users.userId'), nullable=False)
    planId = db.Column(db.Integer, db.ForeignKey('subscription_plans.planId'), nullable=False)
    startDate = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    endDate = db.Column(db.DateTime, nullable=False)
    isActive = db.Column(db.Boolean, default=True)
    subscriptionType = db.Column(db.String(10), nullable=False)  # 'monthly' or 'yearly'
    paymentReference = db.Column(db.Integer, db.ForeignKey('payment.paymentReference'), nullable=True)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def is_subscription_active(self):
        return self.isActive and self.endDate > datetime.utcnow()

    def to_dict(self):
        return {
            "subscriptionId": self.subscriptionId,
            "userId": self.userId,
            "planId": self.planId,
            "startDate": self.startDate.isoformat(),
            "endDate": self.endDate.isoformat(),
            "isActive": self.isActive,
            "subscriptionType": self.subscriptionType,
            "paymentReference": self.paymentReference,
            "createdAt": self.createdAt.isoformat(),
            "updatedAt": self.updatedAt.isoformat()
        }