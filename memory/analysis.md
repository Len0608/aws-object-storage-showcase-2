# AWS Object Storage Showcase 2 - Implementation Analysis

**Extension Name:** *AWS Object Storage Showcase 2 (aws-object-storage-showcase-2)*
**Universal Template Name:** *Aws Object Storage Showcase 2*
**Target Platform:** Linux

---

## Extension Overview

This extension provides a self-contained AWS S3 integration that demonstrates two fundamental S3 operations from a UAC agent host: listing all objects in a bucket and uploading a local file to a bucket. It is an MVP/demo integration. All Python dependencies are bundled with the extension archive; no installation on the UAC agent host is required. Authentication is exclusively via IAM User credentials (Access Key ID + Secret Access Key) supplied through a UAC Credential Field.

---

# Template Fields

## 1. Input Fields

**action**
- **Type**: Choice Field (Single-select)
- **Visible When**: always
- **Required When**: always
- **Options**:
  - `List Objects` — Lists all objects in the specified S3 bucket with size and last-modified metadata
  - `Upload File` — Uploads a local file from the agent host to the specified S3 bucket and key
- **Default Value**: `List Objects`
- **Validation**:
  - Must be one of the defined options
- **Purpose**: Selects which S3 operation to perform; controls conditional visibility of action-specific fields

---

**aws_credentials**
- **Type**: Credential Field
- **Visible When**: always
- **Required When**: always
- **Validation**:
  - Must reference a valid UAC Credential entity
  - `user` attribute must contain the AWS Access Key ID
  - `password` attribute must contain the AWS Secret Access Key
- **Purpose**: Supplies IAM User credentials for authenticating with the AWS S3 API. Accessed as `input_data.aws_credentials.user` (Access Key ID) and `input_data.aws_credentials.password` (Secret Access Key)

---

**aws_region**
- **Type**: Text Field
- **Visible When**: always
- **Required When**: always
- **Validation**:
  - Must be a non-empty string
  - Must be a valid AWS region identifier (e.g., `us-east-1`, `eu-west-1`, `ap-southeast-2`)
- **Purpose**: Specifies the AWS region endpoint for all S3 API calls
- **Example**: `us-east-1`

---

**bucket_name**
- **Type**: Text Field
- **Visible When**: always
- **Required When**: always
- **Validation**:
  - Must be a non-empty string
- **Purpose**: Name of the target AWS S3 bucket for both List Objects and Upload File actions
- **Example**: `my-demo-bucket`

---

**local_file**
- **Type**: Text Field
- **Visible When**: `action` value is equal to "Upload File". It is required when it's visible
- **Required When**: `action` value is equal to "Upload File"
- **Validation**:
  - Must be a non-empty absolute path string
  - Must refer to a file that exists and is readable on the agent host (validated at runtime before S3 connection)
- **Purpose**: Full absolute path to the local file on the UAC agent host that will be uploaded to S3
- **Example**: `/home/stonebranch/data/report.csv`

---

**s3_object_key**
- **Type**: Text Field
- **Visible When**: `action` value is equal to "Upload File". It is required when it's visible
- **Required When**: `action` value is equal to "Upload File"
- **Validation**:
  - Must be a non-empty string
- **Purpose**: Target S3 object key (path and filename) under which the file will be stored in the bucket. Overwrites existing object at this key without a pre-existence check
- **Example**: `reports/2024/q4-report.csv`

---

## 2. Output Fields

**status**
- **Type**: Text Output
- **Purpose**: Short human-readable description of the execution outcome — set to a success message on success, or to the error message on failure. Always populated regardless of action or outcome
- **Examples**: `"Success: Listed 42 objects"`, `"Success: Uploaded s3://my-demo-bucket/reports/q4.csv"`, `"Error: Bucket 'bad-bucket' not found or not accessible"`

---

**objects_found**
- **Type**: Text Output
- **Visible When**: `action` is "List Objects"
- **Purpose**: The true total count of objects in the bucket, unaffected by the display cap. Set only on successful List Objects execution
- **Examples**: `"42"`, `"4532"`, `"0"`

