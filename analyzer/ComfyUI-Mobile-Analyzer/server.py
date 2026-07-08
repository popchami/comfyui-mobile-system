"""Server route skeleton for ComfyUI-Mobile-Analyzer.

This file is a draft. It will need validation inside a real ComfyUI runtime.
"""

from __future__ import annotations

import json
from pathlib import Path

try:
    from aiohttp import web
    from server import PromptServer
except Exception:  # Allows static import outside ComfyUI.
    web = None
    PromptServer = None


PROFILE_DIR = Path("output") / "mobile_profiles"


def list_profiles():
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    profiles = []
    for path in sorted(PROFILE_DIR.glob("*.zip"), reverse=True):
        profiles.append(
            {
                "id": path.stem,
                "name": path.stem,
                "file": path.name,
                "status": "ready",
            }
        )
    return profiles


async def handle_profiles(request):
    return web.json_response(list_profiles())


async def handle_download(request):
    profile_id = request.match_info.get("profile_id", "")
    safe_name = Path(profile_id).name
    zip_path = PROFILE_DIR / f"{safe_name}.zip"
    if not zip_path.exists():
        return web.json_response({"error": "profile not found"}, status=404)
    return web.FileResponse(zip_path)


def setup_routes():
    if PromptServer is None or web is None:
        return
    app = PromptServer.instance.app
    app.router.add_get("/mobile_analyzer/profiles", handle_profiles)
    app.router.add_get("/mobile_analyzer/profiles/{profile_id}/download", handle_download)


try:
    setup_routes()
except Exception:
    pass
