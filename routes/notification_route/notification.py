import re
import uuid
from flask import Blueprint, make_response, jsonify, request
from flask_restful import Api, Resource, reqparse, abort
from models import User

notificationBlueprint = Blueprint("Notification", __name__, url_prefix="/api/v1/notification")
notificationApi = Api(notificationBlueprint)

class notificationResource(Resource):
    
    def get(self):
       pass

    def post(self):
       pass

    def put(self):
        pass

    def patch(self):
        pass


notificationApi.add_resource(notificationResource, "")
