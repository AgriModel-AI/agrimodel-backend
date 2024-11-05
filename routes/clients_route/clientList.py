from flask import request, jsonify
from flask_restful import Resource, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, UserDetails

class ClientResource(Resource):
    
    @jwt_required()
    def get(self):
        """Fetch all clients with additional user details."""
        try:
            # Fetch all users with their associated details
            clients = (
                db.session.query(User, UserDetails)
                .outerjoin(UserDetails, User.userId == UserDetails.userId)
                .all()
            )

            # Prepare client data with both User and UserDetails fields
            client_data = [{
                "userId": user.userId,
                "username": user.username,
                "email": user.email,
                "phone_number": user.phone_number,
                "profilePicture": user.profilePicture,
                "role": user.role,
                "createdAt": user.createdAt.isoformat(),
                "isVerified": user.isVerified,
                "isBlocked": user.isBlocked,
                "authProvider": user.authProvider,
                # UserDetails fields
                "names": details.names if details else None,
                "national_id": details.national_id if details else None,
                "city": details.city if details else None,
                "address": details.address if details else None,
                "dob": details.dob.isoformat() if details and details.dob else None,
                "gender": details.gender if details else None
            } for user, details in clients]

            return {"data": client_data}, 200

        except Exception as e:
            abort(500, message="An error occurred while fetching clients: " + str(e))