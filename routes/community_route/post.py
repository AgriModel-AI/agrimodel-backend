# from datetime import datetime
# import uuid
# from dotenv import load_dotenv
# from flask import jsonify
# from sqlalchemy import asc, desc
# from flask_restful import Resource
# from flask_jwt_extended import jwt_required, get_jwt_identity
# from flask import request
# from config import Config
# from models import Notification, Post, PostLike, User, UserCommunity, db
# from sqlalchemy.orm import selectinload
# import cloudinary.uploader
# import os

# from routes.socketio import send_notification_to_user, send_post_likes_to_users

# # Load the .env file
# load_dotenv()


# ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# user_profile = os.getenv("USER_PROFILE")

# def allowed_file(filename):
#     return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
# class PostsResource(Resource):
#     @jwt_required()
#     def get(self):
#         user_identity = get_jwt_identity()
#         userId = int(user_identity["userId"])
#         community_ids = {c[0] for c in db.session.query(UserCommunity.communityId).filter_by(userId=userId).all()}

#         if not community_ids:
#             return {"posts": []}, 200

#         # Get request parameters
#         search_query = request.args.get('search', '').strip()
#         sort_by = request.args.get('sort_by', 'createdAt')
#         sort_order = request.args.get('sort_order', 'desc')
#         limit = request.args.get('limit', type=int)
#         offset = request.args.get('offset', type=int, default=0)

#         # Base query
#         query = db.session.query(Post).filter(Post.communityId.in_(community_ids))

#         # Apply search filter (if provided)
#         if search_query:
#             query = query.filter(Post.content.ilike(f"%{search_query}%"))

#         # Apply sorting safely
#         sort_column = getattr(Post, sort_by, Post.createdAt)  # Default to createdAt
#         query = query.order_by(desc(sort_column) if sort_order == "desc" else asc(sort_column))

#         # Apply pagination
#         if limit:
#             query = query.limit(limit)
#         if offset:
#             query = query.offset(offset)

#         # Fetch posts with optimized joins
#         posts = query.options(selectinload(Post.comments), selectinload(Post.user)).all()
        
#         if not posts:
#             return {"posts": []}, 200

#         # Optimize liked post query
#         liked_post_ids = {postId for (postId,) in db.session.query(PostLike.postId).filter_by(userId=userId)}

#         # Format response
#         post_list = [
#             {
#                 "user": {
#                     "userId": post.user.userId,
#                     "names": post.user.details.names if post.user.details else post.user.username,
#                     "profilePicture": post.user.profilePicture if post.user.profilePicture else user_profile
#                 },
#                 "postId": post.postId,
#                 "content": post.content,
#                 "createdAt": post.createdAt.strftime("%Y-%m-%d %H:%M:%S"),
#                 "likes": post.likes,
#                 "isLiked": post.postId in liked_post_ids,
#                 "imageUrl": post.imageUrl,
#                 "communityId": post.communityId,
#                 "comments": [
#                     {
#                         "commentId": comment.commentId,
#                         "content": comment.content,
#                         "createdAt": comment.createdAt.strftime("%Y-%m-%d %H:%M:%S"),
#                         "userId": comment.userId,
#                         "names": comment.user.details.names if comment.user.details else comment.user.username,
#                     }
#                     for comment in post.comments
#                 ],
#             }
#             for post in posts
#         ]

#         return {"posts": post_list}, 200


# class PostListResource(Resource):
#     @jwt_required()
#     def get(self, communityId):
#         """Get a list of all posts or filter by community."""
        
#         if communityId:
#             posts = Post.query.filter_by(communityId=communityId).all()
#         else:
#             posts = Post.query.all()
        
#         return {
#             "data": [
#                 {
#                     "postId": p.postId,
#                     "content": p.content,
#                     "createdAt": p.createdAt.isoformat(),
#                     "likes": p.likes,
#                     "imageUrl": p.imageUrl,
#                     "userId": p.userId,
#                     "communityId": p.communityId
#                 } for p in posts
#             ]
#         }, 200

#     @jwt_required()
#     def post(self, communityId):
#         """Create a new post with optional image upload."""
#         user_identity = get_jwt_identity()
#         userId = int(user_identity["userId"])
        
#         data = request.form
#         if 'content' not in data or not data['content']:
#             return {"message": "Content is required."}, 400
        
#         image = request.files.get('image')
#         if not image or not allowed_file(image.filename):
#             return {"message": "A valid image file (png, jpg, jpeg, gif) is required."}, 400
            
        
#         try:
#             # Upload the file to Cloudinary
#             upload_result = cloudinary.uploader.upload(image)

#             # Get the URL of the uploaded image
#             image_url = upload_result.get('url')
#         except Exception as e:
#             return {"message": f"Image upload failed: {str(e)}"}, 404

