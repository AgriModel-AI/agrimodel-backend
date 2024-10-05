import re
import uuid
from flask import Blueprint, make_response, jsonify, request
from flask_restful import Api, Resource, reqparse, abort
from models import User

verificationCodeBlueprint = Blueprint("VerificationCode", __name__, url_prefix="/api/v1/verification-code")
verificationCodeApi = Api(verificationCodeBlueprint)

class verificationCodeResource(Resource):
    
    def get(self):
       pass

    def post(self):
       pass

    def put(self):
        pass

    def patch(self):
        pass


verificationCodeApi.add_resource(verificationCodeResource, "")
