import json
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
            "description": "A community for testing",
            "image": "test_image.jpg"
        }
        
        self.create_and_authenticate_user()
        
    def create_and_authenticate_user(self):
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
            'Authorization': f'Bearer {response.json["access_token"]}',
            'Content-Type': 'application/json'
        }
        
        self.user_id = user.userId
        
        response = self.client.post(
            '/api/v1/communities', 
            data=json.dumps(self.community_data),
            headers=self.auth_headers
        )
        
        self.community_id = response.json["data"]["communityId"]
    
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
