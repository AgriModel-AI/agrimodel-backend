from models import db
from datetime import datetime

class SubscriptionPlan(db.Model):
    __tablename__ = 'subscription_plans'
    
    planId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    monthlyPrice = db.Column(db.Float, nullable=False)
    yearlyPrice = db.Column(db.Float, nullable=False)
    yearlyDiscountPercentage = db.Column(db.Float, default=0)  # Set by admin
    features = db.Column(db.JSON, nullable=True)  # JSON list of features
    isActive = db.Column(db.Boolean, default=True)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    subscriptions = db.relationship('UserSubscription', backref='plan', lazy=True)
    
    def calculate_yearly_price(self):
        """Calculate yearly price after discount"""
        return self.monthlyPrice * 12 * (1 - self.yearlyDiscountPercentage/100)
    
    def update_yearly_price(self):
        """Update yearly price based on monthly price and discount"""
        self.yearlyPrice = self.calculate_yearly_price()