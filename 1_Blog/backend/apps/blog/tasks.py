from celery import shared_task

import logging

import redis

from django.conf import settings
from .models import PostAnalytics, Post

logger = logging.getLogger(__name__)

redis_client = redis.Redis(host=settings.REDIS_HOST, port=6379, db=0)


@shared_task
def increment_post_impressions(post_id):
    """
    Increment the number of impressions for an associated post
    """
    try:
        analytics, created = PostAnalytics.objects.get_or_create(post__id=post_id)
        analytics.increment_impressions()
        analytics.save()
    except PostAnalytics.DoesNotExist:
        logger.error("Post analytics does not exist for post id: %s", post_id)
    except Exception as e:
        logger.error("An unexpected error occurred while updating post analytics: %s", str(e))

@shared_task
def increment_post_views(slug, ip_address):
    """
    Increment the views of a post
    """
    try:
        post = Post.objects.get(slug=slug)
        post_analytics, _ = PostAnalytics.objects.get_or_create(post=post)
        post_analytics.increment_views(ip_address)
        post_analytics.save()
    except Exception as e:
        logger.info(f"Error incrementing views for Post slug {slug}: {str(e)}")

@shared_task
def sync_impressions_to_db():
    """
    Sync the number of impressions for all posts from redis to the database
    """
    keys = redis_client.keys("post:impressions:*")
    try:
        for key in keys:
            post_id = key.decode("utf-8").split(":")[-1]
            impressions = int(redis_client.get(key))
            
            analytics, _ = PostAnalytics.objects.get_or_create(post__id=post_id)
            analytics.impressions += impressions
            analytics.save()
            
            analytics.update_click_through_rate()
            
            redis_client.delete(key)
    except Exception as e:
        logger.error("An unexpected error occurred while syncing impressions to database: %s", str(e))