#         new_post = Post(
#             content=data['content'],
#             userId=userId,
#             communityId=communityId,
#             imageUrl=image_url
#         )
        
#         db.session.add(new_post)
#         db.session.commit()
        
#         data = {
#                 "user": {
#                     "userId": new_post.user.userId,
#                     "names": new_post.user.details.names if new_post.user.details else new_post.user.username,
#                     "profilePicture": new_post.user.profilePicture if new_post.user.profilePicture else user_profile
#                 },
#                 "postId": new_post.postId,
#                 "content": new_post.content,
#                 "createdAt": new_post.createdAt.strftime("%Y-%m-%d %H:%M:%S"),
#                 "likes": new_post.likes,
#                 "isLiked": False,
#                 "imageUrl": new_post.imageUrl,
#                 "communityId": new_post.communityId,
#                 "comments": []
#             }
#         return {"message": "Post created successfully.", "data": data}, 201



# class PostResource(Resource):

#     @jwt_required()
#     def get(self, postId):
#         """Get a post by its ID."""
#         post = Post.query.filter_by(postId=postId).first()
        
#         if post is None:
#             return {"message": "Post not found."}, 404
        
#         return {
#             "postId": post.postId,
#             "content": post.content,
#             "createdAt": post.createdAt.isoformat(),
#             "likes": post.likes,
#             "imageUrl": post.imageUrl,
#             "userId": post.userId,
#             "communityId": post.communityId
#         }, 200
    
#     @jwt_required()
#     def put(self, postId):
#         """Update an existing post."""
#         user_identity = get_jwt_identity()
#         userId = int(user_identity["userId"])

#         post = Post.query.filter_by(postId=postId, userId=userId).first()
#         if not post:
#             return {"message": "Post not found or you are not authorized to update this post."}, 404

#         data = request.form
#         if 'content' in data and data['content']:
#             post.content = data['content']

#         # Handle image upload
#         image = request.files.get('image')
#         if image:
#             if image.filename == '':
#                 return jsonify({"message": "No selected file"}), 400
            
#             if not Config.allowed_file(image.filename):
#                 return jsonify({"message": "File type not allowed"}), 400            
            
#             try:
#             # Upload the file to Cloudinary
#                 upload_result = cloudinary.uploader.upload(image)

#                 # Get the URL of the uploaded image
#                 image_url = upload_result.get('url')
#             except Exception as e:
#                 return {"message": f"Image upload failed: {str(e)}"}, 404

#             # Delete the old image file if it exists
#             if post.imageUrl:
#                 old_image_id = post.imageUrl.split('/')[-1].split('.')[0]
#                 cloudinary.uploader.destroy(old_image_id)
                
#             post.imageUrl = image_url

#         db.session.commit()
#         data = {
#                 "postId": post.postId,
#                 "imageUrl": post.imageUrl,
#                 "content": post.content,
#             }
#         return {"message": "Post updated successfully.", "data": data}, 200

#     @jwt_required()
#     def delete(self, postId):
#         """Delete a post."""
#         user_identity = get_jwt_identity()
#         userId = int(user_identity["userId"])

#         post = Post.query.filter_by(postId=postId, userId=userId).first()
#         if not post:
#             return {"message": "Post not found or you are not authorized to delete this post."}, 404

#         if post.imageUrl:
#             old_image_id = post.imageUrl.split('/')[-1].split('.')[0]
#             cloudinary.uploader.destroy(old_image_id)
                
#         db.session.delete(post)
#         db.session.commit()
#         return {"message": "Post deleted successfully.", "data": {"postId": postId}}, 200
    

# class PostLikeResource(Resource):
#     @jwt_required()
#     def post(self, postId):
#         """Like or Unlike a post based on the like history."""

#         user_identity = get_jwt_identity()
#         userId = int(user_identity["userId"])

#         post = Post.query.get(postId)
#         if not post:
#             return {"message": "Post not found."}, 404

#         # Check if the user already liked the post
#         existing_like = PostLike.query.filter_by(postId=postId, userId=userId).first()
#         user = User.query.filter_by(userId=userId).first()

#         if existing_like:
#             # Unlike the post (remove like history entry)
#             db.session.delete(existing_like)
#             post.likes -= 1
#             action_message = f"{user.username} unliked your post: {post.content}."
#             message = "Post unliked successfully."
#         else:
#             # Like the post (add like history entry)
#             new_like = PostLike(postId=postId, userId=userId)
#             db.session.add(new_like)
#             post.likes += 1
#             action_message = f"{user.username} liked your post: {post.content}."
#             message = "Post liked successfully."
        
