"""OutputFields dataclass for real-time UI updates."""

from dataclasses import dataclass, asdict
from typing import Optional
from universal_extension import ui
from fields.types import Text


@dataclass
class OutputFields:
    """Real-time output fields for UAC UI updates.

    Fields map to the Output Only fields defined in template.json:
    - status        (Text Field 5) — short description of execution outcome
    - objects_found (Text Field 6) — total object count (List Objects action)
    - uploaded_object (Text Field 7) — S3 URI of uploaded object (Upload File action)
    """

    status: Optional[Text] = None
    objects_found: Optional[Text] = None
    uploaded_object: Optional[Text] = None

    def update(self, **fields):
        """Update fields and sync with UAC UI in real-time.

        Args:
            **fields: Field names and values to update (strings will be wrapped in Text)
        """
        for field_name, field_value in fields.items():
            if hasattr(self, field_name):
                # Wrap string values in Text type
                if isinstance(field_value, str):
                    field_value = Text(field_value)
                setattr(self, field_name, field_value)
        ui.update_output_fields(fields)

    def to_dict(self) -> dict:
        """Get current fields as dictionary.

        Returns:
            Dict with non-None field values (Text wrappers unwrapped to strings)
        """
        result = {}
        for k, v in asdict(self).items():
            if v is not None:
                # Extract value from Text wrapper
                result[k] = v.value if isinstance(v, Text) else v
        return result

    def clear(self):
        """Reset all fields to None."""
        self.status = None
        self.objects_found = None
        self.uploaded_object = None
