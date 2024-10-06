from flask import jsonify
from werkzeug.utils import secure_filename
import os
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import request
from config import Config
from models import Post, db

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
        
        # Handle image upload
        image = request.files.get('image')
        image_filename = None
        
        if image:
            if image.filename == '':
                return jsonify({"message": "No selected file"}), 400
            
            if not Config.allowed_file(image.filename):
                return jsonify({"message": "File type not allowed"}), 400
            
            filename = secure_filename(image.filename)
            image_path = os.path.join(Config.UPLOAD_FOLDER, filename)
            image.save(image_path)
            
            image_filename = filename

        new_post = Post(
            content=data['content'],
            userId=userId,
            communityId=communityId,
            imageUrl=image_filename
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
            image_path = os.path.join(Config.UPLOAD_FOLDER, filename)
            image.save(image_path)
            post.imageUrl = filename  # Update imageUrl

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
