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

## Most important specs

- `APP_PROFILE_SCHEMA.md`
- `WORKFLOW_PATCH_RULES.md`
- `UI_VISIBILITY_RULES.md`
- `MVP_SCOPE.md`
- `ANALYZER_SPEC.md`
- `MOBILE_APP_SPEC.md`

## Critical rules

- `app_profile.json` is the contract between Analyzer and app.
- The app only edits fields listed in `patch_targets`.
- The app does not edit node connections in MVP.
- Unknown nodes are not deleted.
- Hidden nodes stay in `workflow.json`.
- Pass-through nodes are normally hidden from UI.
- Use `needs_attention`, not `dangerous`.
- The smartphone app does not install missing nodes or models in MVP.
- Users should fix ComfyUI environment and re-run Analyzer if requirements are missing.
- No manual smartphone file transfer. The app downloads profile zip from ComfyUI.

## MVP target

Analyzer:

- Load workflow JSON
- Classify basic nodes
- Export app_profile.json
- Zip with workflow.json
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

## Next work

1. Create actual `ComfyUI-Mobile-Analyzer` custom node pack.
2. Implement `MobileProfileExporter` minimal version.
3. Implement `/mobile_analyzer/profiles` and `/download` API.
4. Create example `mobile_profile_export_basic.json`.
5. Build a simple smartphone app or web prototype that reads `app_profile.json` and sends patched workflow.
