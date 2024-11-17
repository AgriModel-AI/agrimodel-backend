from flask import request, jsonify
from flask_mail import Message
from flask_restful import Resource, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash
from datetime import datetime
from models import db, User, UserDetails, District
import re

from routes import mail

class CreateAdminUser(Resource):
    @jwt_required()
    def post(self):
        """Admin route to create an admin user."""
        # Check if current user is an admin (Uncomment if needed)
        # current_user_id = get_jwt_identity()
        # current_user = User.query.get(current_user_id)
        # if not current_user or current_user.role != 'admin':
        #     return {"message": "Unauthorized. Only admin users can create new admin accounts."}, 403

        data = request.json
        required_fields = ["username", "email", "phone_number", "names", "gender", "national_id", "district", "address", "dob"]

        # Validate required fields
        for field in required_fields:
            if field not in data or (not str(data[field]).strip() if isinstance(data[field], str) else data[field] is None):
                abort(400, message=f"Field '{field}' is required and cannot be empty.")

        username = data["username"]
        email = data["email"]
        phone_number = data["phone_number"]
        names = data["names"]
        gender = data["gender"]
        national_id = data["national_id"]
        district_id = data.get("district")
        address = data.get("address")
        dob = data.get("dob")

        # Validate email format
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            abort(400, message="Invalid email format.")

        # Validate phone number format
        if not re.match(r"\+250\d{9}", phone_number):
            abort(400, message="Invalid phone number format. It should be in the format: +250700000000.")

        # Check if email, username, or phone number already exists
        if User.query.filter((User.email == email) | (User.phone_number == phone_number) | (User.username == username)).first():
            abort(400, message="Email, phone number, or username already in use.")
            
        if not national_id.isdigit() or len(national_id) != 16:
            abort(400, message="Invalid 'National ID': must be exactly 16 numeric characters.")

        # Check if the national ID already exists
        if UserDetails.query.filter_by(national_id=national_id).first():
            abort(400, message="The provided national ID already exists.")

        # Validate if district exists
        district = District.query.get(district_id)
        if not district:
            abort(404, message="District not found.")

        # Validate date of birth format
        try:
            dob = datetime.strptime(dob, "%Y-%m-%d").date()
        except ValueError:
            abort(400, message="Invalid 'dob': must be in 'YYYY-MM-DD' format.")

        # Generate the password in the format Admin{currentYear}!{currentDay}@agrimodel.rw
        current_year = datetime.now().year
        current_day = datetime.now().day
        generated_password = f"Admin{current_year}!{current_day}@agrimodel.rw"

        # Hash the password
        hashed_password = generate_password_hash(generated_password)

        try:
            # Create a new User instance with the role of 'admin'
            new_admin_user = User(
                username=username,
                password=hashed_password,
                email=email,
                phone_number=phone_number,
                role='admin',
                isVerified=True,
                isBlocked=False
            )
            db.session.add(new_admin_user)
            db.session.commit()

            # Create user details for the new admin user
            user_details = UserDetails(
                userId=new_admin_user.userId,
                names=names,
                national_id=national_id,
                districtId=district_id,
                address=address,
                dob=dob,
                gender=gender
            )
            db.session.add(user_details)
            db.session.commit()

            # Send the generated password to the user's email
            self.send_email(
                email=email,
                subject="Your New Admin Account Password",
                body=f"Hello {username},\n\nYour account has been created successfully. Your login password is: {generated_password}\n\nPlease change your password after logging in for the first time.\n\nBest Regards,\nAdmin Team"
            )

            return {"message": "Admin user created successfully and password has been sent to their email."}, 201

        except Exception as e:
            db.session.rollback()
            abort(500, message=f"Internal server error: {str(e)}")
            
    
    def send_email(self, email, subject, body):
        """Send email with verification code."""
        msg = Message(
            subject=subject,
            recipients=[email],
            body=body
        )
        mail.send(msg)
