from flask import request
from flask_restful import Resource, abort
from models import db, UserSubscription, SubscriptionPlan, User, Payment
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta

class UserSubscriptionListResource(Resource):
    @jwt_required()
    def get(self):
        """Get all subscriptions (admin) or current user's subscriptions"""
        current_user = get_jwt_identity()
        
        if current_user['role'] == 'admin':
            # Admins can see all subscriptions with optional filtering
            query = UserSubscription.query
            
            # Apply filters if provided
            if request.args.get('isActive'):
                is_active = request.args.get('isActive').lower() == 'true'
                query = query.filter_by(isActive=is_active)
                
            if request.args.get('planId'):
                query = query.filter_by(planId=request.args.get('planId'))
                
            subscriptions = query.all()
        else:
            # Regular users can only see their own subscriptions
            subscriptions = UserSubscription.query.filter_by(userId=current_user['userId']).all()
        
        result = []
        for sub in subscriptions:
            result.append({
                'subscriptionId': sub.subscriptionId,
                'userId': sub.userId,
                'planId': sub.planId,
                'startDate': sub.startDate.isoformat(),
                'endDate': sub.endDate.isoformat(),
                'isActive': sub.isActive,
                'autoRenew': sub.autoRenew,
                'subscriptionType': sub.subscriptionType,
                'createdAt': sub.createdAt.isoformat()
            })
            
        return {'subscriptions': result}, 200
    
    @jwt_required()
    def post(self):
        """Create a new subscription"""
        current_user = get_jwt_identity()
        data = request.get_json()
        
        # Required fields
        required_fields = ['planId', 'subscriptionType']
        for field in required_fields:
            if field not in data:
                abort(400, message=f"Field '{field}' is required")
        
        # Validate subscription type
        if data['subscriptionType'] not in ['monthly', 'yearly']:
            abort(400, message="subscriptionType must be 'monthly' or 'yearly'")
        
        # Get the plan
        plan = SubscriptionPlan.query.get(data['planId'])
        
        if not plan:
            abort(404, message=f'Could not find Plan with ID {data['planId']}')
        
        # Check if plan is active
        if not plan.isActive:
            abort(400, message="Selected subscription plan is not available")
        
        # Set subscription end date based on type
        start_date = datetime.utcnow()
        if data['subscriptionType'] == 'monthly':
            end_date = start_date + timedelta(days=30)
            amount = plan.monthlyPrice
        else:  # yearly
            end_date = start_date + timedelta(days=365)
            amount = plan.yearlyPrice
        
        # Create payment record (simplified, real implementation would integrate with payment gateway)
        payment = Payment(
            userId=current_user['userId'],
            amount=amount,
            currency='USD',
            paymentStatus='completed',  # Simplified for this example
            paymentMethod=data.get('paymentMethod', 'credit_card'),
            transactionId=data.get('transactionId')
        )
        db.session.add(payment)
        db.session.flush()  # Flush to get the payment reference ID
        
        # Create the subscription
        subscription = UserSubscription(
            userId=current_user['userId'],
            planId=data['planId'],
            startDate=start_date,
            endDate=end_date,
            isActive=True,
            autoRenew=data.get('autoRenew', True),
            subscriptionType=data['subscriptionType'],
            paymentReference=payment.paymentReference
        )
        
        db.session.add(subscription)
        db.session.commit()
        
        return {
            'message': 'Subscription created successfully',
            'subscriptionId': subscription.subscriptionId,
            'endDate': subscription.endDate.isoformat()
        }, 201

class UserSubscriptionResource(Resource):
    @jwt_required()
    def get(self, subscription_id):
        """Get a specific subscription"""
        current_user = get_jwt_identity()
        
        subscription = UserSubscription.query.get_or_404(subscription_id)
        
        # Only admins or the subscription owner can view it
        if current_user['role'] != 'admin' and subscription.userId != current_user['userId']:
            abort(403, message="Access denied")
        
        # Get plan details
        plan = SubscriptionPlan.query.get(subscription.planId)
        
        if not plan:
            abort(404, message=f'Could not find Plan with ID {subscription.planId}')
        
        return {
            'subscription': {
                'subscriptionId': subscription.subscriptionId,
                'userId': subscription.userId,
                'planId': subscription.planId,
                'planName': plan.name if plan else 'Unknown Plan',
                'startDate': subscription.startDate.isoformat(),
                'endDate': subscription.endDate.isoformat(),
                'isActive': subscription.isActive,
                'autoRenew': subscription.autoRenew,
                'subscriptionType': subscription.subscriptionType,
                'isCurrentlyActive': subscription.is_subscription_active(),
                'createdAt': subscription.createdAt.isoformat(),
                'updatedAt': subscription.updatedAt.isoformat()
            }
        }, 200
    
    @jwt_required()
    def put(self, subscription_id):
        """Update a subscription (toggle auto-renew, cancel, etc.)"""
        current_user = get_jwt_identity()
        
        subscription = UserSubscription.query.get(subscription_id)
        
        if not subscription:
            abort(404, message=f'Could not find Subscription with ID {subscription_id}')
        
        # Only admins or the subscription owner can modify it
        if current_user['role'] != 'admin' and subscription.userId != current_user['userId']:
            abort(403, message="Access denied")
        
        data = request.get_json()
        
        # Fields that can be updated
        if 'autoRenew' in data:
            subscription.autoRenew = data['autoRenew']
            
        if 'isActive' in data and current_user['role'] == 'admin':
            # Only admins can directly set isActive
            subscription.isActive = data['isActive']
            
        # Cancel subscription
        if data.get('cancel') == True and subscription.isActive:
            subscription.isActive = False
            subscription.autoRenew = False
        
        subscription.updatedAt = datetime.utcnow()
        db.session.commit()
        
        return {
            'message': 'Subscription updated successfully'
        }, 200
    
    @jwt_required()
    def delete(self, subscription_id):
        """Cancel a subscription"""
        current_user = get_jwt_identity()
        
        subscription = UserSubscription.query.get(subscription_id)
        
        if not subscription:
            abort(404, message=f'Could not find Subscription with ID {subscription_id}')
        
        # Only admins or the subscription owner can cancel it
        if current_user['role'] != 'admin' and subscription.userId != current_user['userId']:
            abort(403, message="Access denied")
        
        # Instead of deleting, mark as inactive and turn off auto-renew
        subscription.isActive = False
        subscription.autoRenew = False
        subscription.updatedAt = datetime.utcnow()
        
        db.session.commit()
        
        return {
            'message': 'Subscription cancelled successfully'
        }, 200

class UserSubscriptionsResource(Resource):
    @jwt_required()
    def get(self, user_id):
        """Get all subscriptions for a specific user"""
        current_user = get_jwt_identity()
        
        # Only admins or the user themselves can view their subscriptions
        if current_user['role'] != 'admin' and int(user_id) != current_user['userId']:
            abort(403, message="Access denied")
        
        subscriptions = UserSubscription.query.filter_by(userId=user_id).all()
        
        result = []
        for sub in subscriptions:
            plan = SubscriptionPlan.query.get(sub.planId)
            result.append({
                'subscriptionId': sub.subscriptionId,
                'planId': sub.planId,
                'planName': plan.name if plan else 'Unknown Plan',
                'startDate': sub.startDate.isoformat(),
                'endDate': sub.endDate.isoformat(),
                'isActive': sub.isActive,
                'isCurrentlyActive': sub.is_subscription_active(),
                'autoRenew': sub.autoRenew,
                'subscriptionType': sub.subscriptionType
            })
            
        return {'subscriptions': result}, 200