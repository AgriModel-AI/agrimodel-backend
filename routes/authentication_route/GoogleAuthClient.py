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
        print(request.url)
        print(request.args)
        print(request)
        user_identity = {
            "userId": "abd",
            "email": "abd",
            "username":" user.username",
            "role": "user.role"
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

        # except ValueError:
        #     # Invalid token
        #     return jsonify({"message": "Invalid token"}), 400