#         if user and post.userId != userId:    
#             # Create notification
#             notification = Notification(
#                 message=action_message,
#                 userId=post.userId,
#                 timestamp=datetime.utcnow()
#             )
#             db.session.add(notification)

#             # Send real-time notification
#             send_notification_to_user(post.userId, action_message)

#         db.session.commit()
        
#         send_post_likes_to_users({"postId": postId, "likes": post.likes, "userId": userId})
#         return {"message": message, "postId": postId, "likes": post.likes}, 200

from datetime import datetime
import uuid
import os
import logging
from dotenv import load_dotenv
from flask import jsonify
from sqlalchemy import asc, desc
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import request
from config import Config
from models import Notification, Post, PostLike, User, UserCommunity, db
from sqlalchemy.orm import selectinload
# Keep the import for future reference
import cloudinary.uploader

from routes.socketio import send_notification_to_user, send_post_likes_to_users

# Load the .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get environment variables
BACKEND_URL = os.getenv('BACKEND_URL')
if not BACKEND_URL.endswith('/'):
    BACKEND_URL += '/'
user_profile = os.getenv("USER_PROFILE")

# Set up storage directories
UPLOADS_DIR = 'static/uploads/posts'
if not os.path.exists(UPLOADS_DIR):
    try:
        os.makedirs(UPLOADS_DIR)
    except OSError as e:
        logger.error(f"Failed to create directory {UPLOADS_DIR}: {str(e)}")

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image_locally(file, community_id=None):
    """Save image to local storage and return URL"""
    if not file:
        return None
        
    # Generate unique filename
    original_filename = file.filename
    extension = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'jpg'
    unique_filename = f"{uuid.uuid4().hex}.{extension}"
    
    # Create subfolder if needed
    target_dir = UPLOADS_DIR
    if community_id:
        target_dir = os.path.join(UPLOADS_DIR, str(community_id))
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
    
    # Save file
    file_path = os.path.join(target_dir, unique_filename)
    file.save(file_path)
    
    # Create URL using BACKEND_URL
    relative_path = f"static/uploads/posts/{str(community_id) + '/' if community_id else ''}{unique_filename}"
    return f"{BACKEND_URL}{relative_path}"

def delete_image_locally(image_url):
    """Delete image from local storage"""
    if not image_url or not image_url.startswith(BACKEND_URL):
        return False
    
    try:
        # Extract the file path from the URL
        relative_path = image_url.replace(BACKEND_URL, '')
        file_path = os.path.join(os.getcwd(), relative_path)
        
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
    except Exception as e:
        logger.error(f"Failed to delete image: {str(e)}")
    
    return False

