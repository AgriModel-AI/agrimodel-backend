import os
import pathlib
from flask_restful import Resource, abort
import requests
from config import Config
from models import User
from flask import redirect, request, session
from werkzeug.security import check_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required


class LoginResource(Resource):
    def post(self):
        """Standard login for users who registered with email and password."""
        
        required_fields = ["email", "password"]
        for field in required_fields:
            if field not in request.json:
                abort(400, message=f"Field '{field}' is required.")

        email = request.json["email"]
        password = request.json["password"]

        # Fetch the user based on the provided email and ensure it's a local login
        user = User.query.filter_by(email=email).first()
        
        if not user:
            abort(400, message="Invalid credentials: user not found.")
        
        # Check if the user registered with Google auth
        if user.authProvider == "google":
            abort(400, message="This email is linked with Google. Please log in via Google authentication.")
        
        if not user:
            abort(400, message="Invalid credentials: user not found or not registered locally.")
        
        # Check password validity
        if not check_password_hash(user.password, password):
            abort(400, message="Invalid credentials: password is incorrect.")

        # Check if the user is verified and not blocked
        if not user.isVerified:
            return {
                "message": "Your account is not verified.",
                "verification_required": True
            }, 403

        if user.isBlocked:
            abort(403, message="Your account is blocked.")
            
        if user.role == "farmer":
            abort(403, message="Farmer accounts are not allowed to log in.")

        # Generate JWT tokens with user identity
        user_identity = {
            "userId": user.userId,
            "email": user.email,
            "username": user.username,
            "role": user.role
        }

        access_token = create_access_token(identity=user_identity)
        refresh_token = create_refresh_token(identity=user_identity)

        return {
            "message": "Login successful.",
            "access_token": access_token,
            "refresh_token": refresh_token
        }, 200
        

class LoginClientResource(Resource):
    def post(self):
        """Standard login for users who registered with email and password."""
        
        required_fields = ["email", "password"]
        for field in required_fields:
            if field not in request.json:
                abort(400, message=f"Field '{field}' is required.")

        email = request.json["email"]
        password = request.json["password"]

        # Fetch the user based on the provided email and ensure it's a local login
        user = User.query.filter_by(email=email).first()
        
        if not user:
            abort(400, message="Invalid credentials: user not found.")
        
        # Check if the user registered with Google auth
        if user.authProvider == "google":
            abort(400, message="This email is linked with Google. Please log in via Google authentication.")
        
        if not user:
            abort(400, message="Invalid credentials: user not found or not registered locally.")
        
        # Check password validity
        if not check_password_hash(user.password, password):
            abort(400, message="Invalid credentials: password is incorrect.")

        # Check if the user is verified and not blocked
        if not user.isVerified:
            return {
                "message": "Your account is not verified.",
                "verification_required": True
            }, 403

        if user.isBlocked:
            abort(403, message="Your account is blocked.")

        # Generate JWT tokens with user identity
        user_identity = {
            "userId": user.userId,
            "email": user.email,
            "username": user.username,
            "role": user.role
        }

        access_token = create_access_token(identity=user_identity)
        refresh_token = create_refresh_token(identity=user_identity)

        return {
            "message": "Login successful.",
            "access_token": access_token,
            "refresh_token": refresh_token
        }, 200
        
class RefreshTokenResource(Resource):
    @jwt_required(refresh=True)
    def post(self):
        """Generate a new access token and refresh token using a valid refresh token."""
        current_user = get_jwt_identity()

        new_access_token = create_access_token(identity=current_user)
        new_refresh_token = create_refresh_token(identity=current_user)

        return {
            "message": "Access token refreshed successfully.",
            "access_token": new_access_token,
            "refresh_token": new_refresh_token
        }, 200