# Universal Extension Requirements (Refined)

**Extension Name:** AWS Object Storage Showcase 2
**Original Generated:** Not specified
**Refined:** 2026-10-09
**Agent_id:** Not specified
**Requirements Completeness:** High Detail
**Target Platform:** Linux

---

# Table of Contents

1. [Overview](#overview)
2. [Actions](#actions)
   - 2.1 [Action 1 — List Objects](#action-1--list-objects)
   - 2.2 [Action 2 — Upload File](#action-2--upload-file)
3. [Input Requirements](#input-requirements)
   - 3.1 [Action Selection](#action-selection)
   - 3.2 [Connection Parameters](#connection-parameters)
   - 3.3 [Storage Target](#storage-target)
   - 3.4 [Upload File Parameters](#upload-file-parameters)
4. [Output Requirements](#output-requirements)
   - 4.1 [On Success — List Objects](#on-success--list-objects)
   - 4.2 [On Success — Upload File](#on-success--upload-file)
   - 4.3 [On Error — Both Actions](#on-error--both-actions)
5. [Authentication Requirements](#authentication-requirements)
6. [Environment Variables](#environment-variables)
7. [Operational Behavior](#operational-behavior)
8. [Implementation Notes](#implementation-notes)
   - 8.1 [Python Compatibility](#python-compatibility)
   - 8.2 [Target Platform](#target-platform)
   - 8.3 [Third-Party Services and Tools](#third-party-services-and-tools)
   - 8.4 [Error Handling](#error-handling)
   - 8.5 [Resource Cleanup](#resource-cleanup)
9. [Requirements Summary](#requirements-summary)
10. [Document Change History](#document-change-history)
11. [References](#references)

---

# Overview

This document defines the complete requirements for the **AWS Object Storage Showcase 2** Universal Extension for Stonebranch Universal Automation Center (UAC).

**Integration Purpose:** The extension provides a simple, self-contained AWS S3 integration that demonstrates two fundamental S3 operations — listing objects in a bucket and uploading a local file to a bucket — from a UAC agent host. It is an MVP/demo integration intended to showcase that AWS S3 automation can be implemented with Stonebranch. All required Python dependencies must be bundled with the extension; no installation on the Universal Agent host is required.

---

# Actions

## Action 1 — List Objects

**Functional Requirements:**

1. The extension must connect to AWS S3 using the provided credentials and region.
2. The extension must list all objects contained in the specified S3 bucket.
3. The extension must handle S3 API pagination to retrieve all objects when the bucket contains more than 1,000 objects.
4. The extension must display each object as a row in an ASCII table on STDOUT, with the following columns: Object Key, human-readable Size, and Last Modified date.
5. The STDOUT table must use the `tabulate` library with the `rounded_outline` table format.
6. The number of objects written to STDOUT and included in the Extension Output JSON must be capped at the value of the `UE_MAX_OUTPUT_RECORDS` environment variable (default: 100).
7. When the total object count exceeds the display cap, the STDOUT output must include a truncation notice in the form: `Note: Showing <shown> of <total> objects. Set UE_MAX_OUTPUT_RECORDS environment variable to increase this limit.`
8. The `Objects Found` output-only field must always reflect the true total object count in the bucket, regardless of the display cap.
9. The `Status` output-only field must be set to: `Success: Listed <total> objects`.
10. The Extension Output JSON must contain the bucket name, region, true total count, shown count, and an array of object records (up to the display cap) each with key, size in bytes, and last-modified timestamp.

---

## Action 2 — Upload File

**Functional Requirements:**

1. The extension must connect to AWS S3 using the provided credentials and region.
2. The extension must upload the specified local file from the UAC agent host to the specified S3 bucket and object key.
3. If the target S3 object key already exists in the bucket, the extension must overwrite it without performing any pre-existence check (standard S3 put-wins semantics).
4. The `Uploaded Object` output-only field must be set to the S3 URI of the uploaded object, in the format: `s3://<bucket>/<key>`.
5. The `Status` output-only field must be set to: `Success: Uploaded s3://<bucket>/<key>`.
6. The Extension Output JSON must contain the bucket name, S3 key, full S3 URI, file size in bytes, and the AWS region.

---

# Input Requirements

## Action Selection

- **Action** (Choice Field, required, all actions): Selects which S3 operation to perform.
  - Options:
    - `List Objects` — lists all objects in the specified bucket.
    - `Upload File` — uploads a local file to the specified bucket and key.
  - Default presented option: `List Objects`
  - Applicability: Determines which action-specific input fields are shown. `Local File` and `S3 Object Key` fields are shown only when `Upload File` is selected.

---

## Connection Parameters

- **AWS Credentials** (Credential Field, required, all actions): A UAC Credential entity whose attributes map to AWS IAM User authentication values.
  - `user` attribute: AWS Access Key ID (e.g., `AKIAIOSFODNN7EXAMPLE`)
  - `password` attribute: AWS Secret Access Key (e.g., `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`)
  - Applicability: Both actions

- **AWS Region** (Text Field, required, all actions): The AWS region name identifying the endpoint for S3 API calls.
  - Example: `us-east-1`, `eu-west-1`, `ap-southeast-2`
  - Default Value: None
  - Applicability: Both actions

---

## Storage Target

- **Bucket Name** (Text Field, required, all actions): The name of the target AWS S3 bucket.
  - Example: `my-demo-bucket`
  - Default Value: None
  - Applicability: Both actions

---

## Upload File Parameters

These fields are visible and required only when **Action** is set to `Upload File`.

- **Local File** (Text Field, required for Upload File): The full absolute path to the local file on the UAC agent host that must be uploaded.
  - Example: `/home/stonebranch/data/report.csv`
  - Default Value: None
  - Applicability: Upload File action only

- **S3 Object Key** (Text Field, required for Upload File): The target S3 object key (path and filename) under which the file will be stored in the bucket.
  - Example: `reports/2024/q4-report.csv`
  - Default Value: None
  - Applicability: Upload File action only

---

# Output Requirements

## On Success — List Objects

- **Return code:** `0`
- **Status description:** `Success: Listed <total_count> objects`
- **Output-only fields:**
  - `Status` (Text, Output Only): Set to `Success: Listed <total_count> objects`
  - `Objects Found` (Text, Output Only, visible when action = List Objects): Set to the true total object count as a string (e.g., `42`)
- **STDOUT output:** An ASCII table using `tabulate` with `rounded_outline` format. Columns: Object Key, Size (human-readable, e.g., `1.2 MB`, `42 KB`), Last Modified (date and time). One row per object, up to the display cap. If truncated, a note line is appended after the table.
  - Example (untruncated):
    ```
    ╭──────────────────────────────────┬──────────┬─────────────────────╮
    │ Object Key                       │ Size     │ Last Modified       │
    ├──────────────────────────────────┼──────────┼─────────────────────┤
    │ reports/q4.csv                   │ 1.2 MB   │ 2024-10-01 08:30   │
    │ data/raw.json                    │ 42 KB    │ 2024-09-15 14:10   │
    ╰──────────────────────────────────┴──────────┴─────────────────────╯
    2 objects found
    ```
  - Example (truncated at 100 of 4,532 objects):
    ```
    <table with 100 rows>
    Note: Showing 100 of 4,532 objects. Set UE_MAX_OUTPUT_RECORDS environment variable to increase this limit.
    ```
- **Extension Output JSON:**
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
  - `total_count` always reflects the true total in the bucket.
  - `shown_count` reflects the number of objects actually included in the `objects` array (up to the display cap).
  - `objects` contains one entry per shown object with: `key` (string), `size_bytes` (integer), `last_modified` (ISO 8601 UTC string).
- **Success Criteria:**
  1. AWS S3 API call completed without error.
  2. All S3 API pages were retrieved via pagination.
  3. STDOUT table rendered with correct columns and format.
  4. `Objects Found` output-only field contains the true total count.
  5. `Status` output-only field matches the success pattern.
  6. Extension Output JSON is valid and contains all required keys.
  7. Return code is `0`.

---

## On Success — Upload File

- **Return code:** `0`
- **Status description:** `Success: Uploaded s3://<bucket>/<key>`
- **Output-only fields:**
  - `Status` (Text, Output Only): Set to `Success: Uploaded s3://<bucket>/<key>`
  - `Uploaded Object` (Text, Output Only, visible when action = Upload File): Set to the full S3 URI (e.g., `s3://my-demo-bucket/reports/q4.csv`)
- **STDOUT output:** A confirmation message, e.g.:
  ```
  Uploaded /home/stonebranch/data/report.csv → s3://my-demo-bucket/reports/q4.csv (1.2 MB)
  ```
- **Extension Output JSON:**
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
  - `size_bytes`: size of the local file that was uploaded.
- **Success Criteria:**
  1. Local file was successfully read from the agent host.
  2. AWS S3 upload API call completed without error.
  3. `Uploaded Object` output-only field contains the correct S3 URI.
  4. `Status` output-only field matches the success pattern.
  5. Extension Output JSON is valid and contains all required keys.
  6. Return code is `0`.

---

## On Error — Both Actions

- **Return code:** `1`
- **Status description:** A human-readable error message describing the failure (e.g., `Error: Invalid credentials`, `Error: Bucket 'my-bucket' not found`, `Error: Local file not found: /path/to/file`)
- **Output-only fields:**
  - `Status` (Text, Output Only): Set to the error message.
  - Action-specific output fields (`Objects Found`, `Uploaded Object`) remain empty on error.
- **Extension Output JSON:**
  ```json
  {
    "error": {
      "type": "<ErrorCategory>",
      "message": "<descriptive error message>"
    }
  }
  ```
- **Failure Scenarios:**

  | Scenario | Description | Root Causes | Return Code | Status Description Pattern |
  |---|---|---|---|---|
  | Authentication Error | AWS rejected the provided credentials | Invalid Access Key ID or Secret Access Key | `1` | `Error: Authentication failed — <AWS error message>` |
  | Bucket Not Found | The specified bucket does not exist or is not accessible | Bucket name is incorrect; bucket was deleted | `1` | `Error: Bucket '<name>' not found or not accessible` |
  | Access Denied | The IAM user lacks permission for the operation | Missing S3 IAM policy (`s3:ListObjectsV2`, `s3:PutObject`) | `1` | `Error: Access denied — <AWS error message>` |
  | Connection Error | Network failure reaching the S3 endpoint | Network outage, invalid region, firewall | `1` | `Error: Connection failed — <reason>` |
  | Local File Not Found | The specified local file does not exist on the agent host | Wrong path, file deleted, permission issue | `1` | `Error: Local file not found: <path>` |
  | Upload Failure | The S3 upload call failed after initiating transfer | Network interruption during upload, quota exceeded | `1` | `Error: Upload failed — <AWS error message>` |

- **STDERR:** Error messages must be written to STDERR in addition to being captured in the Extension Output JSON and `Status` field.
- **Input Validation:** Required fields that are empty at launch must cause the task to fail immediately with return code `1` and a clear `Status` describing which field is missing. No S3 API calls shall be made before input validation passes.

---

# Authentication Requirements

The extension must authenticate to AWS S3 using Standard IAM User credentials (Access Key ID + Secret Access Key). The credentials are sourced exclusively from a UAC Credential Field configured on the task. The Access Key ID is read from the credential's `user` attribute, and the Secret Access Key is read from the credential's `password` attribute. No session token, instance role, or default credential chain discovery is supported.

---

# Environment Variables

- **`UE_MAX_OUTPUT_RECORDS`** (integer, optional): Controls the maximum number of S3 objects included in the STDOUT table and the `objects` array of the Extension Output JSON for the List Objects action. When the total object count exceeds this value, output is truncated and a note is printed. The `Objects Found` output-only field always shows the true total count regardless of this setting.
  - Default: `100`
  - Applicable to: List Objects action only

---

# Operational Behavior

**Dynamic Choice Fields:**
Not applicable. This extension has no dynamic dropdown fields.

**Cancel Action:**
Not specified. Standard UAC task cancellation behavior applies.

**Re-run Capability:**
Not specified. Standard UAC re-run behavior applies (re-run from the beginning of the action).

**Progress Reporting:**
Not specified. Standard UAC task logging applies.

**Dynamic Commands:**
Not applicable. This extension has no dynamic commands.

---

# Implementation Notes

## Python Compatibility

Python `>= 3.11` (as configured in the extension workspace).

## Target Platform

Linux (x86_64). The build environment is Linux x86_64 with `manylinux_2_17_x86_64` compatibility rules applying. All selected modules are pure Python, so there are no binary wheel constraints in practice.

## Third-Party Services and Tools

**AWS S3 (Amazon Simple Storage Service)**
- The only external service used by this extension.
- Access is via the public AWS S3 API endpoints, authenticated using IAM User credentials.
- No version constraint on the S3 API itself; the boto3 SDK handles versioning internally.
- No specific AWS account setup or bucket configuration is required by the extension beyond the IAM user having appropriate `s3:ListObjectsV2` (for List Objects) and `s3:PutObject` (for Upload File) permissions on the target bucket.

**Python Dependencies (all pure Python):**

| Module | Purpose | Version |
|---|---|---|
| boto3 | Official AWS SDK — provides S3 list and upload operations | 1.43.110 |
| botocore | Low-level AWS service interface; handles request signing and retries | 1.43.110 |
| s3transfer | S3 transfer manager; handles multipart uploads transparently | 0.19.2 |
| jmespath | JSON query language used internally by boto3 | 1.1.0 |
| python-dateutil | Extended date/time parsing for AWS timestamp formats | 2.9.0 |
| urllib3 | HTTP client library used by botocore for AWS API calls | 2.8.0 |
| tabulate | ASCII table formatting for STDOUT object listings | 0.10.0 |

All modules must be bundled with the extension ZIP so that no installation is required on the UAC agent host.

## Error Handling

**Error Categories:**
1. **Authentication errors** — invalid or missing IAM credentials
2. **Authorization errors** — valid credentials but insufficient IAM permissions
3. **Network/connection errors** — unreachable S3 endpoint, invalid region, DNS failure
4. **Resource errors** — bucket not found, object not found (if applicable)
5. **Local file errors** — file not found, permission denied on agent host
6. **Transfer errors** — upload interrupted or failed mid-transfer

**Error Handling Strategy:** All exceptions must be caught, translated into a human-readable message, written to STDERR, set in the `Status` output-only field, serialized into the Extension Output JSON error block, and cause the task to exit with return code `1`.

**Recovery Mechanisms:** None. The extension performs no automatic retry or fallback. UAC's built-in task retry mechanism can be configured at the task level if retries are needed.

## Resource Cleanup

No temporary files or external connections are created by the extension during execution. boto3 manages HTTP connection pooling internally. No explicit cleanup is required.

---

# Requirements Summary

The AWS Object Storage Showcase 2 extension must implement two S3 actions within a single self-contained UAC Universal Extension:

1. **List Objects** — paginates through all objects in a specified S3 bucket, renders an ASCII table (Key, human-readable Size, Last Modified) on STDOUT using `tabulate`, caps display at `UE_MAX_OUTPUT_RECORDS` (default 100) with a truncation notice, always reports the true total in the `Objects Found` output field, and emits a rich Extension Output JSON with the full object list up to the cap.

2. **Upload File** — uploads a specified local file from the agent host to a specified S3 bucket and key, always overwrites if the key exists, reports the S3 URI in the `Uploaded Object` output field, and emits a rich Extension Output JSON with upload details.

Both actions share: IAM User credential input (Access Key ID + Secret Access Key via UAC Credential Field), AWS Region and Bucket Name inputs, and a shared `Status` output-only field. All Python dependencies (boto3 1.43.110 and full dependency chain, plus tabulate 0.10.0) must be bundled. The extension targets Linux x86_64, Python >= 3.11, and is explicitly scoped as an MVP/demo integration.

---

# Document Change History

- **2026-10-09**: Initial requirements captured — Moderate Detail (original `requirements.md`)
- **2026-10-09**: Comprehensive refinement based on 6 clarification questions and user feedback covering: STDOUT formatting (tabulate, rounded_outline), credential mapping (IAM User Access Key ID + Secret Access Key), output-only field design (Status, Objects Found, Uploaded Object), overwrite behavior (always overwrite), large-output safety cap (UE_MAX_OUTPUT_RECORDS, default 100), and Extension Output JSON structure (full object list for List Objects; full upload details for Upload File).

---

# References

- Original Requirements Document: `memory/requirements.md`
- Original Requirements Q&A Document: `memory/agents-memory/requirements-QnA.md`
