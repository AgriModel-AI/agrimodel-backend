import uuid
from flask import current_app, jsonify
from sqlalchemy import asc, desc
from werkzeug.utils import secure_filename
import os
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import request
from config import Config
from models import Post, UserCommunity, db
from sqlalchemy.orm import joinedload


backend_url = 'http://192.168.1.91:5000/'
# Allowed extensions for images
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
class PostsResource(Resource):
    @jwt_required()
    def get(self):
        user_identity = get_jwt_identity()
        userId = int(user_identity["userId"])

        # Fetch community IDs where the user has joined
        user_community_ids = db.session.query(UserCommunity.communityId).filter_by(userId=userId).all()
        community_ids = [c[0] for c in user_community_ids]  # Extract community IDs

        if not community_ids:
            return {"message": "User has not joined any communities"}, 200

        # Get request parameters
        search_query = request.args.get('search', '').strip()
        sort_by = request.args.get('sort_by', 'createdAt')  # Default sorting by createdAt
        sort_order = request.args.get('sort_order', 'desc')  # Default to descending order
        limit = request.args.get('limit', type=int)  # Number of items to fetch
        offset = request.args.get('offset', type=int, default=0)  # Default offset is 0

        # Base query
        query = db.session.query(Post).filter(Post.communityId.in_(community_ids))

        # Apply search filter (if provided)
        if search_query:
            query = query.filter(Post.content.ilike(f"%{search_query}%"))

        # Apply sorting
        if sort_order == "desc":
            query = query.order_by(desc(getattr(Post, sort_by)))
        else:
            query = query.order_by(asc(getattr(Post, sort_by)))

        # Apply pagination (limit/offset)
        if limit:
            query = query.limit(limit).offset(offset)

        # Fetch posts with relationships
        posts = query.options(joinedload(Post.community), joinedload(Post.comments)).all()

        # Format response data
        post_list = [
            {
                "postId": post.postId,
                "content": post.content,
                "createdAt": post.createdAt.strftime("%Y-%m-%d %H:%M:%S"),
                "likes": post.likes,
                "imageUrl": post.imageUrl,
                "community": {
                    "communityId": post.community.communityId,
                    "name": post.community.name,
                },
                "comments": [
                    {
                        "commentId": comment.commentId,
                        "content": comment.content,
                        "createdAt": comment.createdAt.strftime("%Y-%m-%d %H:%M:%S"),
                        "userId": comment.userId,
                    }
                    for comment in post.comments
                ],
            }
            for post in posts
        ]

        return {"posts": post_list}, 200

class PostListResource(Resource):
    @jwt_required()
    def get(self, communityId):
        """Get a list of all posts or filter by community."""
        
        if communityId:
            posts = Post.query.filter_by(communityId=communityId).all()
        else:
            posts = Post.query.all()
        
        return {
            "data": [
                {
                    "postId": p.postId,
                    "content": p.content,
                    "createdAt": p.createdAt.isoformat(),
                    "likes": p.likes,
                    "imageUrl": p.imageUrl,
                    "userId": p.userId,
                    "communityId": p.communityId
                } for p in posts
            ]
        }, 200

    @jwt_required()
    def post(self, communityId):
        """Create a new post with optional image upload."""
        user_identity = get_jwt_identity()
        userId = int(user_identity["userId"])
        
        data = request.form
        if 'content' not in data or not data['content']:
            return {"message": "Content is required."}, 400
        
        image = request.files.get('image')
        if not image or not allowed_file(image.filename):
            return {"message": "A valid image file (png, jpg, jpeg, gif) is required."}, 400
            
            
        filename = secure_filename(image.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(current_app.config["POSTS_UPLOAD_FOLDER"], unique_filename)
        image.save(file_path)

        new_post = Post(
            content=data['content'],
            userId=userId,
            communityId=communityId,
            imageUrl=f"{backend_url}api/v1/communities/posts/image/{unique_filename}"
        )
        
        db.session.add(new_post)
        db.session.commit()
        return {"message": "Post created successfully.", "postId": new_post.postId}, 201



class PostResource(Resource):

    @jwt_required()
    def get(self, postId):
        """Get a post by its ID."""
        post = Post.query.filter_by(postId=postId).first()
        
        if post is None:
            return {"message": "Post not found."}, 404
        
        return {
            "postId": post.postId,
            "content": post.content,
            "createdAt": post.createdAt.isoformat(),
            "likes": post.likes,
            "imageUrl": post.imageUrl,
            "userId": post.userId,
            "communityId": post.communityId
        }, 200
    
    @jwt_required()
    def put(self, postId):
        """Update an existing post."""
        user_identity = get_jwt_identity()
        userId = int(user_identity["userId"])

        post = Post.query.filter_by(postId=postId, userId=userId).first()
        if not post:
            return {"message": "Post not found or you are not authorized to update this post."}, 404

        data = request.form
        if 'content' in data and data['content']:
            post.content = data['content']

        # Handle image upload
        image = request.files.get('image')
        if image:
            if image.filename == '':
                return jsonify({"message": "No selected file"}), 400
            
            if not Config.allowed_file(image.filename):
                return jsonify({"message": "File type not allowed"}), 400
            
            filename = secure_filename(image.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            file_path = os.path.join(current_app.config["POSTS_UPLOAD_FOLDER"], unique_filename)
            image.save(file_path)
            
            post.imageUrl = f"{backend_url}api/v1/communities/posts/image/{unique_filename}"  # Update imageUrl

        db.session.commit()
        return {"message": "Post updated successfully.", "postId": post.postId}, 200
    

    @jwt_required()
    def delete(self, postId):
        """Delete a post."""
        user_identity = get_jwt_identity()
        userId = int(user_identity["userId"])

        post = Post.query.filter_by(postId=postId, userId=userId).first()
        if not post:
            return {"message": "Post not found or you are not authorized to delete this post."}, 404

        db.session.delete(post)
        db.session.commit()
        return {"message": "Post deleted successfully."}, 200
    

class PostLikeResource(Resource):
    @jwt_required()
    def post(self, postId):
        """Like a post."""

        # Increment the likes count on the post
        post = Post.query.get(postId)
        if post:
            post.likes += 1
            db.session.commit()
            return {"message": "Post liked successfully.", "postId": postId, "likes": post.likes}, 201
        else:
            db.session.rollback()  # Rollback the transaction if post not found
            return {"message": "Post not found."}, 404

    @jwt_required()
    def delete(self, postId):
        """Unlike a post."""

        # Decrement the likes count on the post
        post = Post.query.get(postId)
        if post:
            post.likes -= 1
            db.session.commit()
            return {"message": "Post unliked successfully.", "postId": postId, "likes": post.likes}, 200
        else:
            db.session.rollback()  # Rollback the transaction if post not found
            return {"message": "Post not found."}, 404
