from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from core.models import Tag, Recipe
from recipe.serializers import TagSerializer

TAGS_URL = reverse('recipe:tag-list')


class TestPublicTagAPI(TestCase):
    """Tests the public tag API"""

    def setUp(self) -> None:
        self.client = APIClient()

    def test_login_required(self):
        """Tests that the user should be logged in to request the tags"""
        res = self.client.get(TAGS_URL)
        self.assertEqual(res.status_code, 401)


class TestPrivateTagAPI(TestCase):
    """Tests the public tag API"""

    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(
            email='test@email.com',
            password='test.1234',
            name='Test User'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Tests retrieveing tags"""
        Tag.objects.create(user=self.user, name='Python')
        Tag.objects.create(user=self.user, name='Django')

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limitted_to_user(self):
        """Tests that the retrieved tags belong to the authenticated user"""
        user2 = get_user_model().objects.create_user(
            email='test2@email.com',
            password='test.1234',
            name='Test User2'
        )

        Tag.objects.create(user=user2, name='REST')
        tag = Tag.objects.create(user=self.user, name='API')

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)

    def test_create_tag(self):
        """Tests creating a new tag"""
        payload = {'name': 'Python'}
        self.client.post(TAGS_URL, payload)

        exists = Tag.objects.filter(
            user=self.user,
            name=payload['name']
        ).exists()

        self.assertTrue(exists)

    def test_create_invalid_tag(self):
        """Tests creating a new tag with invalid payload"""
        payload = {'name': ''}
        res = self.client.post(TAGS_URL, payload)

        self.assertEqual(res.status_code, 400)

    def test_retrieve_assigned_tags(self):
        """Tests retrieving tags assigned to recipes"""
        tag1 = Tag.objects.create(user=self.user, name='Lunch')
        tag2 = Tag.objects.create(user=self.user, name='Supper')
        recipe = Recipe.objects.create(
            user=self.user, title='Sample', time_minutes=15, cost=5.00)
        recipe.tags.add(tag1)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        serializer1 = TagSerializer(tag1)
        serializer2 = TagSerializer(tag2)

        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_unique_tag_retrieve(self):
        """Tests filtering assigned only tag (unique)"""
        tag1 = Tag.objects.create(user=self.user, name='Lunch')
        Tag.objects.create(user=self.user, name='Supper')
        recipe1 = Recipe.objects.create(
            user=self.user, title='Sample', time_minutes=15, cost=5.00)
        recipe1.tags.add(tag1)
        recipe2 = Recipe.objects.create(
            user=self.user, title='Sample2', time_minutes=10, cost=7.00)
        recipe2.tags.add(tag1)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)
