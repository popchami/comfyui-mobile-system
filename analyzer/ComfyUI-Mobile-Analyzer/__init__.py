"""ComfyUI-Mobile-Analyzer custom node pack skeleton."""

from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

try:
    # Import server module for ComfyUI route registration side effects.
    from . import server as _server  # noqa: F401
except Exception:
    # Keep node import safe during static review outside ComfyUI.
    pass

__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
]
