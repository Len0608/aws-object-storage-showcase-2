"""ActionOutput dataclass for action return values."""

import logging
from dataclasses import dataclass, field
from typing import Optional, Any, Dict, List

from tabulate import tabulate

from utility import SizeFormatter

logger = logging.getLogger("UNV")


@dataclass
class ActionOutput:
    """Output from action functions.

    Covers both actions:
      - List Objects: bucket, region, total_count, shown_count, objects
      - Upload File:  bucket, region, key, s3_uri, size_bytes

    No stdout_options / output_options control fields exist in this template,
    so print_output() always renders all available data and to_dict() always
    returns all available data.
    """

    # --- List Objects fields ---
    # Total count of objects in the bucket (true total, unaffected by cap)
    total_count: Optional[int] = None
    # Number of objects included in STDOUT table and Extension Output
    shown_count: Optional[int] = None
    # List of object dicts: {"key": str, "size_bytes": int, "last_modified": str}
    objects: Optional[List[Dict[str, Any]]] = None

    # --- Upload File fields ---
    # Target S3 object key
    key: Optional[str] = None
    # Full S3 URI of uploaded object
    s3_uri: Optional[str] = None
    # Size of uploaded file in bytes
    size_bytes: Optional[int] = None

    # --- Shared fields ---
    # S3 bucket name (both actions)
    bucket: Optional[str] = None
    # AWS region (both actions)
    region: Optional[str] = None

    # --- Output field sync references ---
    # These are populated by the action and used by extension.py to sync output fields
    # via OutputFields.update() before print_output() is called.
    # Stored here so to_dict() can expose them if needed; primary sync happens in action.
    _output_status: Optional[str] = field(default=None, repr=False)
    _output_objects_found: Optional[str] = field(default=None, repr=False)
    _output_uploaded_object: Optional[str] = field(default=None, repr=False)

    # --- No control fields in this template ---
    # stdout_options and output_options are intentionally absent;
    # all output is always rendered.

    def print_output(self) -> None:
        """Print action results to STDOUT.

        List Objects: renders an ASCII table of objects plus count / truncation notice.
        Upload File:  prints a single confirmation line.
        """
        if self.objects is not None:
            # --- List Objects output ---
            rows = []
            for obj in self.objects:
                human_size = SizeFormatter.format(obj["size_bytes"])
                # last_modified is an ISO 8601 string; display first 16 chars "YYYY-MM-DDTHH:MM"
                raw_dt = obj.get("last_modified", "")
                # Convert ISO 8601 "2024-10-01T08:30:00Z" to "2024-10-01 08:30"
                display_dt = raw_dt[:16].replace("T", " ") if raw_dt else ""
                rows.append([obj["key"], human_size, display_dt])

            table = tabulate(
                rows,
                headers=["Object Key", "Size", "Last Modified"],
                tablefmt="rounded_outline",
            )
            print(table)
            print(f"{self.total_count} objects found")

            if self.total_count is not None and self.shown_count is not None:
                if self.total_count > self.shown_count:
                    print(
                        f"Note: Showing {self.shown_count} of {self.total_count} objects. "
                        "Set UE_MAX_OUTPUT_RECORDS environment variable to increase this limit."
                    )

        elif self.s3_uri is not None:
            # --- Upload File output ---
            local_file = getattr(self, "_local_file", self.key)
            human_size = SizeFormatter.format(self.size_bytes) if self.size_bytes is not None else "unknown"
            # _local_file is set by the action for the confirmation line
            source = getattr(self, "_local_file", None) or self.key or ""
            print(f"Uploaded {source} → {self.s3_uri} ({human_size})")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for Extension Output (unv_output result field).

        No output_options control; all populated fields are always included.

        List Objects returns:
            {"bucket": ..., "region": ..., "total_count": ..., "shown_count": ..., "objects": [...]}

        Upload File returns:
            {"bucket": ..., "key": ..., "s3_uri": ..., "size_bytes": ..., "region": ...}
        """
        output: Dict[str, Any] = {}

        if self.bucket is not None:
            output["bucket"] = self.bucket
        if self.region is not None:
            output["region"] = self.region

        # List Objects specific
        if self.total_count is not None:
            output["total_count"] = self.total_count
        if self.shown_count is not None:
            output["shown_count"] = self.shown_count
        if self.objects is not None:
            output["objects"] = self.objects

        # Upload File specific
        if self.key is not None:
            output["key"] = self.key
        if self.s3_uri is not None:
            output["s3_uri"] = self.s3_uri
        if self.size_bytes is not None:
            output["size_bytes"] = self.size_bytes

        return output
