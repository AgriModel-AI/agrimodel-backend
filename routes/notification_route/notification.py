from datetime import datetime, timedelta
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Notification, db

class NotificationResource(Resource):
    @jwt_required()
    def get(self):
        """Fetch notifications for the logged-in user:
           - Include all unread notifications.
           - Include read notifications from the last month.
        """
        user_identity = get_jwt_identity()
        userId = int(user_identity["userId"])

        # Calculate the date one month ago
        one_month_ago = datetime.utcnow() - timedelta(days=30)

        # Fetch unread notifications and read notifications within the last month
        notifications = Notification.query.filter(
            (Notification.userId == userId) & (
                (Notification.isRead == False) |
                (Notification.isRead == True) & (Notification.timestamp >= one_month_ago)
            )
        ).order_by(Notification.timestamp.desc()).all()

        # Serialize the notifications
        serialized_notifications = [
            {
                "notificationId": notification.notificationId,
                "message": notification.message,
                "timestamp": notification.timestamp.isoformat(),
                "isRead": notification.isRead
            }
            for notification in notifications
        ]

        return {"data": serialized_notifications}, 200

    @jwt_required()
    def patch(self):
        """Mark all notifications as read for the logged-in user."""
        user_identity = get_jwt_identity()
        userId = int(user_identity["userId"])

        # Update unread notifications for the user to mark them as read
        updated_count = Notification.query.filter_by(userId=userId, isRead=False).update({"isRead": True})
        db.session.commit()

        if updated_count == 0:
            return {"message": "No unread notifications found."}, 200

        return {"message": f"{updated_count} notifications marked as read."}, 200
