from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient

CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class TestPublicUserAPI(TestCase):
    """Test the public API for users"""

    def setUp(self):
        self.client = APIClient()

    def test_create_valid_user(self):
        """It should create a user when the payload is valid"""
        payload = {
            'email': 'test@test.com',
            'password': 'test.1234',
            'name': 'Test name'
        }

        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, 201)
        user = get_user_model().objects.get(**res.data)
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)

    def test_user_exists(self):
        """It should not create a user if it already exists"""
        payload = {
            'email': 'test@test.com',
            'password': 'test.1234',
            'name': 'Test name'
        }
        create_user(**payload)
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, 400)

    def test_short_password(self):
        """It should not create a user if the password is less than 8 chars"""
        payload = {
            'email': 'test@test.com',
            'password': '1234',
            'name': 'Test name'
        }
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, 400)
        user_exists = get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        self.assertFalse(user_exists)

    def test_create_token(self):
        """Tests that a token is created for the user"""
        payload = {
            'email': 'someemail@email.com',
            'password': 'test1234',
            'name': 'Test user'
        }
        create_user(**payload)
        res = self.client.post(TOKEN_URL, payload)
        self.assertIn('token',  res.data)
        self.assertEqual(res.status_code, 200)

    def test_create_token_invalid_credentials(self):
        """Tests that the token is not create if the payload is invalid"""
        create_user(email='useremail@test.com', password='test.1234')
        payload = {
            'email': 'email@test.com',
            'password': 'wrong_password'
        }
        res = self.client.post(TOKEN_URL, payload)

        self.assertEqual(res.status_code, 400)
        self.assertNotIn('token', res.data)

    def test_create_token_no_user(self):
        """Tests that the token is not created if the users does not exits"""
        payload = {
            'email': 'email@test.com',
            'password': 'test.1234'
        }
        res = self.client.post(TOKEN_URL, payload)

        self.assertEqual(res.status_code, 400)
        self.assertNotIn('token', res.data)

    def test_missing_fields(self):
        """Test that the token is not created if any field is missing"""
        res = self.client.post(
            TOKEN_URL, {'email': 'email@test.com', 'password': ''})

        self.assertEqual(res.status_code, 400)
        self.assertNotIn('token', res.data)
