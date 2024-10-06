import re
import uuid
from flask import make_response, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource
from models import Community, db, User


def is_admin():
    claims = get_jwt_identity()
    return claims.get('role') == 'admin'

class CommunityListResource(Resource):
    @jwt_required()
    def get(self):
        """Get a list of all communities."""
        communities = Community.query.all()
        return {
            "data": [{"communityId": c.communityId, "name": c.name, "description": c.description, "createdBy": c.createdBy, "createdAt": c.createdAt.isoformat()} for c in communities]
        }, 200

    @jwt_required()
    def post(self):
        """Create a new community - only admins can create."""
        if not is_admin():
            return {"message": "Admins only: You are not authorized to perform this action."}, 403
        
        data = request.json
        if 'name' not in data or not data['name']:
            return {"message": "Community name is required."}, 400
        
        user_identity = get_jwt_identity()
        userId = int(user_identity["userId"])

         # Fetch user based on userId
        user = User.query.filter_by(userId=userId).first()
        
        if not user:
            return {"message": "User not found."}, 404
        
        # Validate description is optional
        new_community = Community(
            name=data['name'],
            description=data.get('description', ''),
            createdBy=userId
        )
        db.session.add(new_community)
        db.session.commit()
        return {"message": "Community created successfully.", "communityId": new_community.communityId}, 201


class CommunityResource(Resource):
    @jwt_required()
    def get(self, communityId):
        """Get a single community by ID."""
        community = Community.query.get_or_404(communityId)
        return {"data": {"communityId": community.communityId, "name": community.name, "description": community.description, "createdBy": community.createdBy, "createdAt": community.createdAt.isoformat()}}, 200

    @jwt_required()
    def put(self, communityId):
        """Update a community."""
        if not is_admin():
            return {"message": "Admins only: You are not authorized to perform this action."}, 403

        community = Community.query.get_or_404(communityId)
        data = request.json
        community.name = data.get('name', community.name)
        community.description = data.get('description', community.description)
        db.session.commit()
        return {"message": "Community updated successfully."}, 200

    @jwt_required()
    def delete(self, communityId):
        """Delete a community."""
        if not is_admin():
            return {"message": "Admins only: You are not authorized to perform this action."}, 403

        community = Community.query.get_or_404(communityId)
        db.session.delete(community)
        db.session.commit()
        return {"message": "Community deleted successfully."}, 204
    
    @jwt_required()
    def delete(self, communityId):
        """Delete a community."""
        if not is_admin():
            return {"message": "Admins only: You are not authorized to perform this action."}, 403

        try:
            community = Community.query.get_or_404(communityId)
            db.session.delete(community)
            db.session.commit()

            return {"message": "Community deleted successfully."}, 200

        except Exception as e:
            db.session.rollback()
            return {"message": "An error occurred while trying to delete the community. Please try again later."}, 500
