import uuid

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.text import slugify

from django_ckeditor_5.fields import CKEditor5Field

from core.storage_backends import PublicMediaStorage

from .utils import get_client_ip

from apps.media.models import Media
from apps.media.serializers import MediaSerializer
from django.utils.html import format_html

# This function is used to store the thumbnail in a specific directory
def blog_thumbnail_directory(instance, filename):
    sanitized_title = instance.title.replace(" ", "_")
    return "thumbnails/blog/{0}/{1}".format(sanitized_title, filename)

# This function is used to store the thumbnail in a specific directory
def category_thumbnail_directory(instance, filename):
    sanitized_name = instance.name.replace(" ", "_")
    return "thumbnails/blog_categories/{0}/{1}".format(sanitized_name, filename)

class Category(models.Model):
    # This field is used to create a unique identifier for the category
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # This field is used to create a tree of categories
    parent = models.ForeignKey("self", related_name="children", on_delete=models.CASCADE, blank=True, null=True)
    
    name = models.CharField(max_length=255)
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    thumbnail = models.ForeignKey(Media, on_delete=models.SET_NULL, related_name="blog_category_thumbnail", null=True, blank=True)
    slug = models.CharField(max_length=128)
    
    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

    def thumbnail_preview(self):
        if self.thumbnail:
            serializer = MediaSerializer(instance=self.thumbnail)
            url = serializer.data.get("presigned_url")
            if url:
                return format_html('<img src="{}" width="100" height="100" />', url)
        return "No thumbnail"
    
    thumbnail_preview.short_description = "Thumbnail Preview"


class Post(models.Model):
    # Manager for published posts
    class PostObject(models.Manager):
        def get_queryset(self):
            return super().get_queryset().filter(status="published")

    # Status options
    status_options = (
        ("draft", "Draft"),
        ("published", "Published"),
    )
    
    # This field is used to create a unique identifier for the post
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    title = models.CharField(max_length=128)
    description = models.CharField(max_length=256)
    content = CKEditor5Field('Content', config_name='default', blank=True, null=True)
    thumbnail = models.ForeignKey(Media, on_delete=models.SET_NULL, related_name="post_thumbnail", null=True, blank=True)
    
    keywords = models.CharField(max_length=128)
    slug = models.CharField(max_length=128)
    
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    status = models.CharField(max_length=10, choices=status_options, default="draft")
    
    objects = models.Manager() # Default manager
    post_published = PostObject() # Manager for published posts (custom manager)
    
    class Meta:
        ordering = ("status", "-created_at")

    def __str__(self):
        return self.title

    def thumbnail_preview(self):
        if self.thumbnail:
            serializer = MediaSerializer(instance=self.thumbnail)
            url = serializer.data.get("presigned_url")
            if url:
                return format_html('<img src="{}" width="100" height="100" />', url)
        return "No thumbnail"
    
    thumbnail_preview.short_description = "Thumbnail Preview"

class PostViews(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="post_views")
    ip_address = models.GenericIPAddressField()
    created_at = models.DateTimeField(auto_now_add=True)

class PostAnalytics(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="post_analytics")
    
    views = models.PositiveIntegerField(default=0)
    impressions = models.PositiveIntegerField(default=0)
    clicks = models.PositiveIntegerField(default=0)
    clicks_through_rate = models.FloatField(default=0)
    avg_time_on_page = models.FloatField(default=0)
    
    def update_click_through_rate(self):
        if self.impressions > 0:
            self.clicks_through_rate = (self.clicks / self.impressions) * 100
        else:
            self.clicks_through_rate = 0
        
        self.save()
    
    def increment_clicks(self):
        self.clicks += 1
        self.save()
        self.update_click_through_rate()
    
    def increment_impressions(self):
        self.impressions += 1
        self.save()
        self.update_click_through_rate()
    
    def increment_views(self, ip_address):
        if not PostViews.objects.filter(post=self.post, ip_address=ip_address).exists():
            PostViews.objects.create(post=self.post, ip_address=ip_address)
            self.views += 1
            self.save()
    
    class Meta:
        verbose_name = 'Post Analytics'
        verbose_name_plural = 'Post Analytics'


class Heading(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="headings")
    
    title = models.CharField(max_length=128)
    slug = models.CharField(max_length=128)
    level = models.IntegerField(
        choices=(
            (1, "H1"),
            (2, "H2"),
            (3, "H3"),
            (4, "H4"),
            (5, "H5"),
            (6, "H6"),
        )
    )
    order = models.PositiveIntegerField()
    
    class Meta:
        ordering = ["order"]
        
    # This method is used to create a slug for the heading
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

@receiver(post_save, sender=Post)
def create_post_analytics(sender, instance, created, **kwargs):
    if created:
        PostAnalytics.objects.create(post=instance)
