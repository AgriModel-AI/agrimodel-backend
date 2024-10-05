from flask import Blueprint
from flask_restful import Api

communityBlueprint = Blueprint("Community", __name__, url_prefix="/api/v1/community")
communityApi = Api(communityBlueprint)