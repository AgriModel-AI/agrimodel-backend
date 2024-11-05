from flask import request, jsonify
from flask_restful import Resource, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, UserDetails

class ClientPatchResource(Resource):

    @jwt_required()
    def patch(self, user_id):
        """Update client account status (block/unblock)."""
        is_blocked = request.json.get("isBlocked")

        if user_id is None or is_blocked is None:
            abort(400, message="userId and isBlocked fields are required.")

        client = User.query.get(user_id)
        if not client:
            return {"message": "Client not found."}, 404

        try:
            # Update the isBlocked status
            client.isBlocked = is_blocked
            db.session.commit()

            action = "blocked" if is_blocked else "unblocked"
            return {
                "message": f"Client has been {action} successfully.",
                "userId": client.userId,
                "isBlocked": client.isBlocked
            }, 200

        except Exception as e:
            db.session.rollback()
            abort(500, message="An error occurred while updating client status: " + str(e))
