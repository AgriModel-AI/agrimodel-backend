from flask import Blueprint
from flask_restful import Api

communityBlueprint = Blueprint("Community", __name__, url_prefix="/api/v1/communities")
communityApi = Api(communityBlueprint)


# Import and register resources
from .community import CommunityListResource, CommunityResource, CommunityImageResource
from .post import PostListResource, PostResource, PostLikeResource
from .comment import CommentResource, CommentListResource
from .userCommunity import UserCommunityResource


# Add login and signup resources
communityApi.add_resource(CommunityListResource, "")
communityApi.add_resource(UserCommunityResource, "/user-community/<int:communityId>")
communityApi.add_resource(CommunityResource, '/<int:communityId>')
communityApi.add_resource(CommunityImageResource, '/<int:communityId>/image')
communityApi.add_resource(PostListResource, '/<int:communityId>/post')
communityApi.add_resource(PostResource, '/post/<int:postId>')
communityApi.add_resource(PostLikeResource, '/post/<int:postId>/like')
communityApi.add_resource(CommentResource, '/post/<int:postId>/comment')
communityApi.add_resource(CommentListResource, '/post/comment/<int:commentId>')