from flask import Blueprint
from flask_restful import Api

modelsBlueprint = Blueprint("models", __name__, url_prefix="/api/v1/models")
modelsApi = Api(modelsBlueprint)


from .modelResource import LatestModelResource, DownloadModelResource, DownloadModelConfigResource, RateModelResource, SyncOfflineRatingsResource, AdminModelResource

modelsApi.add_resource(LatestModelResource, '/latest')
modelsApi.add_resource(DownloadModelResource, '/<string:model_id>/download')
modelsApi.add_resource(DownloadModelConfigResource, '/<string:model_id>/config')
modelsApi.add_resource(RateModelResource, '/<string:model_id>/rate')
modelsApi.add_resource(SyncOfflineRatingsResource, '/sync')
modelsApi.add_resource(AdminModelResource, '/admin')