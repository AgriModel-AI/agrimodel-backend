import re
import uuid
from flask import make_response, jsonify, request
from flask_restful import Resource, reqparse, abort
from werkzeug.security import generate_password_hash
from models import User
from authentication_route import authApi

class SignupResource(Resource):
    
    def post(self):
       pass


authApi.add_resource(SignupResource, "/signup")
