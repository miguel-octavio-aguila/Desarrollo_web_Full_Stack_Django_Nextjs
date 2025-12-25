from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.conf import settings
from django.core.cache import cache

from rest_framework import status
from rest_framework.test import APIClient

from .models import Category, Post, PostAnalytics, Heading


class CategoryModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Tech",
            title="Technology",
            description="All about technology",
            slug="tech"
        )

    def test_category_creation(self):
        self.assertEqual(str(self.category), "Tech")
        self.assertEqual(self.category.title, "Technology")


class PostModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Tech",
            title="Technology",
            description="All about technology",
            slug="tech"
        )

        self.post = Post.objects.create(
            title="Post 1",
            description="Description 1",
            content="Content 1",
            thumbnail=None,
            keywords="test, post",
            slug="post-1",
            category=self.category,
            status="published"
        )

    def test_post_creation(self):
        self.assertEqual(str(self.post), "Post 1")
        self.assertEqual(self.post.category.name, "Tech")

    def test_post_published_manager(self):
        self.assertTrue(Post.post_published.exists())


class PostAnalyticsModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Analytics", slug="analytics")
        self.post = Post.objects.create(
            title="Analytics Post",
            description="Post for analytics",
            content="Analytics content",
            slug="analytics-post",
            category=self.category,
        )
        self.analytics = PostAnalytics.objects.create(post=self.post)

    def test_click_through_rate_update(self):
        self.analytics.increment_impressions()
        self.analytics.increment_clicks()
        self.analytics.refresh_from_db()
        self.assertEqual(self.analytics.clicks_through_rate, 100)


class HeadingModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Heading", slug="heading")
        self.post = Post.objects.create(
            title="Heading Post",
            description="Post for heading",
            content="Heading content",
            slug="heading-post",
            category=self.category,
        )
        self.heading = Heading.objects.create(post=self.post, title="Heading 1", slug="heading-1", level=1, order=1)

    def test_heading_creation(self):
        self.assertEqual(self.heading.slug, "heading-1")
        self.assertEqual(self.heading.level, 1)


