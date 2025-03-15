import json
from base_test import BaseTestCase

class AuthTesting(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.user_data = {
            "email": "test@example.com",
            "name": "Test User",
            "password": "password123",
            "gender": "male",
            "nid": "1234567890123456",
            "phonenumber": "+250789123456",
            "username": "testuser"
        }

    def test_signup_required_fields(self):
        # Test missing required fields
        missing_fields_data = {}
        response = self.client.post(
            '/api/v1/user/signup', 
            data=json.dumps(missing_fields_data), 
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
    
    def test_signup_email_invalid_format(self):
        invalid_email_data = self.user_data.copy()
        invalid_email_data["email"] = "invalid.com"

        response = self.client.post(
            '/api/v1/user/signup', 
            data=json.dumps(invalid_email_data), 
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_signup_success(self):
        response = self.client.post(
            '/api/v1/user/signup', 
            data=json.dumps(self.user_data), 
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
    
    def test_signup_duplicate(self):
        self.client.post(
            '/api/v1/user/signup', 
            data=json.dumps(self.user_data), 
            content_type='application/json'
        )
        response = self.client.post(
            '/api/v1/user/signup', 
            data=json.dumps(self.user_data), 
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_login_require_fields(self):
        missing_fields_data = {}
        response = self.client.post(
            '/api/v1/user/login', 
            data=json.dumps(missing_fields_data), 
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_login_invalid_email_format(self):
        invalid_email_data = {
            "email": "invalidemail",
            "password": "password123"
        }

        response = self.client.post(
            '/api/v1/user/login', 
            data=json.dumps(invalid_email_data), 
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_login_non_existing_user_data(self):
        non_existing_user_data = {
            "email": "nonexisting@example.com",
            "password": "password123"
        }

        response = self.client.post(
            '/api/v1/user/login', 
            data=json.dumps(non_existing_user_data), 
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)

    def test_login_success(self):
        # First create a user
        self.client.post(
            '/api/v1/user/signup', 
            data=json.dumps(self.user_data), 
            content_type='application/json'
        )

        login_data = {
            "email": "test@example.com",
            "password": "password123"
        }
        response = self.client.post(
            '/api/v1/user/login', 
            data=json.dumps(login_data), 
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('access_token', data)