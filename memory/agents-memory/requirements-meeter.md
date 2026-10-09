# Requirements Meeter Output

## Zipsafe Decision
- **Result**: false
- **Reason**: Packages with data files — boto3 ships JSON resource definitions under `boto3/data/` and `boto3/examples/`; botocore ships endpoint and retry configuration JSON under `botocore/data/` and a CA certificate bundle (`cacert.pem`). These non-Python files cannot be loaded from inside a zip archive at runtime.

## CLI Tools
None — this extension makes no calls to external CLI tools on the agent host.

## Python Dependencies
- boto3==1.43.110 — Has data files (JSON resource definitions in `boto3/data/`)
- botocore==1.43.110 — Has data files (JSON endpoint/retry config, `cacert.pem` in `botocore/data/`)
- jmespath==1.1.0 — Pure Python
- python-dateutil==2.9.0 — Pure Python
- s3transfer==0.19.2 — Pure Python
- tabulate==0.10.0 — Pure Python
- urllib3==2.8.0 — Pure Python

## Setup.py Changes
- VENDOR_FOLDER added: no
- data_files updated: no
