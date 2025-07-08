from flask import request
from flask_restful import Resource, abort
from models import db, UserSubscription, SubscriptionPlan, Payment
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
            subscriptions = UserSubscription.query.filter_by(userId=current_user['userId'], isActive=True).all()
        
        result = []
        for sub in subscriptions:
            result.append({
                'subscriptionId': sub.subscriptionId,
                'userId': sub.userId,
                'planId': sub.planId,
                'dailyAttempts': sub.dailyAttempts,
                "isPlanFree": sub.isPlanFree,
                'startDate': sub.startDate.isoformat(),
                'endDate': sub.endDate.isoformat(),
                'isActive': sub.isActive,
                'subscriptionType': sub.subscriptionType,
                'paymentReference': sub.paymentReference,
                'createdAt': sub.createdAt.isoformat()
            })
            
        return {'data': result}, 200
    
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
        planId = data['planId']
        plan = SubscriptionPlan.query.get(planId)
        
        if not plan:
            abort(404, message=f'Could not find Plan with ID {planId}')
            
        if not plan.isActive:
            abort(400, message="Selected subscription plan is not available")
            
         # Cannot directly subscribe to a free plan
        if plan.isPlanFree:
            abort(400, message="Cannot subscribe to free plan. Free plan is automatically assigned.")
            
        existing_subscription = UserSubscription.query.filter_by(
            userId=current_user['userId'], 
            isActive=True
        ).first()
        # if existing_subscription and existing_subscription.is_subscription_active():
        #     abort(400, message="User already has an active subscription")
        
        if existing_subscription and existing_subscription.is_subscription_active():
            # Deactivate current subscription if it exists
            existing_subscription.isActive = False
            db.session.commit()
        
        # Check if plan is active
        
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
            currency='RWF',
            paymentStatus='completed',  # Simplified for this example
            paymentMethod=data.get('paymentMethod'),
            transactionId=data.get('transactionId')
        )
        
        try:
            db.session.add(payment)
            db.session.commit()
            db.session.flush()
        except Exception as e:
            db.session.rollback()
            abort(500, message=f"Failed to create subscription: {str(e)}")
        
        # Create the subscription
        subscription = UserSubscription(
            userId=current_user['userId'],
            planId=planId,
            dailyAttempts=plan.dailyAttempts,
            isPlanFree=plan.isPlanFree,
            startDate=start_date,
            endDate=end_date,
            isActive=True,
            subscriptionType=data['subscriptionType'],
            paymentReference=payment.paymentReference
        )
        
        try:
            db.session.add(subscription)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            abort(500, message=f"Failed to create subscription: {str(e)}")
        
        return {
            'message': 'Subscription created successfully',
            'data': subscription.to_dict()
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
                'dailyAttempts': subscription.dailyAttempts,
                "isPlanFree": subscription.isPlanFree,
                'startDate': subscription.startDate.isoformat(),
                'endDate': subscription.endDate.isoformat(),
                'isActive': subscription.isActive,
                'subscriptionType': subscription.subscriptionType,
                'isCurrentlyActive': subscription.is_subscription_active(),
                'createdAt': subscription.createdAt.isoformat(),
                'updatedAt': subscription.updatedAt.isoformat()
            }
        }, 200
    
    @jwt_required()
    def put(self, subscription_id):
        """Update a subscription"""
        current_user = get_jwt_identity()
        
        subscription = UserSubscription.query.get(subscription_id)
        
        if not subscription:
            abort(404, message=f'Could not find Subscription with ID {subscription_id}')
        
        # Only admins or the subscription owner can modify it
        if current_user['role'] != 'admin' and subscription.userId != current_user['userId']:
            abort(403, message="Access denied")
        
        data = request.get_json()
            
        if 'isActive' in data and current_user['role'] == 'admin':
            # Only admins can directly set isActive
            subscription.isActive = data['isActive']
            
        # Cancel subscription
        if data.get('cancel') == True and subscription.isActive:
            subscription.isActive = False
        
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
            
        subscription.isActive = False
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
                'dailyAttempts': sub.dailyAttempts,
                "isPlanFree": sub.isPlanFree,
                'startDate': sub.startDate.isoformat(),
                'endDate': sub.endDate.isoformat(),
                'isActive': sub.isActive,
                'isCurrentlyActive': sub.is_subscription_active(),
                'subscriptionType': sub.subscriptionType
            })
            
        return {'subscriptions': result}, 200