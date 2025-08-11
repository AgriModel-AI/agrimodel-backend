from datetime import datetime
import re
from dotenv import load_dotenv
from flask import abort, request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import Null
from models import UserDetails, db, User, District
import cloudinary.uploader
import os

# Load the .env file
load_dotenv()

 
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

user_profile = os.getenv("USER_PROFILE")

# Utility function to check if a file is an allowed image type
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Helper validation functions
def validate_required_field(value, field_name):
    if not value or not value.strip():
        abort(400, message=f"{field_name} is required.")

def validate_min_length(value, field_name, min_length):
    if len(value.strip()) < min_length:
        abort(400, message=f"{field_name} must be at least {min_length} characters long.")
        
class UserDetailsResource(Resource):

    @jwt_required()
    def get(self):
        """Get user details for the authenticated user."""
        user_identity = get_jwt_identity()

        # Assuming user_identity is an integer or dict with userId
        userId = int(user_identity["userId"]) if isinstance(user_identity, dict) else user_identity

        # Fetch user details based on userId
        result = (
            db.session.query(User, UserDetails, District)
            .outerjoin(UserDetails, User.userId == UserDetails.userId)
            .outerjoin(District, UserDetails.districtId == District.districtId)
            .filter(User.userId == userId)
            .first()
        )

        # Check if the user exists
        if not result:
            return {"message": "User not found."}, 404

        user, user_details, district = result

        # Convert date of birth (dob) to string (ISO format) if present
        dob_str = user_details.dob.isoformat() if user_details and user_details.dob else None

        # Construct district object if available
        district_obj = {
            "id": district.districtId,
            "provinceId": district.provinceId,
            "name": district.name
        } if district else None

        return {
            "userId": user.userId,
            "username": user.username,
            "email": user.email,
            "phone_number": user.phone_number,
            "profilePicture": user.profilePicture if user.profilePicture else user_profile,
            "role": user.role,
            "names": user_details.names if user_details else user.username,
            "national_id": user_details.national_id if user_details else None,
            "district": district_obj,
            "address": user_details.address if user_details else None,
            "dob": dob_str,
            "gender": user_details.gender if user_details else None
        }, 200

    @jwt_required()
    def post(self):
        """Create or update user details for the authenticated user."""
        user_identity = get_jwt_identity()  # Extract userId from JWT
        userId = int(user_identity["userId"])

        # Check if user details already exist
        user_details = UserDetails.query.filter_by(userId=userId).first()
        user = User.query.get(userId)

        if not user:
            return {"message": "User not found."}, 404

        data = request.form  # Use form data for file upload
        files = request.files

        # Validate required fields for create or update
        required_fields = ["names", "national_id", "district", "address", "dob", "gender", "phone_number"]
        for field in required_fields:
            if field not in data or not data[field].strip():
                abort(400, description=f"Field '{field}' is required and cannot be empty.")

        # Validate district
        district_name = data["district"]
        district = District.query.filter_by(name=district_name).first()
        if not district:
            abort(400, description="Invalid district. Please provide a valid district name.")

        # Validate national_id length
        national_id = data["national_id"]
        if len(national_id) != 16:
            abort(400, description="Invalid national ID. It must be exactly 16 characters long.")

        # Validate phone_number using regex
        phone_number = data["phone_number"]
        if not re.match(r"\+250\d{9}", phone_number):
            abort(400, description="Invalid phone number format. It should be in the format: +250700000000")

        # Validate dob format
        dob = data["dob"]
        try:
            dob_date = datetime.strptime(dob, "%Y-%m-%d").date()
        except ValueError:
            abort(400, description="Invalid date of birth. It must be in 'yyyy-mm-dd' format.")

        # Validate gender
        gender = data["gender"].lower()
        if gender not in ["male", "female"]:
            abort(400, description="Invalid gender. It must be either 'male' or 'female'.")

        # Check for unique constraints
        phone_taken = User.query.filter(User.phone_number == phone_number, User.userId != userId).first()
        if phone_taken:
            abort(400, description="Phone number is already taken by another user.")

        national_id_taken = UserDetails.query.filter(UserDetails.national_id == national_id, UserDetails.userId != userId).first()
        if national_id_taken:
            abort(400, description="National ID is already taken by another user.")

        # Handle profile image upload (optional)
        profile_image = files.get("profilePicture")
        profile_image_path = None
        if profile_image:
            if allowed_file(profile_image.filename):
                try:
                # Upload the file to Cloudinary
                    upload_result = cloudinary.uploader.upload(profile_image)

                    # Get the URL of the uploaded image
                    image_url = upload_result.get('url')
                    profile_image_path = image_url
                except Exception as e:
                    return {"message": f"Image upload failed: {str(e)}"}, 404
            else:
                abort(400, description="Invalid profile picture format. Allowed: png, jpg, jpeg, gif, webp.")

        try:
            if not user_details:
                # Create new user details
                user_details = UserDetails(
                    userId=userId,
                    names=data["names"],
                    national_id=national_id,
                    districtId=district.districtId,
                    address=data["address"],
                    dob=dob_date,
                    gender=gender,
                )
                db.session.add(user_details)
                message = "User details created successfully."
            else:
                # Update existing user details
                user_details.names = data["names"]
                user_details.national_id = national_id
                user_details.districtId = district.districtId
                user_details.address = data["address"]
                user_details.dob = dob_date
                user_details.gender = gender
                message = "User details updated successfully."

            # Update User's profile picture and phone_number (if provided)
            if profile_image_path:
                user.profilePicture = image_url
                
            user.phone_number = phone_number

            # Commit changes
            db.session.commit()

            dob_str = user_details.dob.isoformat() if user_details and user_details.dob else None

            district_obj = {
                "id": district.districtId,
                "provinceId": district.provinceId,
                "name": district.name
            }

            return {
                "userId": user.userId,
                "username": user.username,
                "email": user.email,
                "phone_number": user.phone_number,
                "profilePicture": user.profilePicture,
                "role": user.role,
                "names": user_details.names if user_details else None,
                "national_id": user_details.national_id if user_details else None,
                "district": district_obj,
                "address": user_details.address if user_details else None,
                "dob": dob_str,
                "gender": user_details.gender if user_details else None
            }, 200

        except Exception as e:
            return {"message": "An error occurred"}, 500
        
