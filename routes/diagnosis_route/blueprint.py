from flask import Blueprint
from flask_restful import Api

diagnosisBlueprint = Blueprint("Diagnosis", __name__, url_prefix="/api/v1/diagnosis")
diagnosisApi = Api(diagnosisBlueprint)