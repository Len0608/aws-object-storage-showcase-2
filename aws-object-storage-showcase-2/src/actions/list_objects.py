"""List Objects action — lists all objects in an S3 bucket."""

import logging
import os

import botocore.exceptions

from actions.output import ActionOutput
from exceptions import (
    AuthenticationError,
    AccessDeniedError,
    BucketNotFoundError,
    ConnectionError,
    S3OperationError,
    ValidationError,
)
from fields.input import InputFields
from fields.output import OutputFields
from manager import ExtensionManager
from utility import S3ClientManager

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

# Default maximum number of objects to include in STDOUT table and Extension Output
_DEFAULT_MAX_RECORDS = 100


def list_objects(input_data: InputFields) -> ActionOutput:
    """List all objects in the specified S3 bucket.

    Paginates through all objects, renders an ASCII table on STDOUT (capped by
    UE_MAX_OUTPUT_RECORDS), and returns structured metadata for Extension Output.

    Args:
        input_data: Validated input fields from UAC.

    Returns:
        ActionOutput populated with bucket metadata and object list.

    Raises:
        ValidationError: If a required field is missing or empty.
        AuthenticationError: If AWS credential validation fails.
        AccessDeniedError: If the IAM user lacks s3:ListObjectsV2 permission.
        BucketNotFoundError: If the specified bucket does not exist.
        ConnectionError: If the S3 endpoint cannot be reached.
        S3OperationError: For any other S3 API failure.
    """
    logger.info("Starting list_objects action")
    logger.debug(
        "Input: action=%s, aws_region=%s, bucket_name=%s",
        input_data.action.value if input_data.action else None,
        input_data.aws_region.value if input_data.aws_region else None,
        input_data.bucket_name.value if input_data.bucket_name else None,
    )

    # --- Step 1: Input Validation ---
    _validate_required_fields(input_data)

    aws_region = input_data.aws_region.value.strip()
    bucket_name = input_data.bucket_name.value.strip()
    access_key_id = input_data.aws_credentials.user
    secret_access_key = input_data.aws_credentials.password

    # --- Step 2: Read Configuration ---
    max_records = _read_max_records()
    logger.debug("UE_MAX_OUTPUT_RECORDS resolved to: %d", max_records)

    # --- Initialize OutputFields for real-time UI updates ---
    output_fields = OutputFields()
    output_fields.update(status="Connecting to S3")

    # --- Step 3: Build S3 Client ---
    logger.info("Building S3 client for region: %s", aws_region)
    s3_client = S3ClientManager.get_client(
        access_key_id=access_key_id,
        secret_access_key=secret_access_key,
        region=aws_region,
    )

    # --- Step 4: Paginate and Collect All Objects ---
    output_fields.update(status="Listing objects")
    logger.info("Paginating objects in bucket: %s", bucket_name)

    all_objects = _paginate_objects(s3_client, bucket_name)
    total_count = len(all_objects)
    logger.info("Collected %d objects from bucket: %s", total_count, bucket_name)

    # --- Step 5: Apply Display Cap ---
    shown_count = min(total_count, max_records)
    display_objects = all_objects[:shown_count]
    logger.debug("Display cap: shown_count=%d of total_count=%d", shown_count, total_count)

    # --- Step 7: Set Output Fields ---
    output_fields.update(
        status=f"Success: Listed {total_count} objects",
        objects_found=str(total_count),
    )
    logger.info("list_objects action completed: total=%d, shown=%d", total_count, shown_count)

    # --- Step 8: Return ActionOutput (print_output() renders the table) ---
    return ActionOutput(
        bucket=bucket_name,
        region=aws_region,
        total_count=total_count,
        shown_count=shown_count,
        objects=display_objects,
    )


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _validate_required_fields(input_data: InputFields) -> None:
    """Raise ValidationError if any required field for List Objects is absent."""
    missing = []

    if not input_data.aws_credentials:
        missing.append("aws_credentials")
    if not input_data.aws_region or not input_data.aws_region.value.strip():
        missing.append("aws_region")
    if not input_data.bucket_name or not input_data.bucket_name.value.strip():
        missing.append("bucket_name")

    if missing:
        msg = f"Missing required field(s): {', '.join(missing)}"
        logger.error("Validation failed: %s", msg)
        raise ValidationError(msg)


def _read_max_records() -> int:
    """Read UE_MAX_OUTPUT_RECORDS from the environment; fall back to default."""
    raw = os.environ.get("UE_MAX_OUTPUT_RECORDS", "")
    try:
        value = int(raw)
        return value if value > 0 else _DEFAULT_MAX_RECORDS
    except (ValueError, TypeError):
        return _DEFAULT_MAX_RECORDS


def _paginate_objects(s3_client, bucket_name: str) -> list:
    """Paginate list_objects_v2 and return all objects as a list of dicts.

    Each dict contains:
        key          (str)  — object key
        size_bytes   (int)  — object size in bytes
        last_modified (str) — ISO 8601 UTC timestamp

    Raises:
        AuthenticationError, AccessDeniedError, BucketNotFoundError,
        ConnectionError, S3OperationError — mapped from botocore exceptions.
    """
    try:
        paginator = s3_client.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=bucket_name)

        collected = []
        for page in pages:
            for obj in page.get("Contents", []):
                last_modified = obj["LastModified"]
                # Convert timezone-aware datetime to ISO 8601 UTC string
                iso_str = last_modified.strftime("%Y-%m-%dT%H:%M:%SZ")
                collected.append(
                    {
                        "key": obj["Key"],
                        "size_bytes": obj["Size"],
                        "last_modified": iso_str,
                    }
                )
        return collected

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
