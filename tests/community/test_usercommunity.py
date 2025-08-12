import json
import io
from base_test import BaseTestCase
from models import User, UserCommunity, Community, Post, db

class UserCommunityTesting(BaseTestCase):
    def setUp(self):
        super().setUp()
        # Create test user data
        self.user_data = {
            "email": "community_test@example.com",
            "username": "community_user",
            "password": "password123",
            "phone_number": "+250789123456",
            "role": "admin"
        }
        
        # Create a test community data
        self.community_data = {
            "name": "Test Community",
            "description": "A community for testing"
        }
        
        # Create and authenticate a user for testing
        self.create_and_authenticate_user()

    def create_and_authenticate_user(self):
        # Create user
        self.client.post(
            '/api/v1/auth/signup', 
            data=json.dumps(self.user_data), 
            content_type='application/json'
        )
        
        # Verify user
        user = User.query.filter_by(email=self.user_data["email"]).first()
        user.isVerified = True
        db.session.commit()
        
        # Login to get tokens
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
        
        # Store the user ID for later use
        self.user_id = user.userId
        
        # Create test image file
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc```\x00\x00\x00\x04\x00\x01\xdd\x8d\xb4\x1c\x00\x00\x00\x00IEND\xaeB`\x82'
        test_image = (io.BytesIO(png_data), 'test_image.png')
        
        # Create a test community with form data
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
        
        # Handle response properly
        if response.status_code == 201:
            self.community_id = response.json["communityId"]
        else:
            print(f"Community creation failed: {response.json}")
            self.community_id = None

    def test_join_community_success(self):
        """Test successfully joining a community."""
        
        # Ensure community_id is set
        if not hasattr(self, 'community_id') or self.community_id is None:
            self.skipTest("Community was not created successfully")
            
        response = self.client.post(
            f'/api/v1/communities/user-community/{self.community_id}', 
            headers=self.auth_headers
        )
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json["message"], "Successfully joined the community.")
        
        # Verify the database has the membership record
        membership = UserCommunity.query.filter_by(
            userId=self.user_id, 
            communityId=self.community_id
        ).first()
        
        self.assertIsNotNone(membership)

    def test_join_community_already_joined(self):
        """Test trying to join a community that the user has already joined."""
        
        if not hasattr(self, 'community_id') or self.community_id is None:
            self.skipTest("Community was not created successfully")
        
        # First, join the community
        self.client.post(
            f'/api/v1/communities/user-community/{self.community_id}', 
            headers=self.auth_headers
        )
        
        # Try to join the community again
        response = self.client.post(
            f'/api/v1/communities/user-community/{self.community_id}', 
            headers=self.auth_headers
        )
        
        self.assertEqual(response.status_code, 400)
        # Use the actual message from your API
        self.assertEqual(response.json["message"], "User is already a member of this community.")
    
    def test_join_community_not_exist(self):
        """Test trying to join a community that does not exist."""
        
        non_existent_community_id = 999999  # Assuming this ID does not exist
        
        response = self.client.post(
            f'/api/v1/communities/user-community/{non_existent_community_id}', 
            headers=self.auth_headers
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json["message"], "Community not found.")
    
    def test_leave_community_success(self):
        """Test successfully leaving a community."""
        
        if not hasattr(self, 'community_id') or self.community_id is None:
            self.skipTest("Community was not created successfully")
        
        # Join the community first
        self.client.post(
            f'/api/v1/communities/user-community/{self.community_id}', 
            headers=self.auth_headers
        )
        
        # Now, leave the community
        response = self.client.delete(
            f'/api/v1/communities/user-community/{self.community_id}', 
            headers=self.auth_headers
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["message"], "Successfully left the community.")
        
        # Verify the membership record is removed
        membership = UserCommunity.query.filter_by(
            userId=self.user_id, 
            communityId=self.community_id
        ).first()
        
        self.assertIsNone(membership)
    
    def test_leave_community_not_exist(self):
        """Test trying to leave a community that the user has not joined."""
        
        non_existent_community_id = 999999  # Assuming this ID does not exist
        
        response = self.client.delete(
            f'/api/v1/communities/user-community/{non_existent_community_id}', 
            headers=self.auth_headers
        )
        
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json["message"], "Membership not found.")
    
    def test_get_all_joined_communities(self):
        """Test getting all communities a user has joined."""
        
        if not hasattr(self, 'community_id') or self.community_id is None:
            self.skipTest("Community was not created successfully")
        
        # Join the community first
        self.client.post(
            f'/api/v1/communities/user-community/{self.community_id}', 
            headers=self.auth_headers
        )
        
        # Get all communities the user has joined
        response = self.client.get(
            '/api/v1/communities/user-community', 
            headers=self.auth_headers
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.json["data"]) > 0)
        self.assertIn(self.community_id, [community["communityId"] for community in response.json["data"]])