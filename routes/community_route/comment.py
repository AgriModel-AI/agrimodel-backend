import re
import uuid
from flask import make_response, jsonify, request
from flask_restful import Resource, reqparse, abort
from models import User
from community_route import communityApi

class commentResource(Resource):
    
    def get(self):
       pass

    def post(self):
       pass

    def put(self):
        pass

    def patch(self):
        pass


communityApi.add_resource(commentResource, "/comment")
