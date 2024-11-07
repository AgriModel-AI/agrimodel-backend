from flask import Blueprint
from flask_restful import Api

supportBlueprint = Blueprint("support", __name__, url_prefix="/api/v1/support")
supportApi = Api(supportBlueprint)


from .support import SupportResource


supportApi.add_resource(SupportResource, "")