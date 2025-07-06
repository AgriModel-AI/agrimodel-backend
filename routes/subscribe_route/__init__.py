from flask import Blueprint
from flask_restful import Api

subscriptionBlueprint = Blueprint("subscription", __name__, url_prefix="/api/v1/subscriptions")
subscriptionApi = Api(subscriptionBlueprint)


from .subscriptionPlan import SubscriptionPlanListResource, SubscriptionPlanResource
from .userSubscription import UserSubscriptionListResource, UserSubscriptionResource, UserSubscriptionsResource
from .userDailyUsage import UserDailyUsageResource

#User-Subscriptionss
subscriptionApi.add_resource(UserSubscriptionListResource, "")
subscriptionApi.add_resource(UserSubscriptionResource, "/<int:subscription_id>")
subscriptionApi.add_resource(UserSubscriptionsResource, "/user/<int:user_id>")

#Plans
subscriptionApi.add_resource(SubscriptionPlanListResource, "/plans")
subscriptionApi.add_resource(SubscriptionPlanResource, "/plans/<int:plan_id>")

# Daily Usage
subscriptionApi.add_resource(UserDailyUsageResource, "/usage")

