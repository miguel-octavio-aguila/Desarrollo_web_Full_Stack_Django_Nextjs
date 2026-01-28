import logging

from django.conf import settings
import boto3
from botocore.exceptions import ClientError
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes

logger = logging.getLogger(__name__)

def generate_presigned_url(s3_client, client_method, method_parameters, expires_in):
    """
    Generate a presigned URL to access an S3 object.
    
    : param s3_client: Boto3 S3 client
    : param client_method: Method of the S3 client to generate the URL for
    : param method_parameters: Parameters for the client method
    : param expires_in: Time in seconds for the URL to expire
    : return: Presigned URL as a string
    """
    try:
        presigned_url = s3_client.generate_presigned_url(
            ClientMethod=client_method,
            Params=method_parameters,
            ExpiresIn=expires_in,
        )
        logger.info("Generated presigned URL: %s", presigned_url)
    except ClientError as e:
        logger.exception("Error generating presigned URL: %s", client_method)
        raise
    return presigned_url

def rsa_signer(message):
    try:
        private_key = serialization.load_pem_private_key(
            settings.AWS_CLOUDFRONT_KEY,
            password=None,
            backend=default_backend()
        )

        signature = private_key.sign(
            message,
            padding.PKCS1v15(),
            hashes.SHA1(),
        )
        return signature
    except ClientError as e:
        logger.exception("Error signing message: %s", message)
        raise