class PostsResource(Resource):
    @jwt_required()
    def get(self):
        user_identity = get_jwt_identity()
        userId = int(user_identity["userId"])
        community_ids = {c[0] for c in db.session.query(UserCommunity.communityId).filter_by(userId=userId).all()}

        if not community_ids:
            return {"posts": []}, 200

        # Get request parameters
        search_query = request.args.get('search', '').strip()
        sort_by = request.args.get('sort_by', 'createdAt')
        sort_order = request.args.get('sort_order', 'desc')
        limit = request.args.get('limit', type=int)
        offset = request.args.get('offset', type=int, default=0)

        # Base query
        query = db.session.query(Post).filter(Post.communityId.in_(community_ids))

        # Apply search filter (if provided)
        if search_query:
            query = query.filter(Post.content.ilike(f"%{search_query}%"))

        # Apply sorting safely
        sort_column = getattr(Post, sort_by, Post.createdAt)  # Default to createdAt
        query = query.order_by(desc(sort_column) if sort_order == "desc" else asc(sort_column))

        # Apply pagination
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)

        # Fetch posts with optimized joins
        posts = query.options(selectinload(Post.comments), selectinload(Post.user)).all()
        
        if not posts:
            return {"posts": []}, 200

        # Optimize liked post query
        liked_post_ids = {postId for (postId,) in db.session.query(PostLike.postId).filter_by(userId=userId)}

        # Format response
        post_list = [
            {
                "user": {
                    "userId": post.user.userId,
                    "names": post.user.details.names if post.user.details else post.user.username,
                    "profilePicture": post.user.profilePicture if post.user.profilePicture else user_profile
                },
                "postId": post.postId,
                "content": post.content,
                "createdAt": post.createdAt.strftime("%Y-%m-%d %H:%M:%S"),
                "likes": post.likes,
                "isLiked": post.postId in liked_post_ids,
                "imageUrl": post.imageUrl,
                "communityId": post.communityId,
                "comments": [
                    {
                        "commentId": comment.commentId,
                        "content": comment.content,
                        "createdAt": comment.createdAt.strftime("%Y-%m-%d %H:%M:%S"),
                        "userId": comment.userId,
                        "names": comment.user.details.names if comment.user.details else comment.user.username,
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
            
        try:
            # Save image to local storage
            image_url = save_image_locally(image, communityId)
            
            # Cloudinary upload code (commented out but preserved)
            """
            # Upload the file to Cloudinary
            upload_result = cloudinary.uploader.upload(image)
            # Get the URL of the uploaded image
            image_url = upload_result.get('url')
            """
        except Exception as e:
            logger.error(f"Image upload failed: {str(e)}")
            return {"message": f"Image upload failed: {str(e)}"}, 500

        new_post = Post(
            content=data['content'],
            userId=userId,
            communityId=communityId,
            imageUrl=image_url
        )
        
        db.session.add(new_post)
        db.session.commit()
        
        data = {
                "user": {
                    "userId": new_post.user.userId,
                    "names": new_post.user.details.names if new_post.user.details else new_post.user.username,
                    "profilePicture": new_post.user.profilePicture if new_post.user.profilePicture else user_profile
                },
                "postId": new_post.postId,
                "content": new_post.content,
                "createdAt": new_post.createdAt.strftime("%Y-%m-%d %H:%M:%S"),
                "likes": new_post.likes,
                "isLiked": False,
                "imageUrl": new_post.imageUrl,
                "communityId": new_post.communityId,
                "comments": []
            }
        return {"message": "Post created successfully.", "data": data}, 201


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
            
            try:
                # Delete the old image file if it exists
                if post.imageUrl:
                    delete_image_locally(post.imageUrl)
                    
                # Save new image to local storage
                image_url = save_image_locally(image, post.communityId)
                post.imageUrl = image_url
                
                # Cloudinary code (commented out but preserved)
                """
                # Upload the file to Cloudinary
                upload_result = cloudinary.uploader.upload(image)
                # Get the URL of the uploaded image
                image_url = upload_result.get('url')
                
                # Delete the old image file if it exists
                if post.imageUrl:
                    old_image_id = post.imageUrl.split('/')[-1].split('.')[0]
                    cloudinary.uploader.destroy(old_image_id)
                    
                post.imageUrl = image_url
                """
            except Exception as e:
                logger.error(f"Image upload failed: {str(e)}")
                return {"message": f"Image upload failed: {str(e)}"}, 500

        db.session.commit()
        data = {
                "postId": post.postId,
                "imageUrl": post.imageUrl,
                "content": post.content,
            }
        return {"message": "Post updated successfully.", "data": data}, 200

    @jwt_required()
    def delete(self, postId):
        """Delete a post."""
        user_identity = get_jwt_identity()
        userId = int(user_identity["userId"])

        post = Post.query.filter_by(postId=postId, userId=userId).first()
        if not post:
            return {"message": "Post not found or you are not authorized to delete this post."}, 404

        # Delete image if it exists
        if post.imageUrl:
            delete_image_locally(post.imageUrl)
            
            # Cloudinary deletion code (commented out but preserved)
            """
            old_image_id = post.imageUrl.split('/')[-1].split('.')[0]
            cloudinary.uploader.destroy(old_image_id)
            """
                
        db.session.delete(post)
        db.session.commit()
        return {"message": "Post deleted successfully.", "data": {"postId": postId}}, 200
    

class PostLikeResource(Resource):
    @jwt_required()
    def post(self, postId):
        """Like or Unlike a post based on the like history."""

        user_identity = get_jwt_identity()
        userId = int(user_identity["userId"])

        post = Post.query.get(postId)
        if not post:
            return {"message": "Post not found."}, 404

        # Check if the user already liked the post
        existing_like = PostLike.query.filter_by(postId=postId, userId=userId).first()
        user = User.query.filter_by(userId=userId).first()

        if existing_like:
            # Unlike the post (remove like history entry)
            db.session.delete(existing_like)
            post.likes -= 1
            action_message = f"{user.username} unliked your post: {post.content}."
            message = "Post unliked successfully."
        else:
            # Like the post (add like history entry)
            new_like = PostLike(postId=postId, userId=userId)
            db.session.add(new_like)
            post.likes += 1
            action_message = f"{user.username} liked your post: {post.content}."
            message = "Post liked successfully."
        
        if user and post.userId != userId:    
            # Create notification
            notification = Notification(
                message=action_message,
                userId=post.userId,
                timestamp=datetime.utcnow()
            )
            db.session.add(notification)

            # Send real-time notification
            send_notification_to_user(post.userId, action_message)

        db.session.commit()
        
        send_post_likes_to_users({"postId": postId, "likes": post.likes, "userId": userId})
        return {"message": message, "postId": postId, "likes": post.likes}, 200