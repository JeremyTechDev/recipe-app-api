from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPES_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    """Return a recipe detail URL"""
    return reverse('recipe:recipe-detail', args=[recipe_id])


def create_sample_tag(user, name='Easy'):
    """Create a sample tag"""
    return Tag.objects.create(user=user, name=name)


def create_sample_ingredient(user, name='Bacon'):
    """Create a sample ingredient"""
    return Ingredient.objects.create(user=user, name=name)


def create_sample_recipe(user, **params):
    """Create a sample recipe"""
    defaults = {
        'title': 'Sample Recipe',
        'time_minutes': 10,
        'cost': 5.00,
    }
    defaults.update(params)
    return Recipe.objects.create(user=user, **defaults)


class TestPublicRecipeAPI(TestCase):
    """Tests the unauthenticated recipe API access"""

    def setUp(self) -> None:
        self.client = APIClient()

    def test_auth_required(self):
        """Tests that authentication is requires"""

        res = self.client.get(RECIPES_URL)
        self.assertEqual(res.status_code, 401)


class TestPrivateRecipeAPI(TestCase):
    """Tests the authenticated recipe API access"""

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create(
            email='test@recipe.com',
            password='12345678',
            name='Test')
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Tests retrieving a list of recipes"""
        create_sample_recipe(self.user)
        create_sample_recipe(self.user)

        res = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_limited_to_user(self):
        """Tests retrieving recipes of the auth user"""
        user2 = get_user_model().objects.create(
            email='test2@recipe.com',
            password='12345678',
            name='Test2')
        create_sample_recipe(user2)
        create_sample_recipe(self.user)

        res = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.all().filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data, serializer.data)

    def test_view_detail_recipe(self):
        """Tests viewing a detail recipe"""
        recipe = create_sample_recipe(self.user)
        recipe.tags.add(create_sample_tag(self.user))
        recipe.ingredients.add(create_sample_ingredient(self.user))

        url = detail_url(recipe.id)
        res = self.client.get(url)
        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data, serializer.data)
