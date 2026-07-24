"""Server routes for ComfyUI-Mobile-Analyzer.

Runtime validation inside ComfyUI is still required.
"""

from __future__ import annotations

import time
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
    for path in sorted(PROFILE_DIR.glob("*.zip"), key=lambda item: item.stat().st_mtime, reverse=True):
        stat = path.stat()
        profiles.append(
            {
                "id": path.stem,
                "name": path.stem,
                "file": path.name,
                "status": "ready",
                "size_bytes": stat.st_size,
                "modified_at": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(stat.st_mtime)),
                "download_url": f"/mobile_analyzer/profiles/{path.stem}/download",
            }
        )
    return profiles


def resolve_profile_zip(profile_id: str) -> Path:
    safe_name = Path(profile_id).name
    if safe_name.endswith(".zip"):
        safe_name = safe_name[:-4]
    return PROFILE_DIR / f"{safe_name}.zip"


async def handle_profiles(request):
    return web.json_response(list_profiles())


async def handle_download(request):
    profile_id = request.match_info.get("profile_id", "")
    zip_path = resolve_profile_zip(profile_id)
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
