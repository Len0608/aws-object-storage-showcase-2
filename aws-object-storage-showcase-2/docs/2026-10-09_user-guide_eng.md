> **Version:** 1.0.0 | **Date:** 2026-10-09

# AWS Object Storage Showcase 2 — User Guide

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Task Actions](#task-actions)
   - [List Objects](#list-objects)
   - [Upload File](#upload-file)
4. [Task Configuration](#task-configuration)
   - [Authentication](#authentication)
   - [General](#general)
   - [Upload File Fields](#upload-file-fields)
   - [Output Fields](#output-fields)
5. [Example Walkthrough](#example-walkthrough)
   - [Scenario 1: Auditing S3 Bucket Contents](#scenario-1-auditing-s3-bucket-contents)
   - [Scenario 2: Archiving a Report File to S3](#scenario-2-archiving-a-report-file-to-s3)
6. [Troubleshooting](#troubleshooting)
7. [Field Reference](#field-reference)

---

## Overview

**Aws Object Storage Showcase 2** is a UAC Universal Extension that integrates with Amazon S3. It allows UAC tasks to:

- **List all objects** in an S3 bucket and display them in a formatted table.
- **Upload a local file** from the agent host directly to an S3 bucket.

Authentication is handled through a UAC Credential that stores your AWS IAM User Access Key ID and Secret Access Key.

---

## Prerequisites

- **UAC agent** running on a Linux/Unix host with network access to the AWS S3 endpoint for the target region.
- **AWS IAM User** with sufficient S3 permissions:
  - `s3:ListBucket` — required for the **List Objects** action.
  - `s3:PutObject` — required for the **Upload File** action.
- **UAC Credential** configured with:
  - **Username** field = AWS Access Key ID
  - **Password** field = AWS Secret Access Key
- The **target S3 bucket** must already exist. This extension does not create buckets.
- For uploads, the **local file** must already exist and be readable on the agent host at the time of task execution.

---

## Task Actions

### List Objects

Lists all objects currently stored in the specified S3 bucket.

**When to use:** Use this action to audit bucket contents, verify that expected files are present, or count the total number of objects as part of a workflow.

**Execution flow:**

1. UAC authenticates to AWS S3 using the provided credential.
2. The extension calls the S3 `ListObjectsV2` API, paginating through all pages until every object is retrieved.
3. A formatted ASCII table is printed to the task output (limited to 100 rows by default via `UE_MAX_OUTPUT_RECORDS`).
4. The task completes with exit code `0` on success.
5. The **Objects Found** output field is populated with the total object count.
6. The **Status** field is updated with a short outcome description.

**Status and completion:**

- Exit code `0`: operation succeeded; the **Status** and **Objects Found** fields are populated.
- Exit code `1` or `20`: operation failed; the **Status** field contains the error description.

---

### Upload File

Uploads a file from the agent host's local filesystem to an S3 bucket at a specified object key.

**When to use:** Use this action to archive reports, push generated artifacts, or transfer data files as part of an automated workflow.

**Execution flow:**

1. The extension validates that the local file exists and that all required fields are set.
2. UAC authenticates to AWS S3 using the provided credential.
3. The file is uploaded via the boto3 `upload_file` method, which handles multipart transfer transparently for large files.
4. If an object already exists at the target key, it is silently overwritten without a pre-existence check.
5. The task completes with exit code `0` on success.
6. The **Uploaded Object** output field is populated with the full `s3://` URI of the uploaded object.
7. The **Status** field is updated with a short outcome description.

**Status and completion:**

- Exit code `0`: file uploaded successfully; the **Status** and **Uploaded Object** fields are populated.
- Exit code `1` or `20`: operation failed; the **Status** field contains the error description.

---

## Task Configuration

### Authentication

| Field | Description | Required | Example |
|-------|-------------|----------|---------|
| **AWS Credentials** | UAC Credential containing the AWS IAM Access Key ID (username) and Secret Access Key (password). | Yes | `my-aws-s3-cred` |

### General

| Field | Description | Required | Example |
|-------|-------------|----------|---------|
| **Action** | Selects the S3 operation to perform. Choose **List Objects** to enumerate bucket contents, or **Upload File** to push a local file to S3. Defaults to **List Objects**. | No | `List Objects` |
| **AWS Region** | The AWS region where the target bucket resides. Must be a valid AWS region identifier. | Yes | `us-east-1` |
| **Bucket Name** | The name of the target S3 bucket. The bucket must already exist in the specified region. | Yes | `my-data-bucket` |

### Upload File Fields

These fields appear only when **Action** is set to **Upload File**.

| Field | Description | Required | Example |
|-------|-------------|----------|---------|
| **Local File Path** | Absolute path to the file on the agent host to upload. The file must exist and be readable by the agent process at task launch time. | Yes (Upload File only) | `/home/stonebranch/exports/report.csv` |
| **S3 Object Key** | The key (path and filename) under which the file will be stored in S3. If an object with the same key already exists, it will be overwritten. | Yes (Upload File only) | `reports/2024/q4-report.csv` |

### Output Fields

These fields are read-only and populated by the extension at runtime.

| Field | Description | Populated By |
|-------|-------------|--------------|
| **Status** | Short description of the execution outcome. Visible in the UAC task list view. Preserved on rerun. | Both actions |
| **Objects Found** | Total number of objects found in the bucket. Visible only when **Action** is **List Objects**. Preserved on rerun. | List Objects only |
| **Uploaded Object** | Full `s3://` URI of the uploaded object. Visible only when **Action** is **Upload File**. Preserved on rerun. | Upload File only |

---

## Example Walkthrough

### Scenario 1: Auditing S3 Bucket Contents

**Goal:** List all objects in a production S3 bucket to verify expected data files are present.

**Prerequisites:**
- A UAC Credential named `aws-prod-cred` exists with the IAM user's Access Key ID and Secret Access Key.
- The IAM user has `s3:ListBucket` permission on the target bucket.
- The S3 bucket `prod-data-archive` exists in region `eu-west-1`.

**Configuration:**

| Field | Value | Notes |
|-------|-------|-------|
| Action | `List Objects` | Default; no change needed |
| AWS Credentials | `aws-prod-cred` | |
| AWS Region | `eu-west-1` | Must match the bucket's region |
| Bucket Name | `prod-data-archive` | |

**What happens:**

- The extension connects to S3 in `eu-west-1` and paginates through all objects in `prod-data-archive`.
- An ASCII table of up to 100 objects is printed to the task output log.
- The **Objects Found** output field is set to the total object count (e.g., `42`).
- The **Status** field is set to a success message.
- The task exits with code `0`.

---

### Scenario 2: Archiving a Report File to S3

**Goal:** Upload a nightly report generated on the agent host to an S3 bucket for long-term storage.

**Prerequisites:**
- A UAC Credential named `aws-etl-cred` exists with the IAM user's Access Key ID and Secret Access Key.
- The IAM user has `s3:PutObject` permission on the target bucket and prefix.
- The S3 bucket `company-reports` exists in region `us-east-1`.
- The agent host generates the report at `/var/reports/nightly/sales-2026-10-09.csv` before this task runs.

**Configuration:**

| Field | Value | Notes |
|-------|-------|-------|
| Action | `Upload File` | |
| AWS Credentials | `aws-etl-cred` | |
| AWS Region | `us-east-1` | |
| Bucket Name | `company-reports` | |
| Local File Path | `/var/reports/nightly/sales-2026-10-09.csv` | Must exist on the agent host at launch time |
| S3 Object Key | `sales/2026/10/sales-2026-10-09.csv` | If this key already exists, it will be overwritten |

**What happens:**

- The extension verifies the local file exists at the given path.
- It connects to S3 in `us-east-1` and uploads the file using multipart transfer automatically for large files.
- The **Uploaded Object** output field is set to `s3://company-reports/sales/2026/10/sales-2026-10-09.csv`.
- The **Status** field is set to a success message.
- The task exits with code `0`.

---

## Troubleshooting

### Authentication Failures

| Symptom | Possible Cause | Resolution |
|---------|---------------|------------|
| Status contains `Authentication failed` | Invalid AWS Access Key ID or Secret Access Key in the UAC Credential. | Verify the UAC Credential's username (Access Key ID) and password (Secret Access Key) match the IAM user's current active keys. Rotate keys if necessary. |
| Status contains `SignatureDoesNotMatch` | Clock skew between the agent host and AWS. | Ensure the agent host's system time is synchronized (e.g., via NTP). |
| Status contains `InvalidClientTokenId` | The Access Key ID does not exist or has been deleted. | Check the IAM console and confirm the key is active. Update the UAC Credential. |

---

### Permission Errors

| Symptom | Possible Cause | Resolution |
|---------|---------------|------------|
| Status contains `Access denied` | The IAM user lacks the required S3 permission. | For **List Objects**: add `s3:ListBucket` on the bucket ARN. For **Upload File**: add `s3:PutObject` on the bucket/prefix ARN. |

---

### Resource Creation / Existence Failures

| Symptom | Possible Cause | Resolution |
|---------|---------------|------------|
| Status contains `Bucket not found` | The S3 bucket does not exist, or the bucket name is misspelled. | Confirm the bucket name and region in the AWS S3 console. Ensure the bucket exists before running the task. |
| Status contains `Local file not found` (Upload File only) | The file path specified in **Local File Path** does not exist on the agent host, or the agent process lacks read permission. | Verify the file path is correct and absolute. Confirm the file is created before this task runs (check predecessor task dependencies). |

---

### Connection and Timeout Issues

| Symptom | Possible Cause | Resolution |
|---------|---------------|------------|
| Status contains `Connection error` or `Endpoint connection error` | The agent host cannot reach the S3 endpoint for the specified region. | Check network connectivity and firewall rules. Confirm the agent can reach `s3.<region>.amazonaws.com` on port 443. |
| Status contains `Connect timeout` | Network latency or S3 endpoint unreachable. | Check the agent host's network route to AWS. If using a VPC endpoint, verify its configuration. |

---

### Configuration Mismatches

| Symptom | Possible Cause | Resolution |
|---------|---------------|------------|
| Task fails with exit code `20` at startup | A required field is empty or has an invalid value. | Review the **Status** field for the specific validation message. Check that **AWS Region** and **Bucket Name** are non-empty. When **Action** is **Upload File**, ensure both **Local File Path** and **S3 Object Key** are populated. |
| Upload action fields not visible in the task form | **Action** is set to **List Objects**. The **Local File Path** and **S3 Object Key** fields are hidden unless **Action = Upload File**. | Change the **Action** dropdown to **Upload File**; the fields will appear automatically. |

---

## Field Reference

| Name | Label | Type | Required | Default | Description | Allowed Values |
|------|-------|------|----------|---------|-------------|----------------|
| `action` | Action | Choice | No | `List Objects` | Selects the S3 operation to perform. Determines which fields are shown and which output fields are populated. | `List Objects`, `Upload File` |
| `aws_credentials` | AWS Credentials | Credential | Yes | — | UAC Credential with AWS Access Key ID as username and AWS Secret Access Key as password. | Any valid UAC Credential |
| `aws_region` | AWS Region | Text | Yes | — | AWS region identifier for the target bucket. Must be non-empty. | e.g., `us-east-1`, `eu-west-1`, `ap-southeast-2` |
| `bucket_name` | Bucket Name | Text | Yes | — | Name of the target S3 bucket. The bucket must already exist. Must be non-empty. | Any valid S3 bucket name |
| `local_file` | Local File Path | Text | Yes (Upload File only) | — | Absolute path to the file on the agent host to upload. Visible only when Action = Upload File. | e.g., `/home/stonebranch/data/report.csv` |
| `s3_object_key` | S3 Object Key | Text | Yes (Upload File only) | — | Target object key (path/filename) in S3. Overwrites existing object at this key without warning. Visible only when Action = Upload File. | e.g., `reports/2024/q4-report.csv` |
| `status` | Status | Text (Output Only) | — | — | Short description of the execution outcome. Visible in list view. Preserved on rerun. | Set by the extension at runtime |
| `objects_found` | Objects Found | Text (Output Only) | — | — | Total number of objects in the bucket. Populated only by List Objects. Visible only when Action = List Objects. Preserved on rerun. | Set by the extension at runtime |
| `uploaded_object` | Uploaded Object | Text (Output Only) | — | — | Full `s3://` URI of the uploaded object. Populated only by Upload File. Visible only when Action = Upload File. Preserved on rerun. | Set by the extension at runtime |
