from flask_restful import Resource, abort
from models import User
from flask import request
from werkzeug.security import check_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token

class LoginResource(Resource):

    def post(self):
        """Function to log in the user and return JWT tokens."""
        
        required_fields = ["email", "password"]
        for field in required_fields:
            if field not in request.json:
                abort(400, message=f"Field '{field}' is required.")

        email = request.json["email"]
        password = request.json["password"]

        # Fetch the user based on the provided email
        user = User.query.filter_by(email=email).first()
        
        if not user:
            abort(400, message="Invalid credentials: user not found.")
        
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

        # Generate JWT tokens
        access_token = create_access_token(identity=user.userId)
        refresh_token = create_refresh_token(identity=user.userId)

        return {
            "message": "Login successful.",
            "access_token": access_token,
            "refresh_token": refresh_token
        }, 200
