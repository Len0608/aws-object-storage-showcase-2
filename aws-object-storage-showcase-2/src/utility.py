"""
Utility module for the AWS Object Storage Showcase 2 extension.

Provides:
- S3ClientManager: builds a boto3 S3 client with explicit IAM credentials
- SizeFormatter: converts raw byte counts to human-readable size strings
"""

import logging

import boto3
import boto3.session

logger = logging.getLogger("UNV")


class S3ClientManager:
    """
    Creates and returns a fully configured boto3 S3 client.

    Credentials are supplied explicitly; no fallback to the boto3
    default credential discovery chain (environment variables,
    instance metadata, shared credentials file) occurs.
    """

    @staticmethod
    def get_client(
        access_key_id: str,
        secret_access_key: str,
        region: str,
    ) -> "boto3.client":
        """
        Build and return a boto3 S3 client with explicit credentials.

        Args:
            access_key_id: AWS IAM Access Key ID.
            secret_access_key: AWS IAM Secret Access Key.
            region: AWS region identifier (e.g. "us-east-1").

        Returns:
            A configured boto3 S3 client object.

        Raises:
            Any exception raised by boto3 during client construction
            (e.g. invalid region) is propagated directly to the caller.
        """
        logger.info("Building S3 client for region: %s", region)
        logger.debug(
            "S3 client parameters: region=%s, access_key_id=%s",
            region,
            "***" if access_key_id else None,
        )

        session = boto3.session.Session()
        client = session.client(
            "s3",
            region_name=region,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
        )

        logger.info("S3 client created successfully")
        return client


class SizeFormatter:
    """
    Converts raw byte counts to compact human-readable size strings.

    Uses binary prefixes (1 KB = 1024 bytes).
    """

    _KB: int = 1024
    _MB: int = 1024 * 1024
    _GB: int = 1024 * 1024 * 1024

    @staticmethod
    def format(size_bytes: int) -> str:
        """
        Convert an integer byte count to a human-readable size string.

        Conversion rules:
          - 0 bytes              → "0 B"
          - < 1024 bytes         → "X B"   (no decimal)
          - 1024 ≤ bytes < 1 MB  → "X.X KB" (1 decimal place)
          - 1 MB ≤ bytes < 1 GB  → "X.X MB" (1 decimal place)
          - ≥ 1 GB               → "X.X GB" (1 decimal place)

        Args:
            size_bytes: Raw file or object size in bytes. Must be >= 0.

        Returns:
            Human-readable size string (e.g. "0 B", "42 B", "1.2 MB").
        """
        if size_bytes < SizeFormatter._KB:
            return f"{size_bytes} B"
        if size_bytes < SizeFormatter._MB:
            return f"{size_bytes / SizeFormatter._KB:.1f} KB"
        if size_bytes < SizeFormatter._GB:
            return f"{size_bytes / SizeFormatter._MB:.1f} MB"
        return f"{size_bytes / SizeFormatter._GB:.1f} GB"
