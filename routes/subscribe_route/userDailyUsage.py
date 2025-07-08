from flask import request
from flask_restful import Resource, abort
from models import db, UserDailyUsage, UserSubscription, SubscriptionPlan, User
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import date, datetime, timedelta
from sqlalchemy.exc import IntegrityError

class UserDailyUsageResource(Resource):
    @jwt_required()
    def get(self):
        """Get current user's daily usage and subscription info"""
        current_user = get_jwt_identity()
        user_id = current_user['userId']
        
        # Check active subscription
        subscription, plan = self._get_active_subscription(user_id)
        if not subscription:
            abort(403, message="No active subscription found")
        
        # Get or create today's usage record
        today_usage = self._get_or_create_usage(user_id)
        
        # Calculate remaining attempts
        used = today_usage.attemptsUsed
        
        # Handle unlimited attempts (when dailyAttempts is None)
        if plan.dailyAttempts is None:
            total = "Unlimited"
            remaining = "Unlimited"
            limit_reached = False
        else:
            total = plan.dailyAttempts
            remaining = max(0, total - used)
            limit_reached = used >= total
        
        return {
            "data": {
                "usage": {
                    "date": today_usage.date.isoformat(),
                    "attemptsUsed": used,
                    "dailyLimit": total,
                    "remainingAttempts": remaining,
                    "limitReached": limit_reached,
                    "isUnlimited": plan.dailyAttempts is None
                },
                "subscription": {
                    "subscriptionId": subscription.subscriptionId,
                    "userId": user_id,
                    "isActive": subscription.isActive,
                    "planId": plan.planId,
                    "planName": plan.name,
                    'dailyAttempts': subscription.dailyAttempts,
                    'isPlanFree': subscription.isPlanFree,
                    "startDate": subscription.startDate.isoformat(),
                    "endDate": subscription.endDate.isoformat(),
                    "daysRemaining": (subscription.endDate - datetime.utcnow()).days,
                    "subscriptionType": subscription.subscriptionType
                }
            }
        }, 200
    
    @jwt_required()
    def post(self):
        """Increment usage count for current user"""
        current_user = get_jwt_identity()
        user_id = current_user['userId']
        
        # Check active subscription
        subscription, plan = self._get_active_subscription(user_id)
        if not subscription:
            abort(403, message="No active subscription found")
        
        # Get today's usage
        today_usage = self._get_or_create_usage(user_id)
        
        # Check if daily limit reached - skip this check for unlimited plans
        if plan.dailyAttempts is not None and today_usage.attemptsUsed >= plan.dailyAttempts:
            abort(403, message="Daily usage limit reached")
        
        # Increment usage (even for unlimited plans we track usage)
        today_usage.attemptsUsed += 1
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            abort(500, message=f"Failed to update usage: {str(e)}")
        
        # Response formatting
        used = today_usage.attemptsUsed
        
        # Handle unlimited attempts
        if plan.dailyAttempts is None:
            response = {
                "message": "Usage recorded successfully",
                "data": {
                    "usage": {
                        "date": today_usage.date.isoformat(),
                        "attemptsUsed": used,
                        "dailyLimit": "Unlimited",
                        "remainingAttempts": "Unlimited",
                        "limitReached": False,
                        "isUnlimited": True
                    },
                    "subscription": {
                        "subscriptionId": subscription.subscriptionId,
                        "planId": plan.planId,
                        "userId": user_id,
                        "isActive": subscription.isActive,
                        "planName": plan.name,
                        'dailyAttempts': subscription.dailyAttempts,
                        'isPlanFree': subscription.isPlanFree,
                        "startDate": subscription.startDate.isoformat(),
                        "endDate": subscription.endDate.isoformat(),
                        "daysRemaining": (subscription.endDate - datetime.utcnow()).days,
                        "subscriptionType": subscription.subscriptionType
                    }
                }
            }
        else:
            total = plan.dailyAttempts
            remaining = max(0, total - used)
            response = {
                "message": "Usage recorded successfully",
                "data": {
                    "usage": {
                        "date": today_usage.date.isoformat(),
                        "attemptsUsed": used,
                        "dailyLimit": total,
                        "remainingAttempts": remaining,
                        "limitReached": used >= total,
                        "isUnlimited": False
                    },
                    "subscription": {
                        "subscriptionId": subscription.subscriptionId,
                        "planId": plan.planId,
                        "userId": user_id,
                        "isActive": subscription.isActive,
                        "planName": plan.name,
                        'dailyAttempts': subscription.dailyAttempts,
                        'isPlanFree': subscription.isPlanFree,
                        "startDate": subscription.startDate.isoformat(),
                        "endDate": subscription.endDate.isoformat(),
                        "daysRemaining": (subscription.endDate - datetime.utcnow()).days,
                        "subscriptionType": subscription.subscriptionType
                    }
                }
            }
        
        return response, 200

    def _get_active_subscription(self, user_id):
        """Get user's active subscription and plan"""
        subscription = UserSubscription.query.filter(
            UserSubscription.userId == user_id,
            UserSubscription.isActive == True,
            UserSubscription.endDate > datetime.utcnow()
        ).order_by(UserSubscription.endDate.desc()).first()
        
        if subscription:
            plan = SubscriptionPlan.query.get(subscription.planId)
            if plan and plan.isActive:
                return subscription, plan
        
        # If no active subscription found, get the free plan
        free_plan = SubscriptionPlan.query.filter_by(isPlanFree=True, isActive=True).first()
        
        if not free_plan:
            return None, None
        
        # Create a virtual subscription for the free plan
        virtual_subscription = type('obj', (object,), {
            'subscriptionId': None,
            'planId': free_plan.planId,
            "userId": user_id,
            "isActive": free_plan.isActive,
            "planName": free_plan.name,
            'dailyAttempts': free_plan.dailyAttempts,
            'isPlanFree': free_plan.isPlanFree,
            'startDate': datetime.utcnow(),
            'endDate': datetime.utcnow() + timedelta(days=36500),
            'daysRemaining': datetime.utcnow() + timedelta(days=36500),
            'isActive': True,
            'subscriptionType': 'free',
        })
        
        return virtual_subscription, free_plan
    
    def _get_or_create_usage(self, user_id):
        """Get or create today's usage record"""
        today = date.today()
        usage = UserDailyUsage.query.filter_by(
            userId=user_id,
            date=today
        ).first()
        
        if not usage:
            usage = UserDailyUsage(userId=user_id, date=today, attemptsUsed=0)
            try:
                db.session.add(usage)
                db.session.commit()
            except IntegrityError:
                # Handle race condition if record was created between our check and insert
                db.session.rollback()
                usage = UserDailyUsage.query.filter_by(userId=user_id, date=today).first()
        
        return usage