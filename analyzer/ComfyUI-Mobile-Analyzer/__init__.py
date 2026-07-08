"""ComfyUI-Mobile-Analyzer custom node pack skeleton."""

from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

try:
    from .server import setup_routes
    WEB_DIRECTORY = "web"
except Exception:
    WEB_DIRECTORY = "web"

__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "WEB_DIRECTORY",
]
