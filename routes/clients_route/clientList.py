from flask_restful import Resource, abort
from flask_jwt_extended import jwt_required
from models import db, User, UserDetails, District, Province

class ClientResource(Resource):
    
    @jwt_required()
    def get(self):
        """Fetch all clients with additional user details."""
        try:
            # Explicitly select the required fields and join with Province
            clients = (
                db.session.query(User, UserDetails, District, Province)
                .outerjoin(UserDetails, User.userId == UserDetails.userId)
                .outerjoin(District, District.districtId == UserDetails.districtId)
                .outerjoin(Province, Province.provinceId == District.provinceId)
                .all()
            )

            # Prepare client data with User, UserDetails, District, and Province fields
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
                "district": {
                    "provinceName": province.name if province else None,
                    "districtName": district.name if district else None,
                } if district else None,
                "address": details.address if details else None,
                "dob": details.dob.isoformat() if details and details.dob else None,
                "gender": details.gender if details else None
            } for user, details, district, province in clients]

            return {"data": client_data}, 200

        except Exception as e:
            abort(500, message="An error occurred while fetching clients: " + str(e))
