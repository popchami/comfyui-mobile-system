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
3. Restore the saved ComfyUI URL on app start.
4. Use /object_info as a connection/runtime capability check.
5. Generate a browser-side clientId.
6. Connect to /ws with the same clientId used for /prompt.
7. Submit /prompt with { prompt, client_id }.
8. Watch /ws executing/progress events.
9. Treat executing node null as completion.
10. Fetch /history/{prompt_id} after completion.
11. Extract images from history outputs.
12. Fetch/display images through /view.
13. If WebSocket is unavailable, fall back to polling /history/{prompt_id}.
14. Upload an input image through /upload/image.
15. Show a local preview of the selected input image before generation.
16. Add generated images to an in-session history list.
17. Open generated images in a larger preview.
18. Copy/reuse seed value.
19. Mark selected controls visually.
20. Use collapsible setting sections to avoid overwhelming the mobile screen.
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

### 3. ComfyUI URL restore

Existing HTML restores the saved ComfyUI URL from localStorage on startup.

Flutter SetupScreen now restores and saves the ComfyUI URL through `shared_preferences`.

Fixed:

```text
mobile-app/flutter_mvp/lib/screens/setup_screen.dart
```

Changes:

```text
- Restore saved ComfyUI URL on SetupScreen startup.
- Save normalized ComfyUI URL after successful connection.
- Save normalized ComfyUI URL before opening remote profiles.
```

### 4. Selected image preview

Existing HTML previews a selected i2i image locally before generation.

Flutter GenerateScreen now shows a local preview for selected image fields.

Fixed:

```text
mobile-app/flutter_mvp/lib/screens/generate_screen.dart
```

Changes:

```text
- Show Image.file preview for selected image fields.
- Keep uploaded filename display after /upload/image.
```

### 5. Session generated image history

Existing HTML adds generated images to an in-session history grid.

Flutter GenerateScreen now keeps an in-session generated image strip for the current screen session.

Fixed:

```text
mobile-app/flutter_mvp/lib/screens/generate_screen.dart
```

Changes:

```text
- Add generated images to _sessionHistory after /history result is found.
- Deduplicate by type/subfolder/filename.
- Display a horizontal Session history strip.
```

### 6. Larger image preview

Existing HTML opens generated images in a larger preview.

Flutter GenerateScreen now opens generated images in a dialog with InteractiveViewer.

Fixed:

```text
mobile-app/flutter_mvp/lib/screens/generate_screen.dart
```

Changes:

```text
- Tap generated image to open preview dialog.
- Tap session history thumbnail to open preview dialog.
- Show filename and selectable image URL in the preview.
```

## App-prepared components from legacy HTML

These are useful as app-side components because they are UI/UX or client behavior, not workflow-specific model content:

```text
S: Already reused or should be app core
- URL normalization and saved URL restore
- connection check status
- client_id lifecycle
- /prompt + /ws + /history + /view generation flow
- /history polling fallback
- /upload/image handling
- selected image preview
- generated image display
- local generated history list
- larger image preview screen

A: Useful after MVP validation
- seed copy/reuse
- last-used field values per profile
- visual selected-state markers
- collapsible advanced sections
- friendly progress labels mapped from node roles

B: Useful only after Analyzer metadata improves
- dynamic LoRA list from /object_info
- sampler/scheduler option lists from /object_info
- model existence warnings from /models
- feature visibility based on detected workflow nodes

C: Do not reuse for MVP
- Jupyter notebook execution from the app
- setup notebook runner
- hardcoded Flux-only workflow construction
- NSFW/content-specific prompt lists
- model-specific prompt preset content
```

## Official API vs legacy HTML

Use official APIs as the source of truth when possible:

```text
/system_stats
/object_info
/models
/upload/image
/prompt
/ws
/history/{prompt_id}
/view
/queue
/interrupt
```

Use legacy HTML only for proven client-side behavior around those APIs:

```text
- when to call each API
- how to recover when /ws is unavailable
- what to show in the mobile UI
- how to keep the mobile flow understandable
```

## Not reused directly

Do not directly copy these parts from the legacy HTML into the new architecture:

```text
- prompt preset content
- model-specific hardcoded workflow construction
- NSFW or profile-specific option lists
- fixed Flux-only model filenames as global app assumptions
- old UI layout as final app architecture
- Jupyter notebook execution as normal app behavior
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
- mobile UI friction reference
```

Do not use it as:

```text
- final architecture
- source of app_profile schema
- source of universal model assumptions
- content/prompt template source
- automatic setup executor
```

## Next validation impact

During RunPod/Android validation, compare the new MVP against the existing HTML behavior:

```text
- Can connect to ComfyUI.
- Can remember and restore ComfyUI URL.
- Can submit /prompt with client_id.
- Can receive /ws events when available.
- Can still finish via /history polling if /ws is not available.
- Can upload and preview input images.
- Can fetch/display images through /view.
- Can add generated images to session history.
- Can open generated images in larger preview.
```