class UserDetailsDistrictResource(Resource):

    @jwt_required()
    def post(self):
        """Create or update user details for the authenticated user."""
        user_identity = get_jwt_identity()  # Extract userId from JWT
        userId = int(user_identity["userId"])

        # Check if user details already exist
        user_details = UserDetails.query.filter_by(userId=userId).first()
        user = User.query.get(userId)

        if not user:
            return {"message": "User not found."}, 404

        data = request.form  # Use form data for file upload
        files = request.files

        # Validate required fields for create or update
        required_fields = ["district"]
        for field in required_fields:
            if field not in data or not data[field].strip():
                abort(400, description=f"Field '{field}' is required and cannot be empty.")

        print(data["district"])
        # Validate district
        district_name = data["district"]
        district = District.query.filter_by(name=district_name).first()
        if not district:
            abort(400, description="Invalid district. Please provide a valid district name.")

        try:
            if not user_details:
                # Create new user details
                user_details = UserDetails(
                    userId=userId,
                    names=user.username,
                    districtId=district.districtId
                )
                db.session.add(user_details)
                message = "User details created successfully."
            else:
                # Update existing user details
                user_details.names = user.username
                user_details.districtId = district.districtId
                message = "User details updated successfully."

            # Commit changes
            db.session.commit()

            dob_str = user_details.dob.isoformat() if user_details and user_details.dob else None

            district_obj = {
                "id": district.districtId,
                "provinceId": district.provinceId,
                "name": district.name
            }

            return {
                "userId": user.userId,
                "username": user.username,
                "email": user.email,
                "phone_number": user.phone_number,
                "profilePicture": user.profilePicture,
                "role": user.role,
                "names": user_details.names if user_details else None,
                "national_id": user_details.national_id if user_details else None,
                "district": district_obj,
                "address": user_details.address if user_details else None,
                "dob": dob_str,
                "gender": user_details.gender if user_details else None
            }, 200

        except Exception as e:
            print(e)
            return {"message": "An error occurred"}, 500


