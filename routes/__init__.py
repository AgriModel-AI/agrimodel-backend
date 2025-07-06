from .mail import mail
from .socketio import socketio, send_notification_to_user
from .authentication_route import authBlueprint
from .community_route import communityBlueprint
from .diagnosis_route import diagnosisBlueprint
from .disease_route import diseaseBlueprint
from .userDetails_route import userDetailsBlueprint
from .community_route import communityBlueprint
from .clients_route import clientsBlueprint
from .support_route import supportBlueprint
from .dashboard import dashboardBlueprint
from .notification_route import notificationBlueprint
# from .subscribe_route import subscriptionBlueprint
from .crop_route import cropBlueprint
from .prediction_route import predictBlueprint
from .explore_route import exploreBlueprint