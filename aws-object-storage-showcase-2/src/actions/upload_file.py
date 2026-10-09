"""Upload File action — uploads a local file to an S3 bucket."""

import logging
import os

import botocore.exceptions

from actions.output import ActionOutput
from exceptions import (
    AuthenticationError,
    AccessDeniedError,
    BucketNotFoundError,
    ConnectionError,
    LocalFileNotFoundError,
    S3OperationError,
    ValidationError,
)
from fields.input import InputFields
from fields.output import OutputFields
from manager import ExtensionManager
from utility import S3ClientManager, SizeFormatter

logger = logging.getLogger("UNV")
extension_manager = ExtensionManager()

# Mapping from botocore ClientError codes to extension exception classes
_CLIENT_ERROR_MAP = {
    "InvalidClientTokenId": AuthenticationError,
    "AuthFailure": AuthenticationError,
    "SignatureDoesNotMatch": AuthenticationError,
    "AccessDenied": AccessDeniedError,
    "NoSuchBucket": BucketNotFoundError,
}


def upload_file(input_data: InputFields) -> ActionOutput:
    """Upload a local file to the specified S3 bucket and key.

    Validates that the local file exists, then uploads it via boto3's
    upload_file() (which uses s3transfer for transparent multipart handling).
    Always overwrites an existing object at the target key without a
    pre-existence check.

    Args:
        input_data: Validated input fields from UAC.

    Returns:
        ActionOutput populated with upload metadata.

    Raises:
        ValidationError: If a required field is missing or empty.
        LocalFileNotFoundError: If the local file does not exist or is unreadable.
        AuthenticationError: If AWS credential validation fails.
        AccessDeniedError: If the IAM user lacks s3:PutObject permission.
        BucketNotFoundError: If the specified bucket does not exist.
        ConnectionError: If the S3 endpoint cannot be reached.
        S3OperationError: For any other S3 API failure.
    """
    logger.info("Starting upload_file action")
    logger.debug(
        "Input: action=%s, aws_region=%s, bucket_name=%s, local_file=%s, s3_object_key=%s",
        input_data.action.value if input_data.action else None,
        input_data.aws_region.value if input_data.aws_region else None,
        input_data.bucket_name.value if input_data.bucket_name else None,
        input_data.local_file.value if input_data.local_file else None,
        input_data.s3_object_key.value if input_data.s3_object_key else None,
    )

    # --- Step 1: Input Validation ---
    _validate_required_fields(input_data)

    aws_region = input_data.aws_region.value.strip()
    bucket_name = input_data.bucket_name.value.strip()
    local_file = input_data.local_file.value.strip()
    s3_object_key = input_data.s3_object_key.value.strip()
    access_key_id = input_data.aws_credentials.user
    secret_access_key = input_data.aws_credentials.password

    # --- Initialize OutputFields for real-time UI updates ---
    output_fields = OutputFields()
    output_fields.update(status="Validating local file")

    # --- Step 2: Local File Validation ---
    size_bytes = _validate_local_file(local_file)
    logger.debug("Local file validated: %s (%d bytes)", local_file, size_bytes)

    # --- Step 3: Build S3 Client ---
    output_fields.update(status="Connecting to S3")
    logger.info("Building S3 client for region: %s", aws_region)
    s3_client = S3ClientManager.get_client(
        access_key_id=access_key_id,
        secret_access_key=secret_access_key,
        region=aws_region,
    )

    # --- Step 4: Upload File ---
    output_fields.update(status="Uploading file")
    logger.info(
        "Uploading %s to s3://%s/%s",
        local_file,
        bucket_name,
        s3_object_key,
    )
    _upload(s3_client, local_file, bucket_name, s3_object_key)

    # --- Step 5: Construct S3 URI ---
    s3_uri = f"s3://{bucket_name}/{s3_object_key}"
    logger.info("Upload successful: %s", s3_uri)

    # --- Step 7: Set Output Fields ---
    output_fields.update(
        status=f"Success: Uploaded {s3_uri}",
        uploaded_object=s3_uri,
    )

    logger.info("upload_file action completed: %s", s3_uri)

    # --- Step 8: Return ActionOutput (print_output() renders STDOUT confirmation) ---
    action_output = ActionOutput(
        bucket=bucket_name,
        region=aws_region,
        key=s3_object_key,
        s3_uri=s3_uri,
        size_bytes=size_bytes,
    )
    # Store local_file path so print_output() can use it in the confirmation line
    action_output._local_file = local_file
    return action_output


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _validate_required_fields(input_data: InputFields) -> None:
    """Raise ValidationError if any required field for Upload File is absent."""
    missing = []

    if not input_data.aws_credentials:
        missing.append("aws_credentials")
    if not input_data.aws_region or not input_data.aws_region.value.strip():
        missing.append("aws_region")
    if not input_data.bucket_name or not input_data.bucket_name.value.strip():
        missing.append("bucket_name")
    if not input_data.local_file or not input_data.local_file.value.strip():
        missing.append("local_file")
    if not input_data.s3_object_key or not input_data.s3_object_key.value.strip():
        missing.append("s3_object_key")

    if missing:
        msg = f"Missing required field(s): {', '.join(missing)}"
        logger.error("Validation failed: %s", msg)
        raise ValidationError(msg)


def _validate_local_file(local_file: str) -> int:
    """Check that the local file exists and is readable; return its size in bytes.

    Args:
        local_file: Absolute path to the file on the agent host.

    Returns:
        File size in bytes.

    Raises:
        LocalFileNotFoundError: If the file does not exist or cannot be read.
    """
    try:
        if not os.path.exists(local_file):
            msg = f"Local file not found: {local_file}"
            logger.error(msg)
            raise LocalFileNotFoundError(msg)
        size_bytes = os.path.getsize(local_file)
        return size_bytes
    except PermissionError as exc:
        msg = f"Local file not found: {local_file}"
        logger.error("Permission denied reading file %s: %s", local_file, str(exc))
        raise LocalFileNotFoundError(msg)


def _upload(s3_client, local_file: str, bucket_name: str, s3_object_key: str) -> None:
    """Call s3_client.upload_file() and map botocore exceptions to extension types.

    Args:
        s3_client: Configured boto3 S3 client.
        local_file: Absolute path to the local file.
        bucket_name: Target S3 bucket.
        s3_object_key: Target S3 object key.

    Raises:
        AuthenticationError, AccessDeniedError, BucketNotFoundError,
        ConnectionError, S3OperationError — mapped from botocore exceptions.
    """
    try:
        s3_client.upload_file(local_file, bucket_name, s3_object_key)

    except botocore.exceptions.NoCredentialsError as exc:
        logger.error("No credentials available: %s", str(exc))
        raise AuthenticationError(str(exc))

    except botocore.exceptions.EndpointConnectionError as exc:
        logger.error("Endpoint connection error: %s", str(exc))
        raise ConnectionError(str(exc))

    except botocore.exceptions.ConnectTimeoutError as exc:
        logger.error("Connection timed out: %s", str(exc))
        raise ConnectionError(str(exc))

    except botocore.exceptions.ClientError as exc:
        error_code = exc.response["Error"]["Code"]
        error_message = exc.response["Error"]["Message"]
        logger.error("S3 ClientError [%s]: %s", error_code, error_message)

        exc_class = _CLIENT_ERROR_MAP.get(error_code, S3OperationError)
        raise exc_class(f"[{error_code}] {error_message}")
