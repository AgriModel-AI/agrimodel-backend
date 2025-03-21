from datetime import datetime
from flask import request, jsonify
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Comment, Notification, Post, User, db
from routes.socketio import send_notification_to_user, send_post_comments_to_users

class CommentResource(Resource):
    @jwt_required()
    def get(self, postId):
        """Get all comments for a specific post."""
        comments = Comment.query.filter_by(postId=postId).all()
        return {
            "data": [
                {
                    "commentId": c.commentId,
                    "content": c.content,
                    "createdAt": c.createdAt.isoformat(),
                    "postId": c.postId,
                    "userId": c.userId,
                } for c in comments
            ]
        }, 200

    @jwt_required()
    def post(self, postId):
        """Create a new comment for a specific post."""
        user_identity = get_jwt_identity()
        userId = int(user_identity["userId"])

        data = request.json
        if 'content' not in data or not data['content']:
            return {"message": "Content is required."}, 400
        
        post = Post.query.filter_by(postId=postId).first()
        if not post:
            return {"message": "Post not found."}, 404

        new_comment = Comment(
            content=data['content'],
            postId=postId,
            userId=userId
        )

        db.session.add(new_comment)
        
        user = User.query.filter_by(userId=userId).first()
        
        if user and post.userId != userId:  # Avoid sending a notification if the user comments on their own post
            notification_message = f"{user.username} commented on your post."
            notification = Notification(
                message=notification_message,
                userId=post.userId,
                timestamp=datetime.utcnow()
            )
            db.session.add(notification)
            send_notification_to_user(post.userId, notification_message)
            
        db.session.commit()
        
        data = {"commentId": new_comment.commentId, "content": new_comment.content, "createdAt": new_comment.createdAt.strftime("%Y-%m-%d %H:%M:%S"), "postId": new_comment.postId, "userId": new_comment.userId, "names": new_comment.user.details.names if new_comment.user.details else new_comment.user.username }
        
        send_post_comments_to_users(data)        
        return {"message": "Comment created successfully.", "data": data}, 201
    

class CommentListResource(Resource):
    @jwt_required()
    def put(self, commentId):
        """Update an existing comment."""
        data = request.json
        comment = Comment.query.get(commentId)
        
        if not comment:
            return {"message": "Comment not found."}, 404

        if 'content' in data and data['content']:
            comment.content = data['content']
        
        db.session.commit()
        return {"message": "Comment updated successfully."}, 200

    @jwt_required()
    def delete(self, commentId):
        """Delete a comment."""
        comment = Comment.query.get(commentId)
        
        if not comment:
            return {"message": "Comment not found."}, 404

        db.session.delete(comment)
        db.session.commit()
        return {"message": "Comment deleted successfully."}, 200
