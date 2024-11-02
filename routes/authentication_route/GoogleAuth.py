import os
import pathlib
from flask_restful import Resource, abort
import requests
from config import Config
from models import User, db
from flask import Response, json, jsonify, request
from werkzeug.security import check_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests 
from flask import redirect, request, session


from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests


client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")
flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
    redirect_uri="http://127.0.0.1:5000/api/v1/auth/callback"
)

# class GoogleLoginResource(Resource):
#     def post(self):
#         """Login for users authenticating with Google."""
        
#         if "id_token" not in request.json:
#             abort(400, message="Google ID token is required.")

#         id_token_str = request.json["id_token"]

#         try:
#             # Verify the token with Google
#             idinfo = id_token.verify_oauth2_token(id_token_str, requests.Request(), Config.GOOGLE_CLIENT_ID)
            
#             # Extract user information
#             email = idinfo.get("email")
#             username = idinfo.get("name")
#             profile_picture = idinfo.get("picture")
            
#             # Find or create the user in the database
#             user = User.query.filter_by(email=email).first()
            
#             if not user:
#                 # Sign up (create) a new user if one does not exist
#                 user = User(
#                     email=email,
#                     username=username,
#                     profilePicture=profile_picture,
#                     role="user",  # Set default role
#                     isVerified=True  # Google users are considered verified
#                 )
#                 db.session.add(user)
#                 db.session.commit()
                
#             if user.isBlocked:
#                 abort(403, message="Your account is blocked.")
            
#             # Create access and refresh tokens
#             user_identity = {
#                 "userId": user.userId,
#                 "email": user.email,
#                 "username": user.username,
#                 "role": user.role
#             }
            
#             access_token = create_access_token(identity=user_identity)
#             refresh_token = create_refresh_token(identity=user_identity)

#             return jsonify({
#                 "message": "Login/Signup successful",
#                 "access_token": access_token,
#                 "refresh_token": refresh_token,
#                 "user": user_identity
#             }), 200

#         except ValueError:
#             # Invalid token
#             return jsonify({"message": "Invalid token"}), 400



class GoogleLoginResource(Resource):
    def get(self):
        authorization_url, state = flow.authorization_url()
        session["state"] = state
        return redirect(authorization_url)
        # return Response(
        #     response=json.dumps({'auth_url':authorization_url}),
        #     status=200,
        #     mimetype='application/json'
        # )


class CallbackResource(Resource):
    def get(self):
        flow.fetch_token(authorization_response=request.url)

        if not session["state"] == request.args["state"]:
            abort(500)
        try:

            credentials = flow.credentials
            request_session = requests.session()
            cached_session = cachecontrol.CacheControl(request_session)
            token_request = google.auth.transport.requests.Request(session=cached_session)

            idinfo = id_token.verify_oauth2_token(
                id_token=credentials._id_token,
                request=token_request,
                audience=Config.GOOGLE_CLIENT_ID,
                clock_skew_in_seconds=60
            )
            
            google_id = idinfo['sub']
            
            # Extract user information
            email = idinfo.get("email")
            username = idinfo.get("name")
            profile_picture = idinfo.get("picture")
            
            # Find or create the user in the database
            user = User.query.filter_by(email=email).first()
            
            if not user:
                # Sign up (create) a new user if one does not exist
                user = User(
                    username=username,  # Ensure you are providing a username
                    email=email,
                    password=None,  # Assuming this is a Google signup, password can be None
                    phone_number=None,  # If not provided, this can also be None
                    profilePicture=profile_picture,
                    role="user",  # Set default role
                    isVerified=True,
                    googleId = google_id,
                    authProvider="google"
                )
                db.session.add(user)
                db.session.commit()
                
            if user.isBlocked:
                abort(403, message="Your account is blocked.")
            
            # Create access and refresh tokens
            user_identity = {
                "userId": user.userId,
                "email": user.email,
                "username": user.username,
                "role": user.role
            }
            print(user_identity)
            access_token = create_access_token(identity=user_identity)
            refresh_token = create_refresh_token(identity=user_identity)

            jwt_token = jsonify({
                "message": "Login/Signup successful",
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": user_identity
            })
            
            return redirect(f"http://localhost:3000/google-auth?access_token={access_token}&refresh_token={refresh_token}")

        except ValueError:
            # Invalid token
            return jsonify({"message": "Invalid token"}), 400