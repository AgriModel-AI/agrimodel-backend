from flask import request, jsonify
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import UserCommunity, Community, Post, db

class UserCommunityResource(Resource):
    @jwt_required()
    def post(self, communityId):
        """Join a community."""
        user_identity = get_jwt_identity()
        userId = int(user_identity["userId"])

        # Check if the user is already a member of the community
        existing_membership = UserCommunity.query.filter_by(userId=userId, communityId=communityId).first()
        if existing_membership:
            return {"message": "User is already a member of this community."}, 400

        new_membership = UserCommunity(
            userId=userId,
            communityId=communityId
        )

        db.session.add(new_membership)
        db.session.commit()
        return {"message": "Successfully joined the community."}, 201

    @jwt_required()
    def delete(self, communityId):
        """Leave a community."""
        user_identity = get_jwt_identity()
        userId = int(user_identity["userId"])

        membership = UserCommunity.query.filter_by(userId=userId, communityId=communityId).first()
        
        if not membership:
            return {"message": "Membership not found."}, 404

        db.session.delete(membership)
        db.session.commit()
        return {"message": "Successfully left the community."}, 200

    @jwt_required()
    def get(self, communityId):
        """Get all communities joined by the user with their details."""
        user_identity = get_jwt_identity()
        userId = int(user_identity["userId"])

        memberships = UserCommunity.query.filter_by(userId=userId).all()
        
        communities = []
        for mc in memberships:
            community = Community.query.get(mc.communityId)
            if community:  # Check if community exists
                communities.append({
                    "communityId": community.communityId,
                    "name": community.name,  # Assuming there is a 'name' field in the Community model
                    "description": community.description,  # Assuming there is a 'description' field in the Community model
                    "joinedDate": mc.joinedDate.isoformat()
                })
        
        return {"data": communities}, 200