# HANDOFF: ComfyUI Mobile System

## Current decision

Move away from fixed HTML-per-workflow design.

New direction:

```text
ComfyUI-side Analyzer
  ↓
mobile_profile_export.zip
  ↓
Smartphone app imports profile
  ↓
Dynamic simple UI
  ↓
Patch workflow
  ↓
Submit to ComfyUI
```

## Main components

### 1. ComfyUI-Mobile-Analyzer

A custom node pack for ComfyUI.

First node:

```text
MobileProfileExporter
```

It analyzes workflow JSON and outputs:

```text
mobile_profile_export.zip
  workflow.json
  app_profile.json
  source_info.json
  README.txt
```

Output directory:

```text
ComfyUI/output/mobile_profiles/
```

### 2. Smartphone App

The smartphone app connects to ComfyUI, downloads profile zip files, reads `app_profile.json`, renders a UI, patches `workflow.json`, submits to `/prompt`, and displays result images.

## Files added in this PR

Documentation:

```text
docs/mobile-system/
  README.md
  ARCHITECTURE.md
  APP_PROFILE_SCHEMA.md
  WORKFLOW_PATCH_RULES.md
  UI_VISIBILITY_RULES.md
  MVP_SCOPE.md
  ANALYZER_SPEC.md
  MOBILE_APP_SPEC.md
  HANDOFF.md
```

Analyzer draft:

```text
analyzer/ComfyUI-Mobile-Analyzer/
  README.md
  __init__.py
  nodes.py
  server.py
  requirements.txt
```

Mobile app placeholder:

```text
mobile-app/README.md
```

## Critical rules

- `app_profile.json` is the contract between Analyzer and app.
- The app only edits fields listed in `patch_targets`.
- The app does not edit node connections in MVP.
- Unknown nodes are not deleted.
- Hidden nodes stay in `workflow.json`.
- Pass-through nodes are hidden from normal UI.
- Use `needs_attention`, not `dangerous`.
- The smartphone app does not install missing nodes or models in MVP.
- Users should fix ComfyUI environment and re-run Analyzer if requirements are missing.
- No manual smartphone file transfer. The app downloads profile zip from ComfyUI.

## MVP target

Analyzer:

- Load workflow JSON
- Classify basic nodes
- Export app profile zip
- Provide profile list/download API

Smartphone app:

- Register ComfyUI URL
- Download profile zip
- Render simple UI
- Edit prompt / seed / steps / cfg
- Patch workflow
- Submit to ComfyUI
- Display generated image

## Not MVP

- Full ControlNet UI
- Full IPAdapter UI
- FaceDetailer UI
- Upscale UI
- Wildcard UI
- LLM/Ollama UI
- Auto custom node install
- Auto model download
- Google Drive auto-save
- Payment
- Multi-user support

## Current skeleton caveat

The analyzer implementation is a draft skeleton. It still needs to be tested inside a real ComfyUI runtime.

Known limitations:

- object_info checks are not implemented
- model checks are not implemented
- UI workflow to API workflow conversion is not implemented
- current workflow capture from ComfyUI UI is not implemented
- server route registration may need adjustment after runtime testing

## Next work

1. Test `analyzer/ComfyUI-Mobile-Analyzer` inside ComfyUI.
2. Confirm `MobileProfileExporter` appears in the node menu.
3. Paste a simple API-format workflow JSON and export a zip.
4. Confirm `/mobile_analyzer/profiles` returns the created zip.
5. Confirm `/mobile_analyzer/profiles/{id}/download` downloads it.
6. Build a simple mobile/web prototype that reads `app_profile.json` and sends patched workflow.