---

**uploaded_object**
- **Type**: Text Output
- **Visible When**: `action` is "Upload File"
- **Purpose**: The full S3 URI of the successfully uploaded object. Set only on successful Upload File execution
- **Examples**: `"s3://my-demo-bucket/reports/q4.csv"`, `"s3://staging-bucket/data/raw.json"`

---

## 3. Field Ordering

The task form uses a **2-column grid layout**.

**Field Order (Visual Layout):**

```
┌─────────────────────────────────────────┐
│                  action                 │  ← Full-width
├─────────────────────────────────────────┤
│             aws_credentials             │  ← Full-width (credential)
├─────────────────────────────────────────┤
│   aws_region        │   bucket_name     │  ← Half-width pair
├─────────────────────┴───────────────────┤
│              local_file                 │  ← Full-width (Upload File only)
├─────────────────────────────────────────┤
│             s3_object_key               │  ← Full-width (Upload File only)
├─────────────────────────────────────────┤
│                 status                  │  ← Full-width (output only)
├─────────────────────────────────────────┤
│             objects_found               │  ← Full-width (output only, List Objects)
├─────────────────────────────────────────┤
│            uploaded_object              │  ← Full-width (output only, Upload File)
└─────────────────────────────────────────┘
```

---

# Actions

## Action 1: List Objects

**Description**: Connects to AWS S3 using the provided IAM credentials and region, paginates through all objects in the specified bucket, renders an ASCII table on STDOUT, caps display at the `UE_MAX_OUTPUT_RECORDS` environment variable limit (default 100), and emits a structured Extension Output JSON with full object metadata up to the cap.

### Input Requirements

- **action** — must be "List Objects"
- **aws_credentials** — provides Access Key ID and Secret Access Key
- **aws_region** — identifies the S3 endpoint
- **bucket_name** — the target bucket to list

### Execution Flow

**Step 1 — Input Validation:**
- Verify `aws_credentials`, `aws_region`, and `bucket_name` are all non-empty. If any are missing, set `status` output field to the error message and exit with return code 20.

**Step 2 — Read Configuration:**
- Read `UE_MAX_OUTPUT_RECORDS` environment variable; parse as integer; default to `100` if absent or non-integer.

**Step 3 — Build S3 Client:**
- Instantiate a boto3 S3 client using explicit credentials: `aws_access_key_id = input_data.aws_credentials.user`, `aws_secret_access_key = input_data.aws_credentials.password`, `region_name = input_data.aws_region`. No default credential chain or instance metadata fallback.

**Step 4 — Paginate and Collect All Objects:**
- Use boto3's built-in paginator for `list_objects_v2` on `bucket_name`. Iterate all pages.
- For each object in each page, collect: `key` (string), `size_bytes` (integer), `last_modified` (datetime, converted to ISO 8601 UTC string for JSON output).
- Accumulate all objects into a single list `all_objects`. `total_count = len(all_objects)`.

**Step 5 — Apply Display Cap:**
- `shown_count = min(total_count, max_records)` where `max_records` is the value from Step 2.
- `display_objects = all_objects[:shown_count]`

**Step 6 — Render STDOUT Table:**
- For each object in `display_objects`, compute:
  - `human_size`: convert `size_bytes` to human-readable string using SizeFormatter (e.g., "42 KB", "1.2 MB").
  - `last_modified_str`: format the datetime as `"YYYY-MM-DD HH:MM"` (UTC).
- Build a list of rows: `[key, human_size, last_modified_str]`.
- Render the table using `tabulate` with `tablefmt="rounded_outline"` and headers `["Object Key", "Size", "Last Modified"]`.
- Print the table to STDOUT.
- Print `"<total_count> objects found"` after the table.
- If `total_count > shown_count`, print the truncation notice on a new line: `"Note: Showing <shown_count> of <total_count> objects. Set UE_MAX_OUTPUT_RECORDS environment variable to increase this limit."`

**Step 7 — Set Output Fields:**
- `output_data.objects_found = str(total_count)` (always the true total).
- `output_data.status = f"Success: Listed {total_count} objects"`

**Step 8 — Return Extension Output:**
- Construct and return the result object (see Output Examples below).
- Exit with return code 0.

### Output Examples

**STDOUT** (untruncated, 2 objects):
```
╭──────────────────────────────────┬──────────┬─────────────────────╮
│ Object Key                       │ Size     │ Last Modified       │
├──────────────────────────────────┼──────────┼─────────────────────┤
│ reports/q4.csv                   │ 1.2 MB   │ 2024-10-01 08:30   │
│ data/raw.json                    │ 42.0 KB  │ 2024-09-15 14:10   │
╰──────────────────────────────────┴──────────┴─────────────────────╯
2 objects found
```

**STDOUT** (truncated, 100 of 4532 objects):
```
<table with 100 rows>
100 objects found
Note: Showing 100 of 4532 objects. Set UE_MAX_OUTPUT_RECORDS environment variable to increase this limit.
```

**Extension Output result object (JSON)**:

Note: The Extension Output will also include `exit_code`, `status_description`, and `invocation` elements added automatically during implementation.

```json
{
  "result": {
    "bucket": "my-demo-bucket",
    "region": "us-east-1",
    "total_count": 42,
    "shown_count": 42,
    "objects": [
      {"key": "reports/q4.csv", "size_bytes": 1258291, "last_modified": "2024-10-01T08:30:00Z"},
      {"key": "data/raw.json", "size_bytes": 43008, "last_modified": "2024-09-15T14:10:00Z"}
    ]
  }
}
```

### Success Criteria

1. All required input fields are non-empty.
2. All S3 API pagination pages were retrieved without error.
3. `total_count` in Extension Output reflects the true total object count in the bucket.
4. `shown_count` equals `min(total_count, max_records)`.
5. `objects` array in Extension Output contains exactly `shown_count` entries, each with `key`, `size_bytes`, and `last_modified` (ISO 8601 UTC).
6. STDOUT table uses `tabulate` `rounded_outline` format with columns: Object Key, Size (human-readable), Last Modified.
7. Truncation notice is appended to STDOUT when `total_count > shown_count`.
8. `objects_found` output field equals the string representation of `total_count`.
9. `status` output field equals `"Success: Listed <total_count> objects"`.
10. Return code is `0`.

---

## Action 2: Upload File

**Description**: Validates that the specified local file exists on the agent host, connects to AWS S3 using the provided IAM credentials and region, uploads the file to the specified bucket and key (always overwriting if the key exists), and emits a confirmation message to STDOUT and a structured Extension Output JSON with upload metadata.

### Input Requirements

- **action** — must be "Upload File"
- **aws_credentials** — provides Access Key ID and Secret Access Key
- **aws_region** — identifies the S3 endpoint
- **bucket_name** — the target bucket for the upload
- **local_file** — absolute path to the local file to upload
- **s3_object_key** — target key in the S3 bucket

### Execution Flow

**Step 1 — Input Validation:**
- Verify `aws_credentials`, `aws_region`, `bucket_name`, `local_file`, and `s3_object_key` are all non-empty. If any are missing, set `status` output field to the error message and exit with return code 20.

**Step 2 — Local File Validation:**
- Check that the file at `local_file` path exists on the agent host file system.
- If the file does not exist or cannot be read (FileNotFoundError or PermissionError), set `status` to `"Error: Local file not found: <local_file>"`, write the error to STDERR, and exit with return code 1. No S3 API call is made.
- Retrieve the file size in bytes: `size_bytes = os.path.getsize(local_file)`.

**Step 3 — Build S3 Client:**
- Instantiate a boto3 S3 client using explicit credentials: `aws_access_key_id = input_data.aws_credentials.user`, `aws_secret_access_key = input_data.aws_credentials.password`, `region_name = input_data.aws_region`. No default credential chain or instance metadata fallback.

**Step 4 — Upload File:**
- Call `s3_client.upload_file(local_file, bucket_name, s3_object_key)`. This delegates to s3transfer for transparent multipart upload on large files.
- No pre-existence check is performed; S3 put-wins semantics always apply (existing objects at the key are silently overwritten).

**Step 5 — Construct S3 URI:**
- `s3_uri = f"s3://{bucket_name}/{s3_object_key}"`

**Step 6 — STDOUT Confirmation:**
- Compute `human_size` using SizeFormatter on `size_bytes`.
- Print to STDOUT: `"Uploaded <local_file> → <s3_uri> (<human_size>)"`

**Step 7 — Set Output Fields:**
- `output_data.uploaded_object = s3_uri`
- `output_data.status = f"Success: Uploaded {s3_uri}"`

**Step 8 — Return Extension Output:**
- Construct and return the result object (see Output Examples below).
- Exit with return code 0.

### Output Examples

**STDOUT**:
```
Uploaded /home/stonebranch/data/report.csv → s3://my-demo-bucket/reports/q4.csv (1.2 MB)
```

**Extension Output result object (JSON)**:

Note: The Extension Output will also include `exit_code`, `status_description`, and `invocation` elements added automatically during implementation.

```json
{
  "result": {
    "bucket": "my-demo-bucket",
    "key": "reports/q4.csv",
    "s3_uri": "s3://my-demo-bucket/reports/q4.csv",
    "size_bytes": 1258291,
    "region": "us-east-1"
  }
}
```

### Success Criteria

1. All required input fields are non-empty.
2. Local file exists and is readable at the specified path.
3. S3 upload API call completed without error.
4. `uploaded_object` output field contains the correct S3 URI in `s3://<bucket>/<key>` format.
5. `status` output field equals `"Success: Uploaded s3://<bucket>/<key>"`.
6. Extension Output JSON contains `bucket`, `key`, `s3_uri`, `size_bytes`, and `region`.
7. Return code is `0`.

---

# Progress Reporting

Progress Reporting (percentage of completion report) is not required. Standard UAC task logging applies.

---

# Dynamic Choice Field Population

No Dynamic choice fields should be implemented. This extension has no dynamic dropdowns.

---

# Cancellation Behavior

Default cancellation logic is used (TERM signal). No custom cancellation code is required. boto3 manages HTTP connection pooling internally and no temporary files are created, so no explicit cleanup is needed on cancellation.

---

# Re-Run Behavior

Re-runs are treated as initial executions. No special re-run logic is implemented. The extension has no output-only fields that encode state required for resumption (the `objects_found`, `uploaded_object`, and `status` fields from a previous run are informational and are not evaluated during re-run dispatch).

---

# Dynamic Commands

No Dynamic commands should be implemented. This extension has no dynamic commands.

---

# Utility Modules

## Required Utility Modules

### 1. S3ClientManager

**Purpose:** Creates and returns a fully configured boto3 S3 client using explicit IAM credentials and a specified AWS region. Ensures no fallback to the default boto3 credential discovery chain (environment variables, instance metadata, shared credentials file).

**Required Capabilities:**
- Accept `access_key_id` (str), `secret_access_key` (str), and `region` (str) as parameters
- Return a boto3 S3 client configured with explicit credentials only
- Propagate any boto3 configuration errors (e.g., invalid region format) to the caller

**Used By:** List Objects action, Upload File action

---

### 2. SizeFormatter

**Purpose:** Converts a raw integer byte count into a compact human-readable size string suitable for STDOUT display.

**Required Capabilities:**
- Convert integer byte count to abbreviated string using binary prefixes (1 KB = 1024 bytes):
  - `< 1024` bytes → `"X B"` (no decimal)
  - `1024 ≤ bytes < 1048576` → `"X.X KB"` (1 decimal place)
  - `1048576 ≤ bytes < 1073741824` → `"X.X MB"` (1 decimal place)
  - `≥ 1073741824` → `"X.X GB"` (1 decimal place)
- Handle edge case: `0` bytes → `"0 B"`

**Used By:** List Objects action (Size column in table), Upload File action (STDOUT confirmation line)

---

## Exception Mapping Strategy

**Authentication Errors (botocore ClientError):**
- ClientError code `InvalidClientTokenId` → `AuthenticationError` (exit code 1, non-transient — user config error)
- ClientError code `AuthFailure` → `AuthenticationError` (exit code 1, non-transient)
- ClientError code `SignatureDoesNotMatch` → `AuthenticationError` (exit code 1, non-transient)
- `botocore.exceptions.NoCredentialsError` → `AuthenticationError` (exit code 1, non-transient)

**Authorization Errors (botocore ClientError):**
- ClientError code `AccessDenied` → `AccessDeniedError` (exit code 1, non-transient — IAM policy error)

**Resource Errors (botocore ClientError):**
- ClientError code `NoSuchBucket` → `BucketNotFoundError` (exit code 1, non-transient — user config error)

**Network / Connection Errors:**
- `botocore.exceptions.EndpointConnectionError` → `ConnectionError` (exit code 1, transient — retry may help)
- `botocore.exceptions.ConnectTimeoutError` → `ConnectionError` (exit code 1, transient)

**Transfer Errors (botocore ClientError, all other codes):**
- Any other `ClientError` during upload or list → `S3OperationError` (exit code 1, may be transient)

**Local File Errors:**
- `FileNotFoundError` → `LocalFileNotFoundError` (exit code 1, non-transient)
- `PermissionError` → `LocalFileNotFoundError` (exit code 1, non-transient — file inaccessible)

**Validation Errors:**
- Missing required input field → `ValidationError` (exit code 20, non-transient — user config error)

**Error Output Strategy (all exceptions):**
- Write the human-readable error message to STDERR
- Set `output_data.status` to the error message
- Serialize an error block to Extension Output JSON: `{"error": {"type": "<ExceptionClassName>", "message": "<descriptive message>"}}`
- Exit with the corresponding exit code

**Exit Code Guide:**
- Exit code 0: Successful execution
- Exit code 1: Operational error (auth, access, network, resource, file, transfer)
- Exit code 20: Input validation error (missing required field)

---

# Dependencies

## 1. External API Dependencies

**1. Amazon S3 (Amazon Simple Storage Service)**
- **Endpoint**: `https://s3.<region>.amazonaws.com` (resolved automatically by boto3 based on the `aws_region` input)
- **Purpose**: Core external service — provides object listing and upload operations
- **Protocol**: HTTPS
- **Method**: GET (list), PUT (upload) — all abstracted by boto3
- **Authentication**: AWS Signature Version 4, using Access Key ID and Secret Access Key
- **Response Format**: XML (parsed internally by boto3; extension receives Python objects)
- **Data Retrieved/Sent**:
  - List Objects: object key, size in bytes, last-modified datetime, ETag (key/size/last_modified used)
  - Upload File: raw file bytes streamed from agent host to S3

**General API Requirements:**
- IAM User must have `s3:ListObjectsV2` permission on the target bucket for List Objects action
- IAM User must have `s3:PutObject` permission on the target bucket for Upload File action
- No special AWS account setup beyond the above IAM permissions

---

## 2. Python version dependency

Python `>= 3.11` is required, as configured in the extension workspace.

---

## 3. Target Platform

**Linux (x86_64).** The build system uses `--platform=manylinux_2_17_x86_64` when installing dependencies. All selected Python packages are pure-Python (no C extensions), so they produce platform-agnostic wheels compatible with any Python 3.11+ Linux or Windows agent. No binary wheel constraints apply in practice.

---

## 4. Python Library Dependencies

**1. boto3**
- **Purpose**: Official AWS SDK for Python — provides high-level S3 client, paginator, and upload_file API
- **Version**: `1.43.110`
- **Installation**: `pip install boto3==1.43.110`
- **Usage**: List Objects action (paginator, list_objects_v2), Upload File action (upload_file)
- **Features Used**: `boto3.client('s3', ...)`, paginator for `list_objects_v2`, `s3_client.upload_file()`

