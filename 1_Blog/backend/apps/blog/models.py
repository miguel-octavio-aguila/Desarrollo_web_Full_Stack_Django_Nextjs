import uuid

from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from django_ckeditor_5.fields import CKEditor5Field


# This function is used to store the thumbnail in a specific directory
def blog_thumbnail_directory(instance, filename):
    return "blog/{0}/{1}".format(instance.title, filename)

# This function is used to store the thumbnail in a specific directory
def category_thumbnail_directory(instance, filename):
    return "blog_categories/{0}/{1}".format(instance.name, filename)

class Category(models.Model):
    # This field is used to create a unique identifier for the category
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # This field is used to create a tree of categories
    parent = models.ForeignKey("self", related_name="children", on_delete=models.CASCADE, blank=True, null=True)
    
    name = models.CharField(max_length=255)
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    thumbnail = models.ImageField(upload_to=category_thumbnail_directory, blank=True, null=True)
    slug = models.CharField(max_length=128)
    
    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

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
    thumbnail = models.ImageField(upload_to=blog_thumbnail_directory)
    
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

class PostViews(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.PROTECT, related_name="post_views")
    ip_address = models.GenericIPAddressField()
    created_at = models.DateTimeField(auto_now_add=True)

class Heading(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    post = models.ForeignKey(Post, on_delete=models.PROTECT, related_name="headings")
    
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