# Views Tests
class PostListViewTest(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.api_key = settings.VALID_API_KEYS[0]
        
        self.category = Category.objects.create(name="Test Category", slug="test-category")
        self.post = Post.objects.create(
            title="Test Post",
            description="Test description",
            content="Test content",
            slug="test-post",
            category=self.category,
            status="published"
        )

    def tearDown(self):
        cache.clear()

    def test_get_post_list(self):
        url = reverse("post-list")
        response = self.client.get(
            url,
            HTTP_API_KEY=self.api_key
        )
        
        data = response.json()
        
        self.assertIn("success", data)
        self.assertTrue(data["success"])
        self.assertIn("status", data)
        self.assertEqual(data["status"], 200)
        self.assertIn("results", data)
        self.assertEqual(data["count"], 1)
        
        results = data["results"]
        self.assertEqual(len(results), 1)
        
        post_data = results[0]
        self.assertEqual(post_data["id"], str(self.post.id))
        self.assertEqual(post_data["title"], self.post.title)
        self.assertEqual(post_data["description"], self.post.description)
        self.assertEqual(post_data["slug"], self.post.slug)
        self.assertIsNone(post_data["thumbnail"])
        
        category_data = post_data["category"]
        self.assertEqual(category_data["name"], self.category.name)
        self.assertEqual(category_data["slug"], self.category.slug)
        
        self.assertEqual(post_data["view_count"], 0)
        
        self.assertIsNone(data["next"])
        self.assertIsNone(data["previous"])


class PostDetailViewTest(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.api_key = settings.VALID_API_KEYS[0]
        
        self.category = Category.objects.create(name="Test Category", slug="test-category")
        self.post = Post.objects.create(
            title="Test Post",
            description="Test description",
            content="Test content",
            slug="test-post",
            category=self.category,
            status="published"
        )

    def tearDown(self):
        cache.clear()

    # For testing the increment_post_views task from Celery
    @patch("apps.blog.tasks.increment_post_views.delay")
    def test_get_post_detail_success(self, mock_increment_post_views):
        """
        Test to verify that posts details are obtained successfully
        and that the task of incrementing the view count is called.
        """
        url = reverse("post-detail") + f"?slug={self.post.slug}" 
        response = self.client.get(
            url,
            HTTP_API_KEY=self.api_key
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        
        self.assertIn("success", data)
        self.assertTrue(data["success"])
        self.assertIn("status", data)
        self.assertEqual(data["status"], 200)
        self.assertIn("results", data)
        
        post_data = data["results"]
        self.assertEqual(post_data["id"], str(self.post.id))
        self.assertEqual(post_data["title"], self.post.title)
        self.assertEqual(post_data["description"], self.post.description)
        self.assertEqual(post_data["slug"], self.post.slug)
        self.assertIsNone(post_data["thumbnail"])
        
        category_data = post_data["category"]
        self.assertEqual(category_data["name"], self.category.name)
        self.assertEqual(category_data["slug"], self.category.slug)
        
        self.assertEqual(post_data["view_count"], 0)
        
        mock_increment_post_views.assert_called_once_with(self.post.slug, '127.0.0.1')
    
    def test_get_post_detail_not_found(self):
        """
        Test to verify that a not found error is returned when the post is not found.
        """
        url = reverse("post-detail") + "?slug=nonexistent-slug" 
        response = self.client.get(
            url,
            HTTP_API_KEY=self.api_key
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        data = response.json()
        
        self.assertIn("detail", data)
        self.assertEqual(data["detail"], "Post does not exist")


class PostHeadingsViewTest(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.api_key = settings.VALID_API_KEYS[0]
        
        self.category = Category.objects.create(name="Test Category", slug="test-category")
        self.post = Post.objects.create(
            title="Test Post",
            description="Test description",
            content="Test content",
            slug="test-post",
            category=self.category,
            status="published"
        )
        self.heading = Heading.objects.create(
            post=self.post,
            title="Heading 1",
            slug="heading-1",
            level=1,
            order=1
        )
        self.heading2 = Heading.objects.create(
            post=self.post,
            title="Heading 2",
            slug="heading-2",
            level=2,
            order=2
        )

    def tearDown(self):
        cache.clear()

    def test_get_post_headings_success(self):
        """
        Test to verify that the headings of a post are obtained successfully.
        """
        url = reverse("post-headings") + f"?slug={self.post.slug}" 
        response = self.client.get(
            url,
            HTTP_API_KEY=self.api_key
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        
        self.assertIn("success", data)
        self.assertTrue(data["success"])
        self.assertIn("status", data)
        self.assertEqual(data["status"], 200)
        self.assertIn("results", data)
        
        headings = data["results"]
        self.assertEqual(len(headings), 2)
        
        heading_data = headings[0]
        self.assertEqual(heading_data["title"], self.heading.title)
        self.assertEqual(heading_data["slug"], self.heading.slug)
        self.assertEqual(heading_data["level"], self.heading.level)
        
        heading_data = headings[1]
        self.assertEqual(heading_data["title"], self.heading2.title)
        self.assertEqual(heading_data["slug"], self.heading2.slug)
        self.assertEqual(heading_data["level"], self.heading2.level)
    
    def test_get_post_headings_not_found(self):
        """
        Test to verify that a not found error is returned when the post is not found.
        """
        url = reverse("post-headings") + "?slug=nonexistent-slug" 
        response = self.client.get(
            url,
            HTTP_API_KEY=self.api_key
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        
        self.assertTrue(data["success"])
        self.assertEqual(data["status"], 200)
        self.assertEqual(len(data["results"]), 0)


class IncrementPostClicksViewTest(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.api_key = settings.VALID_API_KEYS[0]
        
        self.category = Category.objects.create(name="Analytics Category", slug="analytics-category")
        self.post = Post.objects.create(
            title="Analytics Test Post",
            description="Test description",
            content="Test content",
            slug="analytics-test-post",
            category=self.category,
            status="published"
        )

    def tearDown(self):
        cache.clear()

    def test_increment_post_clicks_success(self):
        """
        Test to verify that the number of clicks is incremented successfully.
        """
        url = reverse("increment-post-clicks")
        response = self.client.post(
            url,
            {"slug": self.post.slug},
            HTTP_API_KEY=self.api_key,
            format="json"
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        
        self.assertTrue(data["success"])
        self.assertEqual(data["status"], 200)
        
        results = data["results"]
        self.assertIn("message", results)
        self.assertEqual(results["message"], "Post clicks incremented successfully")
        self.assertIn("clicks", results)
        
        self.assertEqual(results["clicks"], 1)
        
        from apps.blog.models import PostAnalytics
        analytics = PostAnalytics.objects.get(post=self.post)
        self.assertEqual(analytics.clicks, 1)
    
    def test_increment_post_clicks_not_found(self):
        """
        Test to verify that a not found error is returned when the post is not found.
        """
        url = reverse("increment-post-clicks")
        response = self.client.post(
            url,
            {"slug": "nonexistent-slug"},
            HTTP_API_KEY=self.api_key,
            format="json"
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        data = response.json()
        
        self.assertIn("detail", data)
        self.assertEqual(data["detail"], "Post does not exist")
