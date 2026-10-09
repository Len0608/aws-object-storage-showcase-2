"""Actions module - Business logic implementations."""

from actions.output import ActionOutput
from actions.list_objects import list_objects
from actions.upload_file import upload_file

# Maps action choice values (as sent by UAC) to action functions.
# Keys must exactly match the SingleChoice values defined in template.json.
ACTION_MAPPER = {
    "List Objects": list_objects,
    "Upload File": upload_file,
}
