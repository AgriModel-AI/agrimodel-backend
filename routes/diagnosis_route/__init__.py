from flask import Blueprint
from flask_restful import Api

diagnosisBlueprint = Blueprint("diagnosis", __name__, url_prefix="/api/v1/diagnosis-result")
diagnosisApi = Api(diagnosisBlueprint)


# Import and register resources
from .diagnosisResult import DiagnosisResultResource
from .diagnosisImageResource import DiagnosisImageResource

# Add login and signup resources
diagnosisApi.add_resource(DiagnosisResultResource, "")
diagnosisApi.add_resource(DiagnosisImageResource, "/image/<string:filename>")