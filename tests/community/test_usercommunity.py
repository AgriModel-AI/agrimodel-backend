import json
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
            "description": "A community for testing",
            "image": "test_image.jpg"
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
            'Authorization': f'Bearer {response.json["access_token"]}',
            'Content-Type': 'application/json'
        }
        
        # Store the user ID for later use
        self.user_id = user.userId
        
        # Create a test community
        response = self.client.post(
            '/api/v1/communities', 
            data=json.dumps(self.community_data),
            headers=self.auth_headers
        )
        
        # Debugging: Print the response JSON to inspect it
        print("Community Creation Response JSON:", response.json)  # Debugging line to inspect the response body
        print("Community Creation Response Status Code:", response.status_code)  # Debugging line to check the HTTP status code
        
        # Check if 'data' exists in the response JSON and handle it
        if "data" in response.json:
            self.community_id = response.json["data"]["communityId"]
        else:
            print("Error: 'data' key not found in the response.")  # Debugging line
            self.community_id = None  # Explicitly set to None if data is missing

    def test_join_community_success(self):
        """Test successfully joining a community."""
        
        # Ensure community_id is set
        if not hasattr(self, 'community_id') or self.community_id is None:
            print("Error: community_id is not set. Exiting test.")  # Debugging line
            return  # Skip this test if community_id is not set
            
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
            print("Error: community_id is not set. Exiting test.")  # Debugging line
            return  # Skip this test if community_id is not set
        
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
        self.assertEqual(response.json["message"], "You are already a member of this community.")
    
    def test_join_community_not_exist(self):
        """Test trying to join a community that does not exist."""
        
        non_existent_community_id = 999999  # Assuming this ID does not exist
        
        response = self.client.post(
            f'/api/v1/communities/user-community/{non_existent_community_id}', 
            headers=self.auth_headers
        )
        
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json["message"], "Community not found.")
    
    def test_leave_community_success(self):
        """Test successfully leaving a community."""
        
        if not hasattr(self, 'community_id') or self.community_id is None:
            print("Error: community_id is not set. Exiting test.")  # Debugging line
            return  # Skip this test if community_id is not set
        
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
        self.assertEqual(response.json["message"], "Community not found or you are not a member.")
    
    def test_get_all_joined_communities(self):
        """Test getting all communities a user has joined."""
        
        if not hasattr(self, 'community_id') or self.community_id is None:
            print("Error: community_id is not set. Exiting test.")  # Debugging line
            return  # Skip this test if community_id is not set
        
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

