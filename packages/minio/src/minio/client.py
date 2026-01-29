import boto3
from botocore.exceptions import ClientError

from .settings import MinIOSettings


class MinIOClient:
    def __init__(self, settings: MinIOSettings | None = None):
        self.settings = settings or MinIOSettings()
        self._client = boto3.client(
            "s3",
            endpoint_url=self.settings.endpoint_url,
            aws_access_key_id=self.settings.access_key,
            aws_secret_access_key=self.settings.secret_key,
        )

    def ensure_bucket(self, bucket_name: str | None = None) -> None:
        bucket = bucket_name or self.settings.bucket_name
        try:
            self._client.head_bucket(Bucket=bucket)
        except ClientError:
            self._client.create_bucket(Bucket=bucket)

    def upload_bytes(
        self,
        object_name: str,
        data: bytes,
        content_type: str = "application/octet-stream",
        bucket_name: str | None = None,
    ) -> str:
        bucket = bucket_name or self.settings.bucket_name
        self.ensure_bucket(bucket)

        self._client.put_object(
            Bucket=bucket,
            Key=object_name,
            Body=data,
            ContentType=content_type,
        )
        return object_name

    def download_bytes(
        self,
        object_name: str,
        bucket_name: str | None = None,
    ) -> bytes:
        bucket = bucket_name or self.settings.bucket_name
        response = self._client.get_object(Bucket=bucket, Key=object_name)
        return response["Body"].read()


_default_client: MinIOClient | None = None


def get_minio_client(settings: MinIOSettings | None = None) -> MinIOClient:
    global _default_client
    if _default_client is None:
        _default_client = MinIOClient(settings)
    return _default_client
