from flask import request
from flask_restful import Resource, abort
from models import db, SubscriptionPlan
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

# Helper function to check admin permissions
def require_admin():
    current_user = get_jwt_identity()
    if current_user['role'] != 'admin':
        abort(403, message="Admin access required")

class SubscriptionPlanListResource(Resource):
    def get(self):
        """Get all active subscription plans"""
        plans = SubscriptionPlan.query.filter_by(isActive=True).all()
        
        result = []
        for plan in plans:
            result.append({
                'planId': plan.planId,
                'name': plan.name,
                'description': plan.description,
                'monthlyPrice': plan.monthlyPrice,
                'yearlyPrice': plan.yearlyPrice,
                'yearlyDiscountPercentage': plan.yearlyDiscountPercentage,
                'features': plan.features,
                'isActive': plan.isActive
            })
            
        return {'plans': result}, 200
    
    @jwt_required()
    def post(self):
        """Create a new subscription plan (admin only)"""
        require_admin()
        
        data = request.get_json()
        required_fields = ['name', 'monthlyPrice']
        for field in required_fields:
            if field not in data:
                abort(400, message=f"Field '{field}' is required")
        
        # Create new plan
        new_plan = SubscriptionPlan(
            name=data['name'],
            description=data.get('description'),
            monthlyPrice=data['monthlyPrice'],
            yearlyPrice=data.get('yearlyPrice', 0),
            yearlyDiscountPercentage=data.get('yearlyDiscountPercentage', 0),
            features=data.get('features'),
            isActive=data.get('isActive', True)
        )
        
        # Calculate yearly price if not provided
        if 'yearlyPrice' not in data:
            new_plan.yearlyPrice = new_plan.calculate_yearly_price()
            
        db.session.add(new_plan)
        db.session.commit()
        
        return {
            'message': 'Subscription plan created successfully',
            'planId': new_plan.planId
        }, 201

class SubscriptionPlanResource(Resource):
    def get(self, plan_id):
        """Get a specific subscription plan"""
        plan = SubscriptionPlan.query.get(plan_id)
        
        if plan:        
            return {
                'planId': plan.planId,
                'name': plan.name,
                'description': plan.description,
                'monthlyPrice': plan.monthlyPrice,
                'yearlyPrice': plan.yearlyPrice,
                'yearlyDiscountPercentage': plan.yearlyDiscountPercentage,
                'features': plan.features,
                'isActive': plan.isActive,
                'createdAt': plan.createdAt.isoformat(),
                'updatedAt': plan.updatedAt.isoformat()
            }, 200
        else:
            return {
                    'message': f'Could not find Plan with ID {plan_id}'
                }, 404
    
    @jwt_required()
    def put(self, plan_id):
        """Update a subscription plan (admin only)"""
        require_admin()
        
        plan = SubscriptionPlan.query.get(plan_id)
        data = request.get_json()
            
        if plan:
            # Update fields
            if 'name' in data:
                plan.name = data['name']
            if 'description' in data:
                plan.description = data['description']
            if 'monthlyPrice' in data:
                plan.monthlyPrice = data['monthlyPrice']
                # Recalculate yearly price if monthly price changes
                if 'yearlyPrice' not in data:
                    plan.update_yearly_price()
            if 'yearlyPrice' in data:
                plan.yearlyPrice = data['yearlyPrice']
            if 'yearlyDiscountPercentage' in data:
                plan.yearlyDiscountPercentage = data['yearlyDiscountPercentage']
                # Recalculate yearly price if discount changes
                if 'yearlyPrice' not in data:
                    plan.update_yearly_price()
            if 'features' in data:
                plan.features = data['features']
            if 'isActive' in data:
                plan.isActive = data['isActive']
                
            plan.updatedAt = datetime.utcnow()
            db.session.commit()
            
            return {
                'message': 'Subscription plan updated successfully'
            }, 200
        else:
            return {
                    'message': f'Could not find Plan with ID {plan_id}'
                }, 404
    
    @jwt_required()
    def delete(self, plan_id):
        """Delete a subscription plan (admin only)"""
        require_admin()
        
        plan = SubscriptionPlan.query.get(plan_id)
        
        # Check if any users are subscribed to this plan
        if plan:
            if plan.subscriptions:
                # Soft delete - mark as inactive instead of removing
                plan.isActive = False
                db.session.commit()
                return {
                    'message': 'Plan has active subscribers. Marked as inactive instead of deleted.'
                }, 200
            else:
                # Hard delete if no subscribers
                db.session.delete(plan)
                db.session.commit()
                return {
                    'message': 'Subscription plan deleted successfully'
                }, 200
        else:
            return {
                    'message': f'Could not find Plan with ID {plan_id}'
                }, 404