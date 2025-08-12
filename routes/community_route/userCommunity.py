from flask import request, jsonify
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import asc, desc, func
from models import User, UserCommunity, Community, Post, db

class UserCommunityResource(Resource):
    @jwt_required()
    def post(self, communityId):
        """Join a community."""
        user_identity = get_jwt_identity()
        userId = int(user_identity["userId"])
        
        community = Community.query.get(communityId)
        if not community:
            return {"message": "Community not found."}, 400

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


class GetUserCommunityResource(Resource):
    @jwt_required()
    def get(self):
        """Get a list of communities with joined status, filtering, sorting, and pagination."""

        # Get the current user's ID
        user_identity = get_jwt_identity()
        user_id = int(user_identity["userId"])

        # Query parameters
        search_query = request.args.get("search", "").strip()
        sort_by = request.args.get("sort_by", "createdAt")  # Default sort: createdAt
        sort_order = request.args.get("sort_order", "desc")  # Default order: desc
        limit = request.args.get("limit", type=int)  # Max items per page
        offset = request.args.get("offset", type=int, default=0)  # Pagination offset

        # Allowed sorting options
        allowed_sort_columns = {
            "name": Community.name,
            "createdAt": Community.createdAt,
            "user_count": func.count(UserCommunity.userId),
            "post_count": func.count(Post.postId),
        }
        sort_column = allowed_sort_columns.get(sort_by, Community.createdAt)
        sort_direction = desc(sort_column) if sort_order.lower() == "desc" else asc(sort_column)

        # Base query
        query = db.session.query(
            Community.communityId,
            Community.name,
            Community.image,
            Community.description,
            Community.createdAt,
            func.count(UserCommunity.userId).label("user_count"),
            func.count(Post.postId).label("post_count"),
            func.count(UserCommunity.userId).filter(UserCommunity.userId == user_id).label("joined")
        ).join(User, Community.createdBy == User.userId) \
        .outerjoin(UserCommunity, Community.communityId == UserCommunity.communityId) \
        .outerjoin(Post, Community.communityId == Post.communityId) \
        .group_by(Community.communityId, User.userId)

        # Apply search filter
        if search_query:
            query = query.filter(
                (Community.name.ilike(f"%{search_query}%")) |
                (Community.description.ilike(f"%{search_query}%"))
            )

        # Apply sorting
        query = query.order_by(sort_direction)

        # Apply pagination
        if limit:
            query = query.limit(limit).offset(offset)

        # Execute query
        communities = query.all()

        # Format results
        data = [{
            "communityId": c.communityId,
            "name": c.name,
            "image": c.image,
            "description": c.description,
            "createdAt": c.createdAt.isoformat(),
            "users": c.user_count,
            "posts": c.post_count,
            "joined": bool(c.joined)  # True if user is a member, False otherwise
        } for c in communities]

        return {"data": data}, 200