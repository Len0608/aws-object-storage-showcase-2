<!-- generated: 2026-10-09 00:00 -->

# Project Analysis — Universal Extension v1.0.0

**Extension name:** `aws-object-storage-showcase-2`  
**API level:** 1.6.0  
**Python requirement:** >=3.11  
**Template name:** Aws Object Storage Showcase 2  
**Variable prefix:** `ops_var`

---

## Purpose

AWS S3 integration that enables UAC tasks to list all objects in an S3 bucket or upload a local file from the agent host to an S3 bucket, authenticated via IAM User credentials stored in a UAC Credential.

---

## Execution Modes / Actions

| Mode | Trigger | Description |
|------|---------|-------------|
| List Objects | `action` = `"List Objects"` (default) | Paginates through all objects in the specified S3 bucket using `list_objects_v2`, renders an ASCII table on STDOUT (capped by `UE_MAX_OUTPUT_RECORDS`, default 100), and returns bucket metadata and total object count in structured output. |
| Upload File | `action` = `"Upload File"` | Validates the local file exists on the agent host, builds an S3 client, and uploads the file via `boto3.upload_file()` (transparent multipart). Overwrites any existing object at the target key without a pre-existence check. Returns the full S3 URI of the uploaded object. |

---

## Complete Field Table

| Seq | Name | Label | Mapping | Type | Required | Default | Restriction | Notes |
|-----|------|-------|---------|------|----------|---------|-------------|-------|
| 0 | `action` | Action | Choice Field 1 | Choice | No | `"List Objects"` | No Restriction | Dispatches to `list_objects` or `upload_file` via ACTION_MAPPER. Validated against `["List Objects", "Upload File"]`. |
| 1 | `aws_credentials` | AWS Credentials | Credential Field 1 | Credential | Yes | — | No Restriction | UAC Credential; `user` = AWS Access Key ID, `password` = AWS Secret Access Key. |
| 2 | `aws_region` | AWS Region | Text Field 1 | Text | Yes | — | No Restriction | AWS region identifier, e.g. `us-east-1`. Must be non-empty. |
| 3 | `bucket_name` | Bucket Name | Text Field 2 | Text | Yes | — | No Restriction | Target S3 bucket name. Must be non-empty. |
| 4 | `local_file` | Local File Path | Text Field 3 | Text | Conditionally | — | No Restriction | Absolute path to the file on the agent host. Required only when `action = "Upload File"`. Hidden (no space) when `action = "List Objects"`. |
| 5 | `s3_object_key` | S3 Object Key | Text Field 4 | Text | Conditionally | — | No Restriction | Target S3 object key (path/filename). Required only when `action = "Upload File"`. Hidden (no space) when `action = "List Objects"`. |
| 6 | `status` | Status | Text Field 5 | Text | — | — | Output Only | Real-time execution status updated by both actions. Shown in list view (`defaultListView: true`) and marked `extensionStatus: true`. Preserved on rerun. |
| 7 | `objects_found` | Objects Found | Text Field 6 | Text | — | — | Output Only | Total object count; set only by `list_objects`. Hidden (no space) when `action = "Upload File"`. Preserved on rerun. |
| 8 | `uploaded_object` | Uploaded Object | Text Field 7 | Text | — | — | Output Only | Full S3 URI (`s3://<bucket>/<key>`) of the uploaded object; set only by `upload_file`. Hidden (no space) when `action = "List Objects"`. Preserved on rerun. |

---

## Cross-References

### Always Required
- `aws_credentials` — needed by both actions to authenticate against AWS.
- `aws_region` — needed by both actions to build the S3 client.
- `bucket_name` — needed by both actions as the target bucket.

### Conditionally Required (enforced in `__post_init__` and action-level validation)
- `local_file` — required when `action = "Upload File"`.
- `s3_object_key` — required when `action = "Upload File"`.

### Visibility Dependencies (`showIfField` references `fieldMapping` value)
| Field | Show When | Hide When |
|-------|-----------|-----------|
| `local_file` | `Choice Field 1` = `"Upload File"` | action is `"List Objects"` |
| `s3_object_key` | `Choice Field 1` = `"Upload File"` | action is `"List Objects"` |
| `objects_found` | `Choice Field 1` = `"List Objects"` | action is `"Upload File"` |
| `uploaded_object` | `Choice Field 1` = `"Upload File"` | action is `"List Objects"` |

### Mutually Exclusive Output Fields
- `objects_found` is populated exclusively by `List Objects`.
- `uploaded_object` is populated exclusively by `Upload File`.

---

## Error Handling Table

| Scope | Error | Handling |
|-------|-------|----------|
| Field validation (`__post_init__`) | `action` value not in `["List Objects", "Upload File"]` | `DataValidationError` (exit_code=20); collected into `ExtensionManager`, re-raised as single error |
| Field validation (`__post_init__`) | `aws_region` or `bucket_name` is empty string | `DataValidationError` (exit_code=20) |
| Field validation (`__post_init__`) | `local_file` or `s3_object_key` absent/empty when action is `Upload File` | `DataValidationError` (exit_code=20) |
| Action pre-check (`list_objects`) | Missing `aws_credentials`, `aws_region`, or `bucket_name` | `ValidationError` (exit_code=20) |
| Action pre-check (`upload_file`) | Missing any of the five required fields for upload | `ValidationError` (exit_code=20) |
| Upload File — file system | Local file path not found or permission denied | `LocalFileNotFoundError` (exit_code=1) |
| Both actions — AWS auth | `NoCredentialsError`, `InvalidClientTokenId`, `AuthFailure`, `SignatureDoesNotMatch` | `AuthenticationError` (exit_code=1) |
| Both actions — IAM permissions | `ClientError` code `AccessDenied` | `AccessDeniedError` (exit_code=1) |
| Both actions — bucket existence | `ClientError` code `NoSuchBucket` | `BucketNotFoundError` (exit_code=1) |
| Both actions — network | `EndpointConnectionError`, `ConnectTimeoutError` | `ConnectionError` (exit_code=1) |
| Both actions — other S3 API | Any unrecognised `ClientError` code | `S3OperationError` (exit_code=1) |
| Extension-level catch-all | Any uncaught `Exception` | `UnexpectedSystemError` (exit_code=1); error added to `ExtensionManager` |
| All `ExecutionError` subclasses | — | Caught in `extension_start()`: `build_result()` called with `exit_code` and `status_description` from exception; `InputFields` rebuilt with `_skip_validation=True` to preserve input in output |
