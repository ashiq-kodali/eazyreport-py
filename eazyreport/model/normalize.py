"""Template loading, normalization, and validation."""
import json
import os
from typing import Any, Dict, Union

from .document import LayoutDocument, LayoutPage


def normalize_document(data: Union[Dict[str, Any], LayoutDocument]) -> LayoutDocument:
    """Normalize a dictionary or LayoutDocument into a fully initialized LayoutDocument."""
    if isinstance(data, LayoutDocument):
        return data
    if not isinstance(data, dict):
        raise ValueError(f"Expected dict or LayoutDocument, got {type(data).__name__}")
    return LayoutDocument.from_dict(data)


def load_template(template: Union[str, bytes, Dict[str, Any], LayoutDocument]) -> LayoutDocument:
    """Load an RTPL template from a file path, JSON string, dict, or LayoutDocument."""
    if isinstance(template, LayoutDocument):
        return template
    if isinstance(template, dict):
        return normalize_document(template)
    if isinstance(template, bytes):
        template = template.decode('utf-8')

    if isinstance(template, str):
        trimmed = template.strip()
        # Check if it is a JSON string
        if trimmed.startswith('{'):
            try:
                parsed = json.loads(trimmed)
                return normalize_document(parsed)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON string template: {e}") from e

        # Check if it is a file path
        if os.path.exists(template):
            with open(template, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                parsed = json.loads(content)
                return normalize_document(parsed)

    raise ValueError("Template must be a LayoutDocument, dict, JSON string, or valid file path to an .rtpl file.")
