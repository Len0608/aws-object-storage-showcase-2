"""
Exceptions module template for UAC Universal Extensions.

This module provides:
- Base ExecutionError class
- Standard exception types (DataValidationError, ConnectionError, etc.)
- ErrorManager singleton for error collection
- Exit code conventions

CUSTOMIZE:
- Add custom exception types for your extension
- Modify ErrorManager methods if needed
"""
from typing import Optional

class ExecutionError(Exception):
    """
    The default error raised by an extension.

    All extension errors must inherit from it.

    Attrs:
        exit_code: The exit code of the extension (for UAC)
        message: The error message for status description
    """

    exit_code: int = 1
    message: str = "Execution Failed"

    def __init__(self, message: Optional[str] = None):
        """
        Initialize exception.

        Args:
            message: Optional message that will be appended to the default message.

        Note:
            To return result data with errors, use error_manager.set_result()
            before raising the exception.
        """
        if message:
            self.message = f"{self.message}: {message}"

        super().__init__(self.message)

class DataValidationError(ExecutionError):
    """Raised when an input field is invalid."""
    exit_code = 20
    message = "Data Validation Error"

class UnexpectedSystemError(ExecutionError):
    """Raised for unexpected system errors."""
    exit_code = 1
    message = "System Error"

class ValidationError(ExecutionError):
    """
    Raised when a required input field is missing or empty.

    Use this when a field that must be provided by the user is absent,
    preventing any meaningful execution from proceeding.
    Exit code 20 signals a user configuration error to UAC.
    """
    exit_code = 20
    message = "Validation Error"

class AuthenticationError(ExecutionError):
    """
    Raised when AWS credential authentication fails.

    Use this when boto3 reports an invalid Access Key ID, auth failure,
    signature mismatch, or missing credentials (ClientError codes
    InvalidClientTokenId, AuthFailure, SignatureDoesNotMatch, or
    botocore.exceptions.NoCredentialsError). This is a non-transient
    error — the user must correct their IAM credentials.
    """
    exit_code = 1
    message = "Authentication Error"

class AccessDeniedError(ExecutionError):
    """
    Raised when the IAM user lacks permission for the requested S3 operation.

    Use this when boto3 raises a ClientError with code AccessDenied.
    This is a non-transient error — the IAM policy must be updated
    to grant the required s3:ListObjectsV2 or s3:PutObject permission.
    """
    exit_code = 1
    message = "Access Denied"

class BucketNotFoundError(ExecutionError):
    """
    Raised when the specified S3 bucket does not exist.

    Use this when boto3 raises a ClientError with code NoSuchBucket.
    This is a non-transient error — the user must verify the bucket
    name and region are correct.
    """
    exit_code = 1
    message = "Bucket Not Found"

class ConnectionError(ExecutionError):
    """
    Raised when a network connection to the AWS S3 endpoint fails.

    Use this when botocore raises EndpointConnectionError or
    ConnectTimeoutError. This is a transient error — retrying the
    task after a delay may succeed if the network issue resolves.
    """
    exit_code = 1
    message = "Connection Error"

class S3OperationError(ExecutionError):
    """
    Raised when an S3 API call fails for a reason other than auth,
    access, or missing bucket.

    Use this for any botocore ClientError not covered by the more
    specific exception types (e.g., unexpected server-side errors
    during list or upload). May be transient.
    """
    exit_code = 1
    message = "S3 Operation Error"

class LocalFileNotFoundError(ExecutionError):
    """
    Raised when the local file specified for upload cannot be accessed.

    Use this when the file at the given path does not exist
    (FileNotFoundError) or cannot be read due to insufficient
    permissions (PermissionError). This is a non-transient error —
    the user must supply a valid, readable file path.
    """
    exit_code = 1
    message = "Local File Not Found"
