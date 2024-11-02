import re
import random
from flask import request
from flask_restful import Resource, abort
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
from models import User, db, VerificationCode
from routes import mail
from flask_mail import Message

class SignupResource(Resource):
    
    def post(self):
        """Function creates API for signing up the user and sending verification code."""
        required_fields = [
            "email",
            "username",
            "password",
            "phone_number",
        ]

        # Ensure all required fields are present
        for field in required_fields:
            if field not in request.json:
                abort(400, message=f"Field '{field}' is required.")

        email = request.json["email"]
        username = request.json["username"]
        password = request.json["password"]
        phone_number = request.json["phone_number"]
        
        # Optional role; default is "farmer"
        role = request.json.get("role", "farmer")  # This line allows setting "admin" or defaulting to "farmer"

        # Validate email format
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            abort(400, message="Invalid email format")

        # Validate password length
        if len(password) < 8:
            abort(400, message="Password must be at least 8 characters long.")

        # Validate phone number format
        if not re.match(r"\+250\d{9}", phone_number):
            abort(400, message="Invalid phone number format. It should be in the format: +250700000000")

        # Check if any of the fields are already in use
        if User.query.filter((User.email == email) | (User.phone_number == phone_number) | (User.username == username)).first():
            abort(400, message="Email, phone number, or username already in use.")

        # Validate the role
        if role not in ["farmer", "admin"]:
            abort(400, message="Invalid role specified. Allowed roles are 'farmer' and 'admin'.")

        try:
            # Hash the password
            hashed_password = generate_password_hash(password)

            # Create a new User instance
            user = User(
                username=username,
                password=hashed_password,
                email=email,
                phone_number=phone_number,
                profilePicture=None,
                role=role,  # Set the role from the request
                isVerified=False,
                isBlocked=False
            )

            db.session.add(user)
            db.session.commit()

            # Generate a 6-digit verification code
            verification_code = str(random.randint(1000, 9999))

            # Create verification code entry
            code_entry = VerificationCode(
                userId=user.userId,
                code=verification_code,
                createdAt=datetime.utcnow(),
                expiresAt=datetime.utcnow() + timedelta(minutes=10),  # Code expires in 10 minutes
                isUsed=False
            )

            db.session.add(code_entry)
            db.session.commit()

            # Send verification email
            self.send_verification_email(user.email, verification_code)

            return {"message": "User created successfully. A verification code has been sent to your email."}, 201

        except Exception as e:
            abort(500, message="Internal server error. Please try again later.")

    def send_verification_email(self, email, code):
        """Send email with verification code."""
        msg = Message(
            subject="Your Verification Code",
            recipients=[email],
            body=f"Your verification code is {code}. It will expire in 10 minutes."
        )
        mail.send(msg)
