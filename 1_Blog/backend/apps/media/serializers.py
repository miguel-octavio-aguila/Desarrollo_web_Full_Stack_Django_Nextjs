from rest_framework import serializers
from botocore.signers import CloudFrontSigner
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta

from utils.s3_utils import rsa_signer
from .models import Media

class MediaSerializer(serializers.ModelSerializer):
    presigned_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Media
        fields = '__all__'

    def get_presigned_url(self, obj):
        if not obj.key:
            return None
        
        cloudfront_key_id = settings.AWS_CLOUDFRONT_KEY_ID
        cf_signer = CloudFrontSigner(cloudfront_key_id, rsa_signer)
        expire_date = timezone.now() + timedelta(seconds=60)
        obj_url = f"https://{settings.AWS_CLOUDFRONT_DOMAIN}/{obj.key}"
        signed_url = cf_signer.generate_presigned_url(obj_url, date_less_than=expire_date)
        return signed_url