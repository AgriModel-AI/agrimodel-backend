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
                'dailyAttempts': plan.dailyAttempts,
                'monthlyPrice': plan.monthlyPrice,
                'yearlyPrice': plan.yearlyPrice,
                'yearlyDiscountPercentage': plan.yearlyDiscountPercentage,
                'isPlanFree': plan.isPlanFree,
                'isActive': plan.isActive
            })
            
        return {'data': result}, 200
    
    @jwt_required()
    def post(self):
        """Create a new subscription plan (admin only)"""
        require_admin()
        
        data = request.get_json()
        required_fields = ['name', 'monthlyPrice', 'description', 'dailyAttempts']
        for field in required_fields:
            if field not in data:
                abort(400, message=f"Field '{field}' is required")
        
        monthly_price = data['monthlyPrice']
        yearly_price = data.get('yearlyPrice')
        yearly_discount = data.get('yearlyDiscountPercentage', 0)

        if yearly_price is None:
            if yearly_discount is None:
                return {"message": "Provide yearlyPrice or yearlyDiscountPercentage."}, 400
            if not isinstance(yearly_discount, (int, float)) or yearly_discount < 0:
                return {"message": "Invalid yearlyDiscountPercentage."}, 400
            yearly_price = monthly_price * 12 * (1 - yearly_discount / 100)
        
        # Create new plan
        new_plan = SubscriptionPlan(
            name=data['name'],
            description=data.get('description'),
            monthlyPrice=monthly_price,
            yearlyPrice=yearly_price,
            yearlyDiscountPercentage=yearly_discount,
            isActive=data.get('isActive', True),
            isPlanFree=data.get('isPlanFree', False),
            dailyAttempts=data.get('dailyAttempts', None)  # Allow None for unlimited attempts
        )
        
        # Calculate yearly price if not provided
        if 'yearlyPrice' not in data:
            new_plan.yearlyPrice = new_plan.calculate_yearly_price()
            
        db.session.add(new_plan)
        db.session.commit()
        
        return {
            'message': 'Subscription plan created successfully',
            'data': new_plan.to_dict()
        }, 201

class SubscriptionPlanResource(Resource):
    def get(self, plan_id):
        """Get a specific subscription plan"""
        plan = SubscriptionPlan.query.get(plan_id)
        
        if plan:        
            return {
                'data': plan.to_dict()
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
            if 'isActive' in data:
                plan.isActive = data['isActive']
                
            if 'isPlanFree' in data:
                plan.isPlanFree = data['isPlanFree']
                
            if 'dailyAttempts' in data:
                plan.dailyAttempts = data['dailyAttempts']
                
            plan.updatedAt = datetime.utcnow()
            db.session.commit()
            
            return {
                'message': 'Subscription plan updated successfully',
                'data': plan.to_dict() if plan else None
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