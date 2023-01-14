"""
Tests for models.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model


def create_user(email='user@example.com', password='testpass'):
    """Create a sample user."""
    return get_user_model().objects.create_user(email, password)


class ModelTest(TestCase):
    """Test models."""

    def test_create_user_with_email_successful(self):
        """Test creating a new user with an email is successful."""
        email = 'test@example.com'
        password = "testpass123"
        first_name = "Test"
        last_name = "User"
        user = get_user_model().objects.create_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                )

        self.assertEqual(user.email, email)
        self.assertEqual(user.first_name, first_name)
        self.assertEqual(user.last_name, last_name)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test email is normalized for new users."""
        sample_emails = [
                ['test1@EXAMPLE.com', 'test1@example.com'],
                ['Test2@Example.com', 'Test2@example.com'],
                ['TEST3@EXAMPLE.COM', 'TEST3@example.com'],
                ['test4@example.COM', 'test4@example.com'],
                ]
        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(email, 'sample123')
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raises_error(self):
        """Test that creating a user without an email raises a ValueError."""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('', 'test123')

    def test_create_new_superuser(self):
        """Test creating a new superuser."""
        user = get_user_model().objects.create_superuser(
                'test@example.com',
                'test123',
                'Test',
                'User',
                )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
