from flask import Blueprint
from flask_restful import Api

exploreBlueprint = Blueprint("explore", __name__, url_prefix="/api/v1/explore")
exploreApi = Api(exploreBlueprint)


# Import and register resources
from .Explore import ExploreListResource, ExploreResource

exploreApi.add_resource(ExploreListResource, '')
exploreApi.add_resource(ExploreResource, '/<int:exploreId>')
