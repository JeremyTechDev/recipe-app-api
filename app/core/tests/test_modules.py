from django.test import TestCase
from django.contrib.auth import get_user_model
from core import models


def create_sample_user(
        email='test@email.com',
        password='test.1234',
        name='Test user'):
    """Creates a sample user"""
    return get_user_model().objects.create_user(
        email=email,
        password=password,
        name=name)


class TestModel(TestCase):

    def test_create_user_with_email_successful(self):
        """It should create a user"""
        email = 'test@email.com'
        password = "test.1234"
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_normalize_email(self):
        """Normalizes the email of a new user"""
        email = 'test@RECIPE_APP.COM'
        user = get_user_model().objects.create_user(email, 'test123')

        self.assertEqual(user.email, email.lower())

    def test_email_validation(self):
        """Should make sure the new user has a valid email field"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('', 'test123')

    def test_create_super_user(self):
        """Should create a super user"""
        user = get_user_model().objects.create_superuser(
            'superuser@test.com',
            'test.1234'
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_tag_str(self):
        """Tests the tag string representation"""
        tag = models.Tag.objects.create(
            user=create_sample_user(),
            name='Python'
        )

        self.assertEqual(str(tag), tag.name)
