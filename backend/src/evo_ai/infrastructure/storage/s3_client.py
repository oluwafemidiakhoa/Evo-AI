"""S3/MinIO storage client."""

import io
from typing import Optional

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from evo_ai.config import settings
from evo_ai.infrastructure.observability.logging import get_logger

logger = get_logger(__name__)


class S3StorageClient:
    """
    S3-compatible storage client (works with MinIO and AWS S3).

    Provides abstraction for storing and retrieving files like:
    - Generated reports
    - Chart visualizations
    - Export files
    """

    def __init__(self) -> None:
        """Initialize S3 client."""
        self.client = boto3.client(
            's3',
            endpoint_url=settings.s3_endpoint,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
            config=Config(signature_version='s3v4'),
        )
        self.bucket = settings.s3_bucket
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self) -> None:
        """Create bucket if it doesn't exist."""
        try:
            self.client.head_bucket(Bucket=self.bucket)
            logger.info("s3_bucket_exists", bucket=self.bucket)
        except ClientError:
            try:
                self.client.create_bucket(Bucket=self.bucket)
                logger.info("s3_bucket_created", bucket=self.bucket)
            except ClientError as e:
                logger.error("s3_bucket_creation_failed", bucket=self.bucket, error=str(e))
                raise

    async def upload_file(
        self,
        file_path: str,
        content: bytes | str,
        content_type: str = "application/octet-stream",
        metadata: Optional[dict] = None
    ) -> str:
        """
        Upload file to S3.

        Args:
            file_path: Path in bucket (e.g., "reports/round-123/summary.md")
            content: File content (bytes or string)
            content_type: MIME type
            metadata: Optional metadata tags

        Returns:
            Full S3 URL of uploaded file

        Example:
            url = await storage.upload_file(
                "reports/round-123.md",
                report_content,
                content_type="text/markdown",
                metadata={"round_id": "123"}
            )
        """
        if isinstance(content, str):
            content = content.encode('utf-8')

        try:
            self.client.upload_fileobj(
                io.BytesIO(content),
                self.bucket,
                file_path,
                ExtraArgs={
                    'ContentType': content_type,
                    'Metadata': metadata or {},
                }
            )
            logger.info("s3_file_uploaded", path=file_path, size=len(content))
            return f"s3://{self.bucket}/{file_path}"

        except ClientError as e:
            logger.error("s3_upload_failed", path=file_path, error=str(e))
            raise

    async def download_file(self, file_path: str) -> bytes:
        """
        Download file from S3.

        Args:
            file_path: Path in bucket

        Returns:
            File content as bytes

        Raises:
            ClientError: If file doesn't exist
        """
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=file_path)
            content = response['Body'].read()
            logger.info("s3_file_downloaded", path=file_path, size=len(content))
            return content

        except ClientError as e:
            logger.error("s3_download_failed", path=file_path, error=str(e))
            raise

    async def delete_file(self, file_path: str) -> bool:
        """
        Delete file from S3.

        Args:
            file_path: Path in bucket

        Returns:
            True if deleted, False if didn't exist
        """
        try:
            self.client.delete_object(Bucket=self.bucket, Key=file_path)
            logger.info("s3_file_deleted", path=file_path)
            return True

        except ClientError as e:
            logger.error("s3_delete_failed", path=file_path, error=str(e))
            return False

    async def file_exists(self, file_path: str) -> bool:
        """
        Check if file exists in S3.

        Args:
            file_path: Path in bucket

        Returns:
            True if exists, False otherwise
        """
        try:
            self.client.head_object(Bucket=self.bucket, Key=file_path)
            return True
        except ClientError:
            return False

    async def generate_presigned_url(
        self,
        file_path: str,
        expiration: int = 3600
    ) -> str:
        """
        Generate presigned URL for temporary file access.

        Args:
            file_path: Path in bucket
            expiration: URL validity in seconds (default 1 hour)

        Returns:
            Presigned URL
        """
        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket, 'Key': file_path},
                ExpiresIn=expiration
            )
            logger.info("s3_presigned_url_generated", path=file_path, expiration=expiration)
            return url

        except ClientError as e:
            logger.error("s3_presigned_url_failed", path=file_path, error=str(e))
            raise
