from datetime import datetime
from flask import abort, request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import UserDetails, db, User

class UserDetailsResource(Resource):

    @jwt_required()
    def get(self):
        """Get user details for the authenticated user."""
        user_identity = get_jwt_identity()

        # Assuming user_identity is an integer or dict with userId
        userId = int(user_identity["userId"]) if isinstance(user_identity, dict) else user_identity

        # Fetch user details based on userId
        result = (
            db.session.query(User, UserDetails)
            .outerjoin(UserDetails, User.userId == UserDetails.userId)
            .filter(User.userId == userId)
            .first()
        )

        # Check if the user exists
        if not result:
            return {"message": "User not found."}, 404

        user, user_details = result

        # Convert date of birth (dob) to string (ISO format) if present
        dob_str = user_details.dob.isoformat() if user_details and user_details.dob else None

        return {
            "userId": user.userId,
            "username": user.username,
            "email": user.email,
            "phone_number": user.phone_number,
            "profilePicture": user.profilePicture,
            "role": user.role,
            "names": user_details.names if user_details else None,
            "national_id": user_details.national_id if user_details else None,
            "city": user_details.city if user_details else None,
            "address": user_details.address if user_details else None,
            "dob": dob_str,
            "gender": user_details.gender if user_details else None
        }, 200


    @jwt_required()
    def post(self):
        """Create user details for the authenticated user with validation."""
        user_identity = get_jwt_identity()  # Extract userId from JWT
        userId = int(user_identity["userId"])

        if UserDetails.query.filter_by(userId=userId).first():
            return {"message": "User details already exist."}, 400

        data = request.json
        
        # Validate required fields
        required_fields = ["names", "national_id"]
        for field in required_fields:
            if field not in data or not data[field].strip():
                abort(400, message=f"Field '{field}' is required and cannot be empty.")

        # Validate names (string and length)
        names = data["names"]
        if not isinstance(names, str) or len(names) < 2:
            abort(400, message="Invalid 'names': must be a string with at least 2 characters.")

        # Validate national_id (string and unique)
        national_id = data["national_id"]
        if not isinstance(national_id, str) or len(national_id) < 10:
            abort(400, message="Invalid 'national_id': must be a string with at least 10 characters.")
        if UserDetails.query.filter_by(national_id=national_id).first():
            abort(400, message="The provided national ID already exists.")

        # Optional fields validation
        city = data.get("city")
        if city and not isinstance(city, str):
            abort(400, message="Invalid 'city': must be a string.")

        address = data.get("address")
        if address and not isinstance(address, str):
            abort(400, message="Invalid 'address': must be a string.")

        # Validate dob (date)
        dob = data.get("dob")
        if dob:
            try:
                dob = datetime.strptime(dob, "%Y-%m-%d").date()
            except ValueError:
                abort(400, message="Invalid 'dob': must be in 'YYYY-MM-DD' format.")

        # Validate gender (optional but must be either 'Male', 'Female', or others)
        gender = data.get("gender")
        if gender and gender not in ["Male", "Female", "Other"]:
            abort(400, message="Invalid 'gender': must be 'Male', 'Female', or 'Other'.")

        # Create and save user details
        try:
            user_details = UserDetails(
                userId=userId,
                names=names,
                national_id=national_id,
                city=city,
                address=address,
                dob=dob,
                gender=gender
            )
            db.session.add(user_details)
            db.session.commit()

            return {"message": "User details created successfully."}, 201

        except Exception as e:
            abort(500, message=str(e))

    
    @jwt_required()
    def patch(self):
        """Update user details for the authenticated user with validation."""
        user_identity = get_jwt_identity()  # Extract userId from JWT
        userId = int(user_identity['userId'])
        
        user_details = UserDetails.query.filter_by(userId=userId).first()

        if not user_details:
            return {"message": "User details not found."}, 404

        data = request.json

        # Validate fields before updating
        if "names" in data:
            names = data['names']
            if not isinstance(names, str) or len(names) < 2:
                abort(400, description="Invalid 'names': must be a string with at least 2 characters.")
            user_details.names = names

        if "national_id" in data:
            national_id = data['national_id']
            if not isinstance(national_id, str) or len(national_id) < 10:
                abort(400, description="Invalid 'national_id': must be a string with at least 10 characters.")
            user_details.national_id = national_id

        if "city" in data:
            city = data['city']
            if city and not isinstance(city, str):
                abort(400, description="Invalid 'city': must be a string.")
            user_details.city = city

        if "address" in data:
            address = data['address']
            if address and not isinstance(address, str):
                abort(400, description="Invalid 'address': must be a string.")
            user_details.address = address

        if "dob" in data:
            dob = data.get("dob")
            if dob:
                try:
                    dob = datetime.strptime(dob, "%Y-%m-%d").date()
                except ValueError:
                    abort(400, description="Invalid 'dob': must be in 'YYYY-MM-DD' format.")
                user_details.dob = dob

        if "gender" in data:
            gender = data['gender']
            if gender and gender not in ["Male", "Female", "Other"]:
                abort(400, description="Invalid 'gender': must be 'Male', 'Female', or 'Other'.")
            user_details.gender = gender
        
        # Commit the updates
        db.session.commit()

        return {"message": "User details updated successfully."}, 200