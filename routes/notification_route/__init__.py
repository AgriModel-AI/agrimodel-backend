from flask import Blueprint
from flask_restful import Api

notificationBlueprint = Blueprint("notification", __name__, url_prefix="/api/v1/notifications")
notificationApi = Api(notificationBlueprint)


# Import and register resources
from .notification import NotificationResource

# Add login and signup resources
notificationApi.add_resource(NotificationResource, "")