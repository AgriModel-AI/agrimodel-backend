import json
import io
from base_test import BaseTestCase
from models import User, UserCommunity, db

class UserCommunityTesting(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.user_data = {
            "email": "community_test@example.com",
            "username": "community_user",
            "password": "password123",
            "phone_number": "+250789123456",
            "role": "admin"
        }
        
        self.community_data = {
            "name": "Test Community",
            "description": "A community for testing"
        }
        
        self.create_and_authenticate_user()
        
    def test_user_signup(self):
        """Test user account creation."""
        signup_response = self.client.post(
            '/api/v1/auth/signup', 
            data=json.dumps(self.user_data), 
            content_type='application/json'
        )
        
        self.assertIn(signup_response.status_code, [201, 400])  # 400 if user already exists
        
        user = User.query.filter_by(email=self.user_data["email"]).first()
        self.assertIsNotNone(user, "User should be created successfully")
        
    def test_user_login(self):
        """Test user authentication."""
        # Ensure user exists and is verified
        user = User.query.filter_by(email=self.user_data["email"]).first()
        if user:
            user.isVerified = True
            db.session.commit()
        
        login_data = {
            "email": self.user_data["email"],
            "password": self.user_data["password"]
        }
        
        login_response = self.client.post(
            '/api/v1/auth/login', 
            data=json.dumps(login_data), 
            content_type='application/json'
        )
        
        self.assertEqual(login_response.status_code, 200, "Login should be successful")
        self.assertIn("access_token", login_response.json, "Access token should be returned")
        
    def test_community_creation(self):
        """Test community creation with file upload."""
        # Ensure user is authenticated first
        user = User.query.filter_by(email=self.user_data["email"]).first()
        if user:
            user.isVerified = True
            db.session.commit()
        
        login_response = self.client.post(
            '/api/v1/auth/login', 
            data=json.dumps({
                "email": self.user_data["email"],
                "password": self.user_data["password"]
            }), 
            content_type='application/json'
        )
        
        auth_headers = {
            'Authorization': f'Bearer {login_response.json["access_token"]}'
        }
        
        # Create test image file
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc```\x00\x00\x00\x04\x00\x01\xdd\x8d\xb4\x1c\x00\x00\x00\x00IEND\xaeB`\x82'
        test_image = (io.BytesIO(png_data), 'test_image.png')
        
        form_data = {
            'name': self.community_data['name'],
            'description': self.community_data['description'],
            'image': test_image
        }
        
        community_response = self.client.post(
            '/api/v1/communities', 
            data=form_data,
            headers=auth_headers
        )
        
        self.assertEqual(community_response.status_code, 201, "Community should be created successfully")
        self.assertIn("communityId", community_response.json, "Community ID should be returned")
        
    def create_and_authenticate_user(self):
        """Helper method for test setup."""
        self.client.post(
            '/api/v1/auth/signup', 
            data=json.dumps(self.user_data), 
            content_type='application/json'
        )
        
        user = User.query.filter_by(email=self.user_data["email"]).first()
        user.isVerified = True
        db.session.commit()
        
        login_data = {
            "email": self.user_data["email"],
            "password": self.user_data["password"]
        }
        
        response = self.client.post(
            '/api/v1/auth/login', 
            data=json.dumps(login_data), 
            content_type='application/json'
        )
        
        self.auth_headers = {
            'Authorization': f'Bearer {response.json["access_token"]}'
        }
        
        self.user_id = user.userId
        
        # Create test image file
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc```\x00\x00\x00\x04\x00\x01\xdd\x8d\xb4\x1c\x00\x00\x00\x00IEND\xaeB`\x82'
        test_image = (io.BytesIO(png_data), 'test_image.png')
        
        form_data = {
            'name': self.community_data['name'],
            'description': self.community_data['description'],
            'image': test_image
        }
        
        response = self.client.post(
            '/api/v1/communities', 
            data=form_data,
            headers=self.auth_headers
        )
        
        self.community_id = response.json["communityId"]
    
    def test_join_community_success(self):
        """Test successfully joining a community."""
        response = self.client.post(
            f'/api/v1/communities/user-community/{self.community_id}', 
            headers=self.auth_headers
        )
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json["message"], "Successfully joined the community.")
        
        membership = UserCommunity.query.filter_by(
            userId=self.user_id, 
            communityId=self.community_id
        ).first()
        
        self.assertIsNotNone(membership)