from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient

from core.models import Ingredient
from recipe.serializers import IngredientSerializer


INGREDIENT_URL = reverse('recipe:ingredient-list')


class TestIngredientPublicAPI(TestCase):
    """Test the public ingredients API"""

    def setUp(self) -> None:
        self.client = APIClient()

    def test_required_login(self):
        """Test that login is required to use the endpoint"""
        res = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, 401)


class TestIngredientPrivateAPI(TestCase):
    """Test the private ingredients API"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='test@test.com',
            password='12345678',
            name='Test'
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients_list(self):
        """Test retrieving a list of ingredients"""
        Ingredient.objects.create(user=self.user, name='Kale')
        Ingredient.objects.create(user=self.user, name='Rice')

        res = self.client.get(INGREDIENT_URL)

        Ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(Ingredients, many=True)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_auth_users(self):
        """Tests that the ingredients are limited to the auth user"""
        user2 = get_user_model().objects.create_user(
            email='test@testemail.com',
            password='12345678',
            name='Test'
        )

        Ingredient.objects.create(user=user2, name='Cheese')
        ingredient = Ingredient.objects.create(user=self.user, name='Beans')

        res = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)
