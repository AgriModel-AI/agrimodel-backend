from flask import Blueprint
from flask_restful import Api

userDetailsBlueprint = Blueprint("userDetails", __name__, url_prefix="/api/v1/user-details")
userDetailsApi = Api(userDetailsBlueprint)


# Import and register resources
from .userDetails import UserDetailsResource

# Add login and signup resources
userDetailsApi.add_resource(UserDetailsResource, "")