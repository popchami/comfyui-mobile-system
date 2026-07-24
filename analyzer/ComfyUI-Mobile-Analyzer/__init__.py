"""ComfyUI-Mobile-Analyzer custom node pack skeleton."""

from .nodes import NODE_CLASS_MAPPINGS as V1_NODE_CLASS_MAPPINGS
from .nodes import NODE_DISPLAY_NAME_MAPPINGS as V1_NODE_DISPLAY_NAME_MAPPINGS

try:
    from .nodes_v2_debug import NODE_CLASS_MAPPINGS as V2_DEBUG_NODE_CLASS_MAPPINGS
    from .nodes_v2_debug import NODE_DISPLAY_NAME_MAPPINGS as V2_DEBUG_NODE_DISPLAY_NAME_MAPPINGS
except Exception:
    V2_DEBUG_NODE_CLASS_MAPPINGS = {}
    V2_DEBUG_NODE_DISPLAY_NAME_MAPPINGS = {}

try:
    from .nodes_v2_validated_debug import NODE_CLASS_MAPPINGS as V2_VALIDATED_DEBUG_NODE_CLASS_MAPPINGS
    from .nodes_v2_validated_debug import NODE_DISPLAY_NAME_MAPPINGS as V2_VALIDATED_DEBUG_NODE_DISPLAY_NAME_MAPPINGS
except Exception:
    V2_VALIDATED_DEBUG_NODE_CLASS_MAPPINGS = {}
    V2_VALIDATED_DEBUG_NODE_DISPLAY_NAME_MAPPINGS = {}

NODE_CLASS_MAPPINGS = {
    **V1_NODE_CLASS_MAPPINGS,
    **V2_DEBUG_NODE_CLASS_MAPPINGS,
    **V2_VALIDATED_DEBUG_NODE_CLASS_MAPPINGS,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    **V1_NODE_DISPLAY_NAME_MAPPINGS,
    **V2_DEBUG_NODE_DISPLAY_NAME_MAPPINGS,
    **V2_VALIDATED_DEBUG_NODE_DISPLAY_NAME_MAPPINGS,
}

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
