from flask import Blueprint
from flask_restful import Api

predictBlueprint = Blueprint("predict", __name__, url_prefix="/api/v1/predict")
predictApi = Api(predictBlueprint)


# Import and register resources
from .prediction import PredictionResource

# Add login and signup resources
predictApi.add_resource(PredictionResource, "")