import os
import pathlib
import uuid
from flask_restful import Resource, abort
import requests
from config import Config
from models import User, db
from flask import current_app, jsonify, request
from flask_jwt_extended import create_access_token, create_refresh_token
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests 
from flask import redirect, request, session
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
load_dotenv()


from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests


frontend_url = os.getenv("FRONTEND_URL")
backend_url = os.getenv("BACKEND_URL")
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")
flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
    redirect_uri=f"{backend_url}api/v1/auth/callback-client"
)

class GoogleLoginResourceClient(Resource):
    def get(self):
        authorization_url, state = flow.authorization_url()
        session["state"] = state
        return redirect(authorization_url)


class CallbackResourceClient(Resource):
    
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
            google_profile_picture = idinfo.get("picture")
            
            # Find or create the user in the database
            user = User.query.filter_by(email=email).first()
            
            if not user:
                unique_filename = f"{uuid.uuid4()}_{secure_filename('google_profile.jpg')}"
                profile_image_path = os.path.join(
                    current_app.config["PROFILE_UPLOAD_FOLDER"], unique_filename
                )

                # Download the Google profile picture and save locally
                if google_profile_picture:
                    response = requests.get(google_profile_picture)
                    if response.status_code == 200:
                        with open(profile_image_path, "wb") as f:
                            f.write(response.content)

                # Assign the local URL to the user's profile picture
                profile_picture_url = f"{backend_url}api/v1/user-details/profile-image/{unique_filename}"
                
                user = User(
                    username=username,  # Ensure you are providing a username
                    email=email,
                    password=None,  # Assuming this is a Google signup, password can be None
                    phone_number=None,  # If not provided, this can also be None
                    profilePicture=profile_picture_url,
                    role="farmer",  # Set default role
                    isVerified=True,
                    googleId = google_id,
                    authProvider="google"
                )
                db.session.add(user)
                db.session.commit()
                
            if user.isBlocked:
                return redirect(f"{frontend_url}account-block")
            
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
            
            return jwt_token

        except ValueError:
            # Invalid token
            return jsonify({"message": "Invalid token"}), 400