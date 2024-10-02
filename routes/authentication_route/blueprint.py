from flask import Blueprint
from flask_restful import Api

authBlueprint = Blueprint("Auth", __name__, url_prefix="/api/v1/auth")
authApi = Api(authBlueprint)