import mimetypes
from typing import Optional, TYPE_CHECKING
import aioboto3
from botocore.config import Config
from src.core.config import settings

if TYPE_CHECKING:
    from aiobotocore.client import AioBaseClient
    S3ServiceClient = AioBaseClient

class S3Client:
    """
    S3-Compatible Storage Client (Optimized for Backblaze B2).
    Handles secure file uploads and time-limited URL generation.
    """

    def __init__(self):
        self.bucket_name: str = settings.S3_BUCKET_NAME
        self.session = aioboto3.Session()

        # Backblaze requires specific config for S3 compatibility
        self.client_config = Config(
            signature_version='s3v4',
            retries={'max_attempts': 3, 'mode': 'standard'}
        )

    def _get_client(self):
        """Internal helper to create the async client context."""
        return self.session.client(
            's3',
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
            region_name=settings.S3_REGION,
            config=self.client_config
        )

    # --- Core Operations ---

    async def generate_presigned_url(self, object_key: Optional[str], expires_in: int = 3600) -> Optional[str]:
        """
        Generates a secure, temporary URL for a private file.
        Default expiry is 1 hour.
        """
        if not object_key:
            return None

        async with self._get_client() as s3:
            # Type hint the dynamic s3 client
            s3_client: "S3ServiceClient" = s3
            return await s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': object_key},
                ExpiresIn=expires_in
            )

    async def upload_file(self, content: bytes, object_key: str, content_type: Optional[str] = None) -> str:
        """
        Uploads binary data to the bucket and returns the object key.
        Guesses content_type from object_key if not provided.
        """
        if not content_type:
            content_type, _ = mimetypes.guess_type(object_key)
            content_type = content_type or 'application/octet-stream'

        async with self._get_client() as s3:
            s3_client: "S3ServiceClient" = s3
            await s3_client.put_object(
                Bucket=self.bucket_name,
                Key=object_key,
                Body=content,
                ContentType=content_type
            )
            return object_key

    async def delete_file(self, object_key: str):
        """Removes a file from the bucket."""
        async with self._get_client() as s3:
            s3_client: "S3ServiceClient" = s3
            await s3_client.delete_object(Bucket=self.bucket_name, Key=object_key)

    async def download_file(self, object_key: str) -> bytes:
        """Downloads a file from the bucket and returns its content as bytes."""
        async with self._get_client() as s3:
            s3_client: "S3ServiceClient" = s3
            response = await s3_client.get_object(Bucket=self.bucket_name, Key=object_key)
            return await response['Body'].read()