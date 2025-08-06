from flask import Blueprint
from flask_restful import Api

dashboardBlueprint = Blueprint("dashboard", __name__, url_prefix="/api/v1/dashboard")
dashboardApi = Api(dashboardBlueprint)


# Import and register resources
from .Province import ProvinceResource
from .DashboardStats import DashboardStatsResource
from .Analysis import DiseaseSummaryResource, DiseaseTrendResource, ProvinceDignosisSummaryResource, RecentActivityResource
from .Report import ReportsResource 
from .Report1 import ReportResource as ReportJ 


# Add login and signup resources
dashboardApi.add_resource(DashboardStatsResource, "/stats")
dashboardApi.add_resource(ProvinceResource, "/provinces")
dashboardApi.add_resource(DiseaseTrendResource, '/analytics/disease-trend')
dashboardApi.add_resource(DiseaseSummaryResource, '/analytics/disease-summary')
dashboardApi.add_resource(ReportsResource, '/reports/<string:report_type>')
dashboardApi.add_resource(RecentActivityResource, '/activity/recent')
dashboardApi.add_resource(ProvinceDignosisSummaryResource, '/analytics/province-summary')
dashboardApi.add_resource(ReportJ, '/reportss', '/reportss/<string:report_type>')