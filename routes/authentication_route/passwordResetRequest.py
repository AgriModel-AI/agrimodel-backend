from datetime import datetime, timedelta
import random
import re
from flask import request
from flask_restful import Resource, abort
from models import User, PasswordResetRequest, db
from werkzeug.security import generate_password_hash
from flask_mail import Message
from routes import mail

class PasswordResetResource(Resource):

    def post(self):
        """Send a password reset email."""
        email = request.json.get("email")
        
        # Validate email format
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            abort(400, message="Invalid email format.")

        user = User.query.filter_by(email=email).first()
        if not user:
            abort(400, message="Email not found.")

        # Generate a unique token for password reset
        token = str(random.randint(100000, 999999))  # Simple example; consider using a more secure method

        # Set token expiration (e.g., 1 hour from now)
        expires_at = datetime.utcnow() + timedelta(hours=1)

        # Create a new password reset request
        password_reset_request = PasswordResetRequest(
            userId=user.userId,
            token=token,
            expiresAt=expires_at
        )

        db.session.add(password_reset_request)
        db.session.commit()

        # Send reset email
        self.send_reset_email(user.email, token)

        return {"message": "Password reset email sent."}, 200

    def send_reset_email(self, email, token):
        """Send email with password reset token."""
        msg = Message(
            subject="Password Reset Request",
            recipients=[email],
            body=f"Your password reset token is: {token}. It is valid for 1 hour."
        )
        mail.send(msg)


class VerifyPasswordResetResource(Resource):

    def post(self):
        """Verify the password reset token and reset the password."""
        email = request.json.get("email")
        token = request.json.get("token")
        new_password = request.json.get("new_password")
        confirm_password = request.json.get("confirm_password")

        # Validate new password and confirmation
        if new_password != confirm_password:
            abort(400, message="New password and confirmation do not match.")
        
        if len(new_password) < 8:  # Minimum password length
            abort(400, message="Password must be at least 8 characters long.")

        user = User.query.filter_by(email=email).first()
        if not user:
            abort(400, message="Email not found.")

        # Fetch the password reset request for the user
        reset_request = PasswordResetRequest.query.filter_by(userId=user.userId, token=token).first()
        
        if not reset_request:
            abort(400, message="Invalid token.")
        
        if reset_request.is_expired():
            abort(400, message="Token has expired.")
        
        # Hash the new password
        hashed_password = generate_password_hash(new_password)

        # Update the user's password
        user.password = hashed_password
        db.session.commit()

        # Optionally, delete the password reset request to prevent reuse
        db.session.delete(reset_request)
        db.session.commit()

        return {"message": "Password has been reset successfully."}, 200