**2. botocore**
- **Purpose**: Low-level AWS service interface; handles request signing, retry logic, and error parsing for boto3
- **Version**: `1.43.110`
- **Installation**: `pip install botocore==1.43.110`
- **Usage**: Installed as boto3 dependency; exception classes (`botocore.exceptions.ClientError`, `EndpointConnectionError`, etc.) used directly in error handling
- **Features Used**: `botocore.exceptions.ClientError`, `botocore.exceptions.EndpointConnectionError`, `botocore.exceptions.ConnectTimeoutError`, `botocore.exceptions.NoCredentialsError`

**3. s3transfer**
- **Purpose**: S3 transfer manager used internally by boto3's `upload_file()` to handle multipart uploads transparently for large files
- **Version**: `0.19.2`
- **Installation**: `pip install s3transfer==0.19.2`
- **Usage**: Installed as boto3 dependency; used implicitly by `s3_client.upload_file()`
- **Features Used**: Transparent multipart upload management

**4. jmespath**
- **Purpose**: JSON query language used internally by boto3 for response parsing
- **Version**: `1.1.0`
- **Installation**: `pip install jmespath==1.1.0`
- **Usage**: Installed as boto3 dependency; no direct usage in extension code
- **Features Used**: Internal boto3 response query

**5. python-dateutil**
- **Purpose**: Extended date/time parsing for AWS timestamp formats returned by S3 API
- **Version**: `2.9.0`
- **Installation**: `pip install python-dateutil==2.9.0`
- **Usage**: Installed as botocore dependency; AWS timestamps are returned as timezone-aware datetime objects; used implicitly
- **Features Used**: Timezone-aware datetime parsing

**6. urllib3**
- **Purpose**: HTTP client library used by botocore for all AWS API HTTP calls
- **Version**: `2.8.0`
- **Installation**: `pip install urllib3==2.8.0`
- **Usage**: Installed as botocore dependency; no direct usage in extension code
- **Features Used**: HTTP connection pooling for S3 API calls

**7. tabulate**
- **Purpose**: ASCII table formatting library for rendering S3 object listings on STDOUT
- **Version**: `0.10.0`
- **Installation**: `pip install tabulate==0.10.0`
- **Usage**: List Objects action — renders the objects table with `tablefmt="rounded_outline"`
- **Features Used**: `tabulate(rows, headers=[...], tablefmt="rounded_outline")`

---

## 5. Python Standard Library Dependencies

**1. os**
- **Purpose**: File system operations on the agent host
- **Version**: Built-in (Python 3.11+)
- **Installation**: No installation required
- **Usage**: Upload File action — `os.path.exists()` for local file existence check, `os.path.getsize()` for file size retrieval
- **Features Used**: `os.path.exists`, `os.path.getsize`

**2. sys**
- **Purpose**: Writing error messages to STDERR
- **Version**: Built-in (Python 3.11+)
- **Installation**: No installation required
- **Usage**: All error handling paths — `sys.stderr.write()`
- **Features Used**: `sys.stderr`

---

## 6. CLI Tool Dependencies

No Dependencies. This extension uses only bundled Python libraries and makes no calls to external CLI tools on the agent host.

---

## 7. Environment Variables

**UE_MAX_OUTPUT_RECORDS** (integer, optional):
- **Purpose**: Controls the maximum number of S3 objects included in the STDOUT table and the `objects` array of the Extension Output JSON for the List Objects action. When the total object count exceeds this value, output is truncated and a note is printed to STDOUT. The `objects_found` output field always reflects the true total count regardless of this setting.
- **Default**: `100`
- **Usage**: Read at the start of List Objects execution; parsed as integer; non-integer values fall back to default
- **Examples**: `UE_MAX_OUTPUT_RECORDS=500`, `UE_MAX_OUTPUT_RECORDS=50`
