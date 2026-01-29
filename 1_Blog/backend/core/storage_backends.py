from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage

class StaticStorage(S3Boto3Storage):
    """Static files storage using S3 directly (not CloudFront) to avoid signed URL requirements"""
    location = "static"
    custom_domain = settings.AWS_S3_CUSTOM_DOMAIN  # Use S3 domain directly, not CloudFront
    default_acl = "public-read"


class PublicMediaStorage(S3Boto3Storage):
    location = "media"
    default_acl = "public-read"
    file_overwrite = False  # Prevents overwriting existing files