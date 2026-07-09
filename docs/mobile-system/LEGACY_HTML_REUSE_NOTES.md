# Legacy HTML Reuse Notes

## Purpose

This file records how the existing verified HTML profiles under `profiles/` are used as reference material for the new Analyzer + Flutter MVP direction.

The existing HTML files are treated as proven behavior references, not as the final product architecture.

## Existing HTML profiles found

```text
profiles/flux1_dev/normal/comfyui_mobile.html
profiles/flux2_klein/normal/comfyui_mobile.html
profiles/flux_full/comfyui_mobile.html
profiles/flux1_dev/pixelart/comfyui_pixelart.html
profiles/flux1_dev/icon/comfyui_icon_mobile.html
profiles/sdxl/chibi/comfyui_sdxl_chibi.html
profiles/sdxl/pixelart/comfyui_sdxl_pixelart.html
```

## Important file identity note

The following two files currently have the same blob SHA and appear to be identical at the file-content level:

```text
profiles/flux1_dev/normal/comfyui_mobile.html
profiles/flux2_klein/normal/comfyui_mobile.html
```

`profiles/flux_full/comfyui_mobile.html` has a different blob SHA and should be treated as a different file even though the filename is the same.

## Useful proven behavior from existing HTML

The existing normal HTML contains a ComfyUI flow that is useful as a reference:

```text
1. Normalize the ComfyUI URL by removing trailing slashes.
2. Save the ComfyUI URL to localStorage.
3. Use /object_info as a connection/runtime capability check.
4. Generate a browser-side clientId.
5. Connect to /ws with the same clientId used for /prompt.
6. Submit /prompt with { prompt, client_id }.
7. Watch /ws executing/progress events.
8. Treat executing node null as completion.
9. Fetch /history/{prompt_id} after completion.
10. Extract images from history outputs.
11. Fetch/display images through /view.
12. If WebSocket is unavailable, fall back to polling /history/{prompt_id}.
```

## Reused in this PR

### 1. URL path preservation

Static review found that the new Flutter/prototype code could lose path-based proxy URL prefixes.

Fixed:

```text
mobile-app/flutter_mvp/lib/services/comfy_api_client.dart
mobile-app/flutter_mvp/lib/services/comfy_progress_client.dart
mobile-app/prototype/comfy-progress.js
```

Why:

```text
Path-based URLs such as https://host/proxy/8188 must become:
https://host/proxy/8188/system_stats
wss://host/proxy/8188/ws

They must not become:
https://host/system_stats
wss://host/ws
```

### 2. History polling fallback

Existing HTML used WebSocket progress when available, but kept `/history/{prompt_id}` polling as a fallback when WebSocket was not connected.

The Flutter GenerateScreen now keeps polling `/history/{prompt_id}` after `/prompt`, even when WebSocket progress is unavailable or intermittently fails.

Fixed:

```text
mobile-app/flutter_mvp/lib/screens/generate_screen.dart
```

Changes:

```text
- Waiting status changed to "Submitted; waiting for history...".
- History polling now waits 80 times at 1.5 second intervals.
- Temporary /history errors do not immediately fail the generation flow.
- WebSocket executing null now shows "Execution complete; loading history...".
```

## Not reused directly

Do not directly copy these parts from the legacy HTML into the new architecture:

```text
- prompt preset content
- model-specific hardcoded workflow construction
- NSFW or profile-specific option lists
- fixed Flux-only model filenames as global app assumptions
- old UI layout as final app architecture
```

Reason:

```text
The new direction is dynamic profile import and patch_targets, not fixed handwritten HTML per workflow.
```

## How to use legacy HTML going forward

Use existing HTML as:

```text
- behavior reference
- fallback logic reference
- RunPod/ComfyUI practical flow reference
- known-good workflow operation reference
```

Do not use it as:

```text
- final architecture
- source of app_profile schema
- source of universal model assumptions
- content/prompt template source
```

## Next validation impact

During RunPod/Android validation, compare the new MVP against the existing HTML behavior:

```text
- Can connect to ComfyUI.
- Can submit /prompt with client_id.
- Can receive /ws events when available.
- Can still finish via /history polling if /ws is not available.
- Can fetch/display images through /view.
```
