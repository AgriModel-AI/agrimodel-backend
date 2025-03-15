import json
from base_test import BaseTestCase

class AuthTesting(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "password123",
            "phone_number": "+250789123456",
            "role": "admin"
        }

    def test_signup_required_fields(self):
        # Test missing required fields
        missing_fields_data = {}
        response = self.client.post(
            '/api/v1/auth/signup', 
            data=json.dumps(missing_fields_data), 
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
    
    def test_signup_email_invalid_format(self):
        invalid_email_data = self.user_data.copy()
        invalid_email_data["email"] = "invalid.com"

        response = self.client.post(
            '/api/v1/auth/signup', 
            data=json.dumps(invalid_email_data), 
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_signup_success(self):
        response = self.client.post(
            '/api/v1/auth/signup', 
            data=json.dumps(self.user_data), 
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
    
    def test_signup_duplicate(self):
        # First create a user
        self.client.post(
            '/api/v1/auth/signup', 
            data=json.dumps(self.user_data), 
            content_type='application/json'
        )
        # Try to create the same user again
        response = self.client.post(
            '/api/v1/auth/signup', 
            data=json.dumps(self.user_data), 
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_login_required_fields(self):
        missing_fields_data = {}
        response = self.client.post(
            '/api/v1/auth/login', 
            data=json.dumps(missing_fields_data), 
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_admin_login_success(self):
        # First create and verify a user with admin role
        self.create_and_verify_user(self.user_data)
        
        login_data = {
            "email": self.user_data["email"],
            "password": self.user_data["password"]
        }
        
        response = self.client.post(
            '/api/v1/auth/login', 
            data=json.dumps(login_data), 
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access_token", response.json)
        self.assertIn("refresh_token", response.json)
    
    def test_client_login_success(self):
        # Create and verify a user
        self.create_and_verify_user(self.user_data)
        
        login_data = {
            "email": self.user_data["email"],
            "password": self.user_data["password"]
        }
        
        response = self.client.post(
            '/api/v1/auth/client/login', 
            data=json.dumps(login_data), 
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access_token", response.json)
        self.assertIn("refresh_token", response.json)
    
    def test_login_non_existing_user(self):
        login_data = {
            "email": "nonexisting@example.com",
            "password": "password123"
        }

        response = self.client.post(
            '/api/v1/auth/login', 
            data=json.dumps(login_data), 
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
    
    def test_farmer_login_rejected(self):
        # Create a farmer user
        farmer_data = self.user_data.copy()
        farmer_data["role"] = "farmer"
        self.create_and_verify_user(farmer_data)
        
        login_data = {
            "email": farmer_data["email"],
            "password": farmer_data["password"]
        }
        
        response = self.client.post(
            '/api/v1/auth/login', 
            data=json.dumps(login_data), 
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)  # Farmers not allowed to use admin login
    
    # Helper method to create and verify a user
    def create_and_verify_user(self, user_data):
        # Create user
        self.client.post(
            '/api/v1/auth/signup', 
            data=json.dumps(user_data), 
            content_type='application/json'
        )
        
        # Simulate verification (this would need to be adjusted based on your actual verification process)
        # For test purposes, directly update the database to mark the user as verified
        from models import User, db
        user = User.query.filter_by(email=user_data["email"]).first()
        user.isVerified = True
        db.session.commit()