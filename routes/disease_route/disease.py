import re
import uuid
from flask import Blueprint, make_response, jsonify, request
from flask_restful import Api, Resource, reqparse, abort
from models import User

diseaseBlueprint = Blueprint("Disease", __name__, url_prefix="/api/v1/disease")
diseaseApi = Api(diseaseBlueprint)

class diseaseResource(Resource):
    
    def get(self):
       pass

    def post(self):
       pass

    def put(self):
        pass

    def patch(self):
        pass


diseaseApi.add_resource(diseaseResource, "")
