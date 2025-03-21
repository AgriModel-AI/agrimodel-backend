from flask import Blueprint
from flask_restful import Api

userDetailsBlueprint = Blueprint("userDetails", __name__, url_prefix="/api/v1/user-details")
userDetailsApi = Api(userDetailsBlueprint)


# Import and register resources
from .userDetails import UserDetailsResource, UserDetailsDistrictResource
from .PasswordChange import PasswordChangeResource
from .BlockAccountResource import BlockAccountResource

# Add login and signup resources
userDetailsApi.add_resource(UserDetailsResource, "")
userDetailsApi.add_resource(UserDetailsDistrictResource, "/district")
userDetailsApi.add_resource(PasswordChangeResource, "/password-change")
userDetailsApi.add_resource(BlockAccountResource, "/block-account")