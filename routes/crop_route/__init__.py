from flask import Blueprint
from flask_restful import Api

cropBlueprint = Blueprint("crop", __name__, url_prefix="/api/v1/crop")
cropApi = Api(cropBlueprint)


# Import and register resources
from .crop import CropResource

# Add login and signup resources
cropApi.add_resource(CropResource, "")