import re
import uuid
from flask import current_app, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource
from sqlalchemy import func, asc, desc
from models import Community, Post, UserCommunity, db, User
from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv
load_dotenv()

# backend_url = os.getenv("BACKEND_URL")
backend_url = 'http://192.168.1.91:5000/'
# Allowed extensions for images
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def is_admin():
    claims = get_jwt_identity()
    return claims.get('role') == 'admin'

class CommunityListResource(Resource):
    @jwt_required()
    def get(self):
        """Get a list of communities with optional filtering, sorting, and pagination."""

        # Query parameters
        search_query = request.args.get('search', '').strip()
        sort_by = request.args.get('sort_by', 'createdAt')  # Default sorting by createdAt
        sort_order = request.args.get('sort_order', 'desc')  # Default to descending order
        limit = request.args.get('limit', type=int)  # Number of items to fetch
        offset = request.args.get('offset', type=int, default=0)  # Pagination offset

        # Validate sorting attribute
        allowed_sort_columns = {
            'name': Community.name,
            'createdAt': Community.createdAt,
            'user_count': func.count(UserCommunity.userId),
            'post_count': func.count(Post.postId)
        }
        sort_column = allowed_sort_columns.get(sort_by, Community.createdAt)
        sort_direction = desc(sort_column) if sort_order.lower() == 'desc' else asc(sort_column)

        # Base query
        query = db.session.query(
            Community.communityId,
            Community.name,
            Community.image,
            Community.description,
            Community.createdAt,
            User.username.label('creator_username'),
            User.email.label('creator_email'),
            func.count(UserCommunity.userId).label('user_count'),
            func.count(Post.postId).label('post_count')
        ).join(User, Community.createdBy == User.userId) \
         .outerjoin(UserCommunity, Community.communityId == UserCommunity.communityId) \
         .outerjoin(Post, Community.communityId == Post.communityId) \
         .group_by(Community.communityId, User.userId)

        # Apply search filter if provided
        if search_query:
            query = query.filter(
                (Community.name.ilike(f"%{search_query}%")) |
                (Community.description.ilike(f"%{search_query}%"))
            )

        # Apply sorting
        query = query.order_by(sort_direction)

        # Apply limit and offset for pagination
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
            "createdBy": {
                "username": c.creator_username,
                "email": c.creator_email
            },
            "createdAt": c.createdAt.isoformat(),
            "users": c.user_count,
            "posts": c.post_count
        } for c in communities]

        return {"data": data}, 200

    @jwt_required()
    def post(self):
        """Create a new community - only admins can create."""
        # if not is_admin():
        #     return {"message": "Admins only: You are not authorized to perform this action."}, 403
        
        data = request.form
        if 'name' not in data or not data['name']:
            return {"message": "Community name is required."}, 400
        
        if 'description' not in data or not data['description']:
            return {"message": "Community description is required."}, 400
        
        image = request.files.get('image')
        if not image or not allowed_file(image.filename):
            return {"message": "A valid image file (png, jpg, jpeg, gif) is required."}, 400
        
        user_identity = get_jwt_identity()
        userId = int(user_identity["userId"])

         # Fetch user based on userId
        user = User.query.filter_by(userId=userId).first()
        
        if not user:
            return {"message": "User not found."}, 404
        
        filename = secure_filename(image.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(current_app.config["COMMUNITY_UPLOAD_FOLDER"], unique_filename)
        image.save(file_path)
        
        
        # Validate description is optional
        new_community = Community(
            name=data['name'],
            description=data.get('description', ''),
            createdBy=userId,
            image=f"{backend_url}api/v1/communities/image/{unique_filename}"
        )
        db.session.add(new_community)
        db.session.commit()
        return {"message": "Community created successfully.", "communityId": new_community.communityId}, 201


class CommunityResource(Resource):
    @jwt_required()
    def get(self, communityId):
        """Get a single community by ID along with creator's username and email."""
        
        # Perform a join to get the community data along with user details
        community = db.session.query(
            Community.communityId, 
            Community.name, 
            Community.image, 
            Community.description, 
            Community.createdAt, 
            User.userId.label('creator_id'), 
            User.username.label('creator_username'), 
            User.email.label('creator_email')
        ).join(User, Community.createdBy == User.userId).filter(Community.communityId == communityId).first()

        if not community:
            return {"message": "Community not found."}, 404

        # Format the result
        data = {
            "communityId": community.communityId,
            "name": community.name,
            "image": community.image,
            "description": community.description,
            "createdBy": {
                "userId": community.creator_id,
                "username": community.creator_username,
                "email": community.creator_email
            },
            "createdAt": community.createdAt.isoformat()
        }

        return {"data": data}, 200
    
    @jwt_required()
    def put(self, communityId):
        """Update a community."""
        if not is_admin():
            return {"message": "Admins only: You are not authorized to perform this action."}, 403

        community = Community.query.get(communityId)
        
        if not community:
            return {"message": "Community not found."}, 404
        
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

        try:
            community = Community.query.get(communityId)
            if not community:
                return {"message": "Community not found."}, 404

            Post.query.filter_by(communityId=communityId).delete()
            
            UserCommunity.query.filter_by(communityId=communityId).delete()

            db.session.delete(community)
            db.session.commit()

            return {"message": "Community deleted successfully."}, 200
        
        except Exception as e:
            db.session.rollback()
            return {"message": "An error occurred while deleting the community.", "error": str(e)}, 500

class CommunityImageResource(Resource):
    
    def patch(self, communityId):
        """Replace the existing image for a specific community with a new one."""
        community = Community.query.get(communityId)
        
        if not community:
            return {"message": "Community not found."}, 404

        # Check if an image file is part of the request
        if 'image' not in request.files:
            return {"message": "No image file provided."}, 400
        
        image = request.files['image']
        
        if image and allowed_file(image.filename):
            # Securely save the new image
            filename = secure_filename(image.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            file_path = os.path.join(current_app.config["COMMUNITY_UPLOAD_FOLDER"], unique_filename)
            image.save(file_path)

            # Delete the old image file if it exists
            if community.image:
                old_image_path = os.path.join(current_app.config["COMMUNITY_UPLOAD_FOLDER"], community.image)
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            
            # Update the community image field
            community.image = f"{backend_url}api/v1/communities/image/{unique_filename}"
            db.session.commit()
            
            image_url_res = f"{backend_url}api/v1/communities/image/{unique_filename}"

            return {"message": "Community image updated successfully.", "image_url": image_url_res}, 200
        else:
            return {"message": "Invalid file format. Allowed types: png, jpg, jpeg, gif."}, 400