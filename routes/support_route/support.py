from datetime import datetime
from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource
from models import Notification, SupportRequest, db, User, SupportRequestStatus, SupportRequestType
from flask_socketio import emit
from routes import mail
from flask_mail import Message

from routes import send_notification_to_user

class SupportResource(Resource):
    @jwt_required()
    def post(self):
        user_identity = get_jwt_identity()
        user_id = int(user_identity["userId"])  

        # Get the request data
        data = request.get_json()
        subject = data.get('subject')
        description = data.get('description')
        request_type = data.get('type')

        # Validate required fields
        if not subject or not description or not request_type:
            return {"message": "All fields (subject, description, type) are required."}, 400

        # Map user-friendly request type to Enum key
        type_mapping = {
            'Technical Issue': 'TECHNICAL',
            'Prediction Issue': 'PREDICTION_ISSUE',
            'Usage Help': 'USAGE_HELP',
            'Feedback or Suggestions': 'FEEDBACK',
            'Other': 'OTHER'
        }

        # Get the corresponding Enum key
        enum_key = type_mapping.get(request_type)
        if not enum_key:
            return {"message": "Invalid support request type provided."}, 400
        
        try:
            # Create a new support request entry
            support_request = SupportRequest(
                userId=user_id,
                subject=subject,
                description=description,
                type=SupportRequestType[enum_key],
                status=SupportRequestStatus.PENDING,
                createdAt=datetime.utcnow(),
                updatedAt=datetime.utcnow()
            )
            db.session.add(support_request)
            db.session.commit()
            
            # Get all users with role 'admin'
            admin_users = User.query.filter_by(role='admin').all()

            # Create notifications for each admin user
            for admin in admin_users:
                notification = Notification(
                    message=f"New support request from User ID {user_id}: {subject}",
                    userId=admin.userId,
                    timestamp=datetime.utcnow()
                )
                db.session.add(notification)
                send_notification_to_user(admin.userId, "New support request notification")

            db.session.commit()

            

            return {"message": "Support request created successfully and notifications sent."}, 201

        except Exception as e:
            db.session.rollback()
            return {"message": str(e)}, 500
    
    @jwt_required()
    def get(self):
        try:
            # Get all support requests
            support_requests = SupportRequest.query.all()
            response = [
                {
                "requestId": request.requestId,
                "user": {
                    "userId": request.user.userId,
                    "username": request.user.username,
                    "email": request.user.email,
                    "role": request.user.role,
                    "isVerified": request.user.isVerified,
                    "profilePicture": request.user.profilePicture,
                    # Add more fields as necessary
                },
                "subject": request.subject,
                "description": request.description,
                "type": request.type.value,
                "status": request.status.value,
                "createdAt": request.createdAt.isoformat(),  # Convert datetime to string
                "updatedAt": request.updatedAt.isoformat() if request.updatedAt else None  # Handle possible None value
                }
                for request in support_requests
            ]
            return {"data": response}, 200

        except Exception as e:
            return {"message": str(e)}, 500


    @jwt_required()
    def patch(self):
        support_request_id = request.args.get('id')
        if not support_request_id:
            return {"message": "Support request ID is required."}, 400

        data = request.get_json()
        new_status = data.get('status')
        if not new_status:
            return {"message": "Status is required."}, 400
        status_enum = None

        # Additional fields for "CLOSED" status
        title = data.get('title')
        description = data.get('description')

        if new_status:
            try:
                status_enum = SupportRequestStatus[new_status.upper()]
            except KeyError:
                return {"message": "Invalid status value provided."}, 400

        try:
            support_request = SupportRequest.query.get(support_request_id)
            if not support_request:
                return {"message": "Support request not found."}, 404

            user = User.query.get(support_request.userId)
            if not user:
                return {"message": "Associated user not found."}, 404

            if status_enum:
                support_request.status = status_enum
                support_request.updatedAt = datetime.utcnow()

                # Send email and in-app notification based on the status
                if status_enum != SupportRequestStatus.CLOSED:
                    send_email_notification(user.email, status_enum)
                    send_notification_to_user(user.userId, f"Your support request status has been updated to {status_enum.value}.")

                elif status_enum == SupportRequestStatus.CLOSED:
                    if not title or not description:
                        return {"message": "Title and description are required for closing a request."}, 400

                    # Send a detailed email for the "CLOSED" status
                    send_email_notification(user.email, status_enum, title, description)
                    send_notification_to_user(user.userId, "Your support request has been closed. Check your email for more details.")

                notification = Notification(
                    message=f"Support Request With ID: {support_request_id}, Status Updated: {status_enum}",
                    userId=user.userId,
                    timestamp=datetime.utcnow()
                )
                db.session.add(notification)
                db.session.commit()
            return {"message": "Support request updated successfully."}, 200

        except Exception as e:
            db.session.rollback()
            return {"message": str(e)}, 500

# Helper function to send an email notification
def send_email_notification(email, status, title=None, description=None):
    if status == SupportRequestStatus.CLOSED:
        msg = Message(
            subject="Support Request Closed",
            recipients=[email],
            body=f"Your support request has been closed.\n\nTitle: {title}\nDescription: {description}"
        )
    else:
        msg = Message(
            subject=f"Support Request Status Updated: {status.value}",
            recipients=[email],
            body=f"Your support request status has been updated to {status.value}."
        )
    mail.send(msg)


        
