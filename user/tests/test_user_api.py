"""
Tests for the user API.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

CREATE_USER_URL = reverse('signup')
TOKEN_URL = reverse('login')


def create_user(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """Test the public feature of the user API."""

    def setUp(self):
        self.client = APIClient()

    def test_create_valid_user_success(self):
        """Test creating user with valid payload is successful."""
        payload = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
            }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload['email'])
        self.assertTrue(user.check_password(payload['password']))
        self.assertEqual(user.first_name, payload['first_name'])
        self.assertEqual(user.last_name, payload['last_name'])

    def test_user_with_email_exists_error(self):
        """Test error returned if user with email exists."""
        payload = {
                'email': 'test@example.com',
                'password': 'testpass123',
                'first_name': 'Test Name',
                'last_name': 'User',
                }
        create_user(**payload)
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_for_user(self):
        """Test generates token for valid credentials."""
        user_details = {
                'first_name': 'Test Name',
                'last_name': 'User',
                'email': 'test@example.com',
                'password': 'test-user-password123',
                }
        create_user(**user_details)

        payload = {
                'email': user_details['email'],
                'password': user_details['password'],
                }
        res = self.client.post(TOKEN_URL, payload)

        self.assertIn('refresh', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_bad_credentials(self):
        """Test token not generated for invalid credentials."""
        user_details = {
                'first_name': 'Test Name',
                'last_name': 'User',
                'email': 'test@example.com',
                'password': 'test-user-password123',
                }
        create_user(**user_details)

        payload = {
                'email': user_details['email'],
                'password': 'wrong-password',
                }
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('refresh', res.data)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_token_blank_password(self):
        """Test token not generated for blank password."""

        payload = {
                'email': 'test@example.com',
                'password': '',
                }
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('refresh', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class JWTAuthenticationTestCase(APITestCase):
    def test_get_token(self):
        """
        Test that controls the implementation of the JWT Authentication.
        A pair of token is created and the token is testing with the
        verify endpoint.
        """
        user = get_user_model().objects.create_user(
                first_name="first_name",
                last_name="last_name",
                email="email5@email.com",
                password="password")
        user.is_active = False
        user.save()
        response = self.client.post(TOKEN_URL, {'email': 'email5@email.com',
                                                'password': 'password'},
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        user.is_active = True
        user.save()
        response = self.client.post(TOKEN_URL, {"email": "email5@email.com",
                                                "password": "password"},
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('access' in response.data)
        token = response.data['access']
        verify_url = reverse('verify')
        response = self.client.post(verify_url, {"token": token},
                                    format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.post(verify_url, {"token": "whatever"},
                                    format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
