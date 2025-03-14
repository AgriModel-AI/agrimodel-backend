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
    autoRenew = db.Column(db.Boolean, default=True)
    subscriptionType = db.Column(db.String(10), nullable=False)  # 'monthly' or 'yearly'
    paymentReference = db.Column(db.Integer, db.ForeignKey('payment.paymentReference'), nullable=True)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship is handled by backref in User model
    
    def is_subscription_active(self):
        """Check if subscription is still valid"""
        return self.isActive and self.endDate > datetime.utcnow()
    
    def extend_subscription(self, months=1):
        """Extend subscription by specified months"""
        if self.endDate > datetime.utcnow():
            # If subscription is still active, extend from current end date
            self.endDate = self.endDate + timedelta(days=30*months)
        else:
            # If expired, extend from now
            self.endDate = datetime.utcnow() + timedelta(days=30*months)
            self.isActive = True
        self.updatedAt = datetime.utcnow()