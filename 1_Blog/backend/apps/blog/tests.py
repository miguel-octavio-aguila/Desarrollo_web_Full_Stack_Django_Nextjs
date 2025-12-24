from django.test import TestCase

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
        