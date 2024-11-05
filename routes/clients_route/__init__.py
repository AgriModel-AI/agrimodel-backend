from flask import Blueprint
from flask_restful import Api

clientsBlueprint = Blueprint("clients", __name__, url_prefix="/api/v1/clients")
clientsApi = Api(clientsBlueprint)


# Import and register resources
from .clientList import ClientResource
from .clientPatch import ClientPatchResource


# Add login and signup resources
clientsApi.add_resource(ClientResource, "")
clientsApi.add_resource(ClientPatchResource, "/<int:user_id>")