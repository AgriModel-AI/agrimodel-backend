import re
import uuid
from flask import make_response, jsonify, request
from flask_restful import Resource, reqparse, abort
from werkzeug.security import check_password_hash
from flask_jwt_extended import create_refresh_token, create_access_token
from models import User
from authentication_route import authApi

class passwordResetResource(Resource):
    
    def post(self):
       pass


authApi.add_resource(passwordResetResource, "/password-reset")
