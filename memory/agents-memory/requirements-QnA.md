# Requirements Completeness Assessment

**Classification: Moderate Detail**

The requirements establish a clear, well-focused core: a UAC Universal Extension for AWS S3 with exactly two actions (List Objects and Upload File), using the boto3 Python SDK, deployed as a self-contained bundle. The primary input fields are named, the MVP scope is explicitly stated, and the decision to omit a prefix filter is deliberate.

What's already well-understood and does not need discussion:
- The two actions and their names (List Objects, Upload File)
- The Python SDK choice (boto3)
- The bundling requirement (no agent-side installation)
- The input fields (AWS Credentials, AWS Region, Bucket Name, Local File, S3 Object Key)
- That no prefix filtering field is needed
- The simplicity target (MVP/demo)

To build the best solution together, we'll shape a few key decisions around: how AWS credentials are mapped to UAC's credential model, what information the extension displays to users at runtime, and how edge cases like large object listings and existing-object overwrites should behave.

---

# Platform Compatibility

**Platform Compatibility from Requirements**: Linux (Build Platform OS: Linux, Architecture: x86_64)
**Platform Compatibility Agreement**: Linux-only — `manylinux_2_17_x86_64` compatibility rules apply. All selected modules are pure Python, so there are no binary wheel constraints in practice.

---

# Python Modules and Versions

## Researched Modules

**boto3** *(user-specified)*
- **Module Purpose**: Official AWS SDK for Python — provides high-level S3 operations: list objects, upload files, download files, manage buckets
- **Version**: 1.43.110
- **Type**: Pure Python

**botocore** *(auto-dependency of boto3)*
- **Module Purpose**: Low-level AWS service interface that boto3 builds upon; handles request signing, retries, and endpoint routing
- **Version**: 1.43.110
- **Type**: Pure Python

**s3transfer** *(auto-dependency of boto3)*
- **Module Purpose**: S3 transfer manager — handles multipart uploads and downloads transparently; bundled automatically with boto3
- **Version**: 0.19.2
- **Type**: Pure Python

**jmespath** *(auto-dependency of boto3/botocore)*
- **Module Purpose**: JSON query language used internally by boto3 for response filtering
- **Version**: 1.1.0
- **Type**: Pure Python

**python-dateutil** *(auto-dependency of botocore)*
- **Module Purpose**: Extended date/time parsing used by botocore to handle AWS timestamp formats
- **Version**: 2.9.0
- **Type**: Pure Python

**urllib3** *(auto-dependency of botocore)*
- **Module Purpose**: HTTP client library used by botocore for all AWS API communication
- **Version**: 2.8.0
- **Type**: Pure Python

**tabulate** *(LLM-hypothesized — for STDOUT table formatting)*
- **Module Purpose**: Lightweight library for formatting Python data as ASCII tables on STDOUT (e.g., displaying S3 object listings as a readable table)
- **Version**: 0.10.0
- **Type**: Pure Python

## Agreed Python Modules and Versions

*[This section is a placeholder to be updated once the user provides answers to the module-related questions.]*

| Module Name | Module Purpose | Version | Type |
|---|---|---|---|
| [TBD] | [TBD] | [TBD] | [TBD] |

---

# Question Rationale

The requirements are clear on scope, SDK, and field names, but leave open three practical categories that are essential for implementation:

1. **Credential mapping** — UAC's Credential Field has four attributes (`user`, `password`, `token`, `passphrase`). Without knowing the AWS authentication method, the correct mapping cannot be determined.
2. **Output design** — The requirements name input fields but say nothing about what users will see when a task runs (UAC UI output fields, STDOUT content, Extension Output JSON). These decisions directly affect how useful the demo appears to evaluators.
3. **Edge case behavior** — Two straightforward situations need a defined behavior: what happens when a bucket has thousands of objects (List), and what happens when the target S3 key already exists (Upload).

---

# Clarifying Questions for Requirements Refinement

## Critical Decision Path Questions

**Question 1**: Which Python modules should be used, and should STDOUT output use formatted ASCII tables or plain text?

