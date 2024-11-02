from flask_restful import Resource, abort
from models import VerificationCode, User, db
from flask import request
from datetime import datetime

class ValidateCodeResource(Resource):

    def post(self):
        """Function to validate the verification code using email."""
        
        required_fields = ["email", "code"]
        for field in required_fields:
            if field not in request.json:
                abort(400, message=f"Field '{field}' is required.")

        email = request.json["email"]
        code = request.json["code"]

        # Fetch the user based on the provided email
        user = User.query.filter_by(email=email).first()
        
        if not user:
            abort(400, message="User not found with the provided email.")

        # Fetch the verification code entry from the database using the userId
        verification_entry = VerificationCode.query.filter_by(userId=user.userId, code=code).first()

        if not verification_entry:
            abort(400, message="Invalid verification code.")

        # Check if the code is already used
        if verification_entry.isUsed:
            abort(400, message="This verification code has already been used.")

        # Check if the code has expired
        if verification_entry.expiresAt < datetime.utcnow():
            abort(400, message="This verification code has expired.")

        # Mark the code as used
        verification_entry.isUsed = True

        # Update the user's verification status
        user.isVerified = True
        
        # Commit the changes to the database
        db.session.commit()

        return {"message": "Verification code validated successfully. Your account is now verified."}, 200


from flask_restful import Resource, abort
from models import VerificationCode, User, db
from flask import request
from datetime import datetime, timedelta
import random
from flask_mail import Message
from routes import mail

class ResendCodeResource(Resource):

    def post(self):
        """Function to resend the verification code to the user."""
        
        required_fields = ["email"]
        for field in required_fields:
            if field not in request.json:
                abort(400, message=f"Field '{field}' is required.")

        email = request.json["email"]

        # Fetch the user based on the provided email
        user = User.query.filter_by(email=email).first()
        
        if not user:
            abort(400, message="User not found with the provided email.")

        # Check if the user's account is already verified
        if user.isVerified:
            return {"message": "This account is already verified."}, 400

        # Generate a new 6-digit verification code
        verification_code = str(random.randint(1000, 9999))

        # Create or update verification code entry
        verification_entry = VerificationCode.query.filter_by(userId=user.userId).first()
        
        if verification_entry:
            # Update existing entry with the new code and reset expiry
            verification_entry.code = verification_code
            verification_entry.createdAt = datetime.utcnow()
            verification_entry.expiresAt = datetime.utcnow() + timedelta(minutes=10)  # Code expires in 10 minutes
            verification_entry.isUsed = False
        else:
            # Create a new verification code entry if one doesn't exist
            verification_entry = VerificationCode(
                userId=user.userId,
                code=verification_code,
                createdAt=datetime.utcnow(),
                expiresAt=datetime.utcnow() + timedelta(minutes=10),
                isUsed=False
            )
            db.session.add(verification_entry)

        # Commit changes to the database
        db.session.commit()

        # Send the new verification email
        self.send_verification_email(user.email, verification_code)

        return {"message": "A new verification code has been sent to your email."}, 200

    def send_verification_email(self, email, code):
        """Send email with the new verification code."""
        msg = Message(
            subject="Your New Verification Code",
            recipients=[email],
            body=f"Your new verification code is {code}. It will expire in 10 minutes."
        )
        mail.send(msg)
