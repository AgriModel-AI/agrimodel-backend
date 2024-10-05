import re
import uuid
from flask import make_response, jsonify, request
from flask_restful import Resource, reqparse, abort
from models import User
from diagnosis_route import diagnosisApi

class communityResource(Resource):
    
    def get(self):
       pass

    def post(self):
       pass

    def put(self):
        pass

    def patch(self):
        pass


diagnosisApi.add_resource(communityResource, "/diagnosis-result")