- **Question Type**: New Discussion topic
- **Context & Resources**:
  The requirements specify boto3 as the AWS SDK. The version check confirms **boto3 1.43.110** (and its full dependency chain — botocore 1.43.110, s3transfer 0.19.2, jmespath 1.1.0, python-dateutil 2.9.0, urllib3 2.8.0) are all pure Python and fully compatible with the Linux x86_64 build environment. No wheel compatibility concerns exist.

  The additional question is about STDOUT formatting for the List Objects action. Two options:

  - **Option A — Plain text output (no extra dependency)**: Objects are listed one per line, e.g.:
    ```
    my-folder/report-2024.csv  (1.2 MB, 2024-10-01)
    my-folder/data.json        (42 KB, 2024-09-15)
    Total: 2 objects
    ```

  - **Option B — ASCII table using `tabulate` (1 extra pure-Python dependency, ~40 KB)**: Objects are displayed in a clean, aligned table:
    ```
    ╭──────────────────────────────────┬──────────┬─────────────────────╮
    │ Object Key                       │ Size     │ Last Modified       │
    ├──────────────────────────────────┼──────────┼─────────────────────┤
    │ my-folder/report-2024.csv        │ 1.2 MB   │ 2024-10-01 08:30   │
    │ my-folder/data.json              │ 42 KB    │ 2024-09-15 14:10   │
    ╰──────────────────────────────────┴──────────┴─────────────────────╯
    2 objects found
    ```

  For a demo/showcase extension, the table format (Option B) is more visually compelling when presenting in UAC's task output view. tabulate is a well-maintained pure-Python package with no compatibility concerns. The `rounded_outline` table format shown above is the recommended style per UAC extension guidelines.

  Reference: [tabulate on PyPI](https://pypi.org/project/tabulate/)

- **Question Dependencies**: None
- **Recommended Answer**: **Option B** — use tabulate 0.10.0 for STDOUT table formatting. boto3 1.43.110 and its full dependency chain are confirmed.
- **Rationale**: For a demo/showcase extension, visual quality of STDOUT output directly affects how evaluators perceive the integration. The cost (one small pure-Python dependency) is minimal; the benefit is a noticeably more professional output.
- **Trade-offs**: Adds one dependency (~40 KB). Negligible for a bundled extension. Plain text (Option A) avoids it but produces less readable output.
- **Requirement Impact**: If Option B is chosen, `tabulate==0.10.0` is added to `requirements.txt`. No template changes.
- **User's Answer**: Option B — use tabulate 0.10.0 for formatted STDOUT table output; confirm boto3 1.43.110 and full dependency chain.

---

**Question 2**: How should AWS credentials be provided and mapped to the UAC Credential Field?

- **Question Type**: Clarification on existing requirement
- **Context & Resources**:
  The requirements name "AWS Credentials" as a field. In UAC, a Credential Field is a reference to a UAC Credential entity, which stores up to four attributes: `user`, `password`, `token`, and `passphrase`. Each attribute is mapped to exactly one piece of authentication data.

  AWS supports three authentication patterns:

  - **Option A — Standard IAM User (Access Key ID + Secret Access Key)**: The most common approach for external systems (non-AWS servers). A permanent IAM user is created in AWS, and its access key pair is stored in UAC. Mapping: `user` = Access Key ID (e.g., `AKIAIOSFODNN7EXAMPLE`), `password` = Secret Access Key (e.g., `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`).

  - **Option B — STS Temporary Credentials (Access Key ID + Secret Access Key + Session Token)**: Used with AWS IAM role assumption (e.g., via AWS STS `AssumeRole`). Temporary credentials expire automatically (typically 1–12 hours), making them more secure. Requires a third value: `token` = Session Token. Slightly more complex to set up in UAC (credentials must be rotated before expiry).

  - **Option C — No explicit credentials (Instance Role / Default Credential Chain)**: No credential field is needed. boto3 discovers credentials automatically from the agent host's environment (environment variables, `~/.aws/credentials` file, or EC2/ECS instance metadata). This works only when UAC agents run on AWS infrastructure with an assigned IAM Instance Role.

  For a portable demo that works on any Linux server (not only AWS-hosted agents), Option A is the standard choice.

  Reference: [boto3 Credentials Guide](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html)

- **Question Dependencies**: None
- **Recommended Answer**: **Option A** — Standard IAM User credentials: Access Key ID mapped to `user`, Secret Access Key mapped to `password`. No Session Token field needed.
- **Rationale**: Option A works on any server (AWS or non-AWS), requires no credential rotation, and is the universal baseline for AWS integrations. Options B and C add complexity without benefit for an MVP demo.
- **Trade-offs**: Long-lived credentials (vs. STS temporary ones) are a security consideration in production environments. For the stated demo purpose, this trade-off is explicitly acceptable. IAM policies can restrict the key to S3 read/write only, limiting blast radius.
- **Requirement Impact**: None — the existing "AWS Credentials" field accommodates this mapping directly.
- **User's Answer**: Option A — Standard IAM User credentials: `user` = Access Key ID, `password` = Secret Access Key.

---

## Essential Input/Output Questions

**Question 3**: What object information should be displayed per entry in the List Objects output, and what output-only field should appear in the UAC task UI?

- **Question Type**: New Discussion topic
- **Context & Resources**:
  When listing S3 objects, the AWS S3 API returns several metadata fields per object. The choice of what to show affects both the STDOUT table and the UAC UI's output-only field.

  **STDOUT per-object columns** — three options:

  | Column Set | Fields Shown | Best For |
  |---|---|---|
  | Option A — Minimal | Object Key only | Very simple listing |
  | Option B — Standard | Object Key, Size (human-readable), Last Modified date | Practical browsing (recommended) |
  | Option C — Full | Object Key, Size, Last Modified, Storage Class, ETag | Deep inspection |

  **Output-Only Field in UAC UI** (always visible in the task summary panel):
  - UAC best practice is 2–3 output-only fields showing the most important runtime result at a glance.
  - For List Objects, a natural choice is: `Objects Found: 42` (a count field).
  - For Upload File (separate action), a natural choice is: `Uploaded Object: s3://my-bucket/path/to/file.csv`.

  A shared `Status` output-only field (e.g., `Success: Listed 42 objects`) is standard across both actions.

- **Question Dependencies**: None
- **Recommended Answer**: **Option B** — display Object Key, human-readable Size, and Last Modified date in the STDOUT table. UAC output-only fields: one shared `Status` field (used by both actions) + one action-specific field (`Objects Found` count for List Objects; `Uploaded Object` S3 URI for Upload File).
- **Rationale**: Standard columns provide the right level of detail for a demo without clutter. Storage class and ETag are rarely useful during a live demo. Two output-only fields is the right balance per UAC guidelines.
- **Trade-offs**: Full metadata (Option C) would show more but overwhelms a demo audience. Minimal output (Option A) is too sparse to be impressive.
- **Requirement Impact**: Adds two output-only fields to the template:
  - `Status` (Text Field, Output Only) — shared across actions, e.g., `Success: Listed 42 objects`
  - `Objects Found` (Text Field, Output Only, visible only when action = List Objects) — e.g., `42`
  - `Uploaded Object` (Text Field, Output Only, visible only when action = Upload File) — e.g., `s3://my-bucket/reports/q4.csv`
- **User's Answer**: Option B — Object Key, human-readable Size, Last Modified date on STDOUT. Two output-only fields: `Status` (shared) and action-specific (`Objects Found` count / `Uploaded Object` S3 URI).

---

**Question 4**: What should happen when the Upload File action targets an S3 key that already exists in the bucket?

- **Question Type**: New Discussion topic
- **Context & Resources**:
  Amazon S3 is an object store: uploading to an existing key silently replaces (overwrites) the previous object with no versioning or warning, unless S3 Versioning is enabled on the bucket. The extension has two behavioral options:

  - **Option A — Always overwrite (S3 native behavior)**: Upload proceeds regardless of whether the object key already exists. The existing object is replaced. Simple, one API call, no extra latency.

  - **Option B — Error if object already exists**: Before uploading, the extension performs a `head_object` check. If the key exists, it raises an error (return code 1). The user must explicitly choose a different key or delete the existing object first. Requires an extra API call and adds complexity.

  Note: boto3's `upload_file` method (which internally uses `s3transfer`) handles multipart uploads automatically for large files, independent of this overwrite decision.

- **Question Dependencies**: None
- **Recommended Answer**: **Option A** — Always overwrite. Standard S3 behavior; no extra API call; appropriate for an MVP.
- **Rationale**: S3's "put wins" semantics are well understood. Adding a pre-check doubles API calls and adds code complexity with no benefit for a demo integration. Users who need protection can manage it via IAM policies or S3 Versioning at the bucket level.
- **Trade-offs**: Silent overwrites could be unexpected for users unfamiliar with S3 semantics. A clear note in the `Status` output field (e.g., `Success: Uploaded s3://bucket/key`) serves as implicit confirmation.
- **Requirement Impact**: None — the existing Upload File fields are sufficient.
- **User's Answer**: Option A — always overwrite; standard S3 behavior with no pre-existence check.

---

## Functional Behavior Questions

**Question 5**: Should the List Objects action cap the number of objects shown in STDOUT and Extension Output when a bucket contains a large number of objects?

- **Question Type**: New Discussion topic
- **Context & Resources**:
  S3 buckets can contain millions of objects. The AWS S3 API returns results in pages of up to 1,000 objects per page, requiring pagination for larger buckets. If the extension writes every object to STDOUT and Extension Output without a limit:

  1. **UAC database bloat**: All task output (STDOUT + Extension Output JSON) is stored in UAC's database. Thousands of rows can significantly increase storage consumption.
  2. **UI performance**: The UAC task output view becomes slow or unresponsive when rendering very large text blocks.

  The UAC extension best practice is to use an environment variable `UE_MAX_OUTPUT_RECORDS` to cap inline output. The default is 100 records. When truncated, the output includes a clear note:
  ```
  Note: Showing 100 of 4,532 objects. Set UE_MAX_OUTPUT_RECORDS environment variable to increase this limit.
  ```

  This cap applies only to what is *displayed* in STDOUT and Extension Output — it does not affect the actual S3 objects or the API call itself. The `Objects Found` output-only field always shows the true total count regardless of the cap.

  Environment variables in UAC are set per task definition in the standard "Environment Variables" section, requiring no extra template field.

  Reference: Large Output Safety Net Pattern (ue-architect-notes.md)

- **Question Dependencies**: None
- **Recommended Answer**: Yes — apply a default cap of 100 objects, configurable via `UE_MAX_OUTPUT_RECORDS` environment variable.
- **Rationale**: Essential safety net for any extension producing variable-length record output. Zero template cost (environment variable, not a field). Standard practice per UAC extension guidelines.
- **Trade-offs**: Users who need to see more than 100 objects must set the environment variable explicitly. This is a minor operational step and far outweighs the risk of uncontrolled output size.
- **Requirement Impact**: No new template fields. The `Objects Found` output-only field (from Q3) will always show the true total, even when STDOUT is truncated.
- **User's Answer**: Yes — cap at 100 objects by default using `UE_MAX_OUTPUT_RECORDS` environment variable. True total count always shown in the `Objects Found` output field.

---

**Question 6**: What should the Extension Output (machine-readable JSON) contain for each action?

- **Question Type**: New Discussion topic
- **Context & Resources**:
  Extension Output is a JSON object produced when the task reaches its final state (Success, Failed, or Cancelled). It is accessible to downstream UAC tasks and workflows via variable substitution, enabling automation chains (e.g., "list objects → process each object in a loop").

  For a demo/showcase extension, richer Extension Output better illustrates UAC's automation capabilities to evaluators.

  **For List Objects**, two options:

  - **Option A — Summary only**:
    ```json
    {
      "result": {
        "bucket": "my-demo-bucket",
        "region": "us-east-1",
        "total_count": 42,
        "shown_count": 42
      }
    }
    ```

  - **Option B — Full object list** (respecting `UE_MAX_OUTPUT_RECORDS` cap):
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

  **For Upload File**, two options:

  - **Option A — Confirmation only**:
    ```json
    {
      "result": {
        "bucket": "my-demo-bucket",
        "key": "reports/q4.csv"
      }
    }
    ```

  - **Option B — Full upload details**:
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

  In failure scenarios, both options include a standard error block: `{"error": {"type": "...", "message": "..."}}`.

- **Question Dependencies**: Q5 (if object cap is applied, the `objects` array in List Objects JSON reflects the cap, and `shown_count` will differ from `total_count`)
- **Recommended Answer**: **Option B for both actions** — include full object list (with cap from Q5) for List Objects, and full upload details for Upload File.
- **Rationale**: A demo extension benefits from rich Extension Output because it demonstrates UAC's downstream automation capability to evaluators. With the 100-record cap in place, the JSON payload remains manageable. A simple error object is included on failure for clean error propagation.
- **Trade-offs**: Larger JSON payload vs. richer automation capability. The record cap from Q5 keeps the list manageable. Option A (summary only) is smaller but less impressive as a demo.
- **Requirement Impact**: No new template fields. Extension Output is generated at runtime by the extension code.
- **User's Answer**: Option B for both actions — full object list (capped) with total_count/shown_count for List Objects; full upload details (bucket, key, S3 URI, size, region) for Upload File.
