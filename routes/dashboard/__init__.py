from flask import Blueprint
from flask_restful import Api

dashboardBlueprint = Blueprint("dashboard", __name__, url_prefix="/api/v1/dashboard")
dashboardApi = Api(dashboardBlueprint)


# Import and register resources
from .Province import ProvinceResource
from .DashboardStats import DashboardStatsResource


# Add login and signup resources
dashboardApi.add_resource(DashboardStatsResource, "/stats")
dashboardApi.add_resource(ProvinceResource, "/provinces")