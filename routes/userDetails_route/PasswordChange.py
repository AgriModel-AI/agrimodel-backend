import re
from flask import request
from flask_restful import Resource, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash, generate_password_hash
from models import User, db

class PasswordChangeResource(Resource):
    @jwt_required()
    def post(self):
        """Change user password."""
        # Extract user ID from JWT token
        user_identity = get_jwt_identity()
        userId = int(user_identity["userId"])

        # Fetch user from the database
        user = User.query.get(userId)
        if not user:
            abort(404, message="User not found.")

        # Extract request data
        data = request.json

        # Required fields
        required_fields = ["current_password", "new_password", "confirm_password"]
        for field in required_fields:
            if field not in data or not data[field].strip():
                abort(400, description=f"Field '{field}' is required and cannot be empty.")

        current_password = data["current_password"]
        new_password = data["new_password"]
        confirm_password = data["confirm_password"]

        # Validate current password
        if not check_password_hash(user.password, current_password):
            abort(400, description="Current password is incorrect.")

        # Validate new password length
        if len(new_password) < 8:
            abort(400, description="New password must be at least 8 characters long.")

        # Validate new password format (example: must include letters and numbers)
        if not re.search(r"[A-Za-z]", new_password) or not re.search(r"[0-9]", new_password):
            abort(400, description="New password must contain both letters and numbers.")

        # Check if new password and confirm password match
        if new_password != confirm_password:
            abort(400, description="New password and confirm password do not match.")

        try:
            # Hash the new password
            hashed_password = generate_password_hash(new_password)

            # Update user's password in the database
            user.password = hashed_password
            db.session.commit()

            return {"message": "Password updated successfully."}, 200

        except Exception as e:
            abort(500, description="An error occurred while updating the password. Please try again later.")
