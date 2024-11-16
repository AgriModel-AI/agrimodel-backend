from flask import request
from flask_restful import Resource, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User, db

class BlockAccountResource(Resource):
    @jwt_required()
    def patch(self):
        """Block or unblock a user account."""
        # Extract user ID from JWT token
        user_identity = get_jwt_identity()
        
        data = request.json
        target_user_id = user_identity["userId"]
        is_blocked = data.get("isBlocked")

        if is_blocked is None:
            abort(400, description="'isBlocked' field is required.")

        # Validate that the target user exists
        target_user = User.query.get(target_user_id)
        if not target_user:
            abort(404, description="User not found.")


        try:
            # Update the user's isBlocked status
            target_user.isBlocked = bool(is_blocked)
            db.session.commit()

            action = "blocked" if target_user.isBlocked else "unblocked"
            return {"message": f"User account successfully {action}."}, 200

        except Exception as e:
            abort(500, description="An error occurred while updating the account status. Please try again later.")
