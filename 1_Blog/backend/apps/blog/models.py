from django.db import models
from django.utils import timezone

# This function is used to store the thumbnail in a specific directory
def blog_thumbnail_directory(instance, filename):
    return "blog/{0}/{1}".format(instance.title, filename)

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
    
    title = models.CharField(_("Title"), max_length=128)
    description = models.CharField(_("Description"), max_length=256)
    content = models.TextField(_("Content"))
    thumbnail = models.ImageField(_("Thumbnail"), upload_to=blog_thumbnail_directory)
    
    keywords = models.CharField(_("Keywords"), max_length=128)
    slug = models.CharField(_("Slug"), max_length=128)
    
    created_at = models.DateTimeField(_("Created at"), default=timezone.now)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)
    
    status = models.CharField(_("Status"), max_length=10, choices=status_options, default="draft")
    
    objects = models.Manager() # Default manager
    published = PostObject() # Manager for published posts (custom manager)
    
    class Meta:
        ordering = ("-published")
        
    def __str__(self):
        return self.title
