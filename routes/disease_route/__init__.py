from flask import Blueprint
from flask_restful import Api

diseaseBlueprint = Blueprint("disease", __name__, url_prefix="/api/v1/disease")
diseaseApi = Api(diseaseBlueprint)


# Import and register resources
from .disease import DiseaseResource
from .DiseaseSingleImageResource import DiseaseSingleImageResource

# Add login and signup resources
diseaseApi.add_resource(DiseaseResource, "")
diseaseApi.add_resource(DiseaseSingleImageResource, "/image/<string:filename>")