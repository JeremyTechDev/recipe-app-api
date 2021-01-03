import tempfile
import os

from PIL import Image
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPES_URL = reverse('recipe:recipe-list')


def image_upload_url(recipe_id):
    """Return url for recipe image"""
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


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

    def test_create_recipe(self):
        """Tests createing a recipe"""
        payload = {
            'title': 'Soup',
            'time_minutes': 25,
            'cost': 7.00,
        }
        res = self.client.post(RECIPES_URL, payload)
        self.assertEqual(res.status_code, 201)
        recipe = Recipe.objects.get(id=res.data['id'])

        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_create_recipe_with_tags(self):
        """Tests creating a recipe with some tags"""
        tag1 = create_sample_tag(self.user, 'vegan')
        tag2 = create_sample_tag(self.user, 'Dessert')
        payload = {
            'title': 'Sandwich',
            'time_minutes': 15,
            'cost': 3.00,
            'tags': [tag1.id, tag2.id]
        }
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, 201)
        recipe = Recipe.objects.get(id=res.data['id'])
        tags = recipe.tags.all()

        self.assertEqual(tags.count(), 2)
        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)

    def test_create_recipe_with_ingredients(self):
        """Tests creating a recipe with some ingredients"""
        ingredient1 = create_sample_ingredient(self.user, 'Bread')
        ingredient2 = create_sample_ingredient(self.user, 'Tomato Sauce')
        payload = {
            'title': 'Pizza',
            'time_minutes': 20,
            'cost': 12.00,
            'ingredients': [ingredient1.id, ingredient2.id]
        }
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, 201)
        recipe = Recipe.objects.get(id=res.data['id'])
        ingredients = recipe.ingredients.all()

        self.assertEqual(ingredients.count(), 2)
        self.assertIn(ingredient1, ingredients)
        self.assertIn(ingredient2, ingredients)

    def test_partial_update_recipe(self):
        """Tests updating a recipe with a PATCH method"""
        recipe = create_sample_recipe(self.user)
        recipe.tags.add(create_sample_tag(self.user))
        new_tag = create_sample_tag(self.user, 'Curry')

        payload = {'title': 'Chicken', 'tags': [new_tag.id]}
        url = detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])

        tags = recipe.tags.all()
        self.assertEqual(len(tags), 1)
        self.assertIn(new_tag, tags)

    def test_full_update_recipe(self):
        """Tests updating a recipe with a PUT method"""

        recipe = create_sample_recipe(self.user)
        recipe.tags.add(create_sample_tag(self.user))

        payload = {
            'title': 'Pasta',
            'time_minutes': 25,
            'cost': 18,
        }

        url = detail_url(recipe.id)
        self.client.put(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.time_minutes, payload['time_minutes'])
        self.assertEqual(recipe.cost, payload['cost'])
        tags = recipe.tags.all()
        self.assertEqual(len(tags), 0)


class TestRecipeImageUpload(TestCase):
    """Tests image uploads"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create(
            email='image@recipe.com',
            password='12345678',
            name='Test')
        self.client.force_authenticate(self.user)
        self.recipe = create_sample_recipe(self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_image_upload(self):
        """Test uploading images to recipe"""
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as ntf:
            img = Image.new('RGB', (10, 10))
            img.save(ntf, format='JPEG')
            ntf.seek(0)
            res = self.client.post(url, {'image': ntf}, format='multipart')

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, 200)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_invalid_image_upload(self):
        """Tests uploading an invalid image"""
        url = image_upload_url(self.recipe.id)
        res = self.client.post(url, {'image': 'no-image'}, format='multipart')
        self.assertEqual(res.status_code, 400)
