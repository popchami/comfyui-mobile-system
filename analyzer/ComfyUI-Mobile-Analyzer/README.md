# ComfyUI-Mobile-Analyzer

ComfyUI-Mobile-Analyzer is a planned ComfyUI custom node pack for exporting smartphone-app-friendly workflow profiles.

## Status

Skeleton only. This folder is a temporary implementation starting point for review.

## Goal

Analyze a ComfyUI workflow and export:

```text
mobile_profile_export.zip
  workflow.json
  app_profile.json
  source_info.json
  README.txt
```

The smartphone app will download this zip from ComfyUI and use `app_profile.json` to build a mobile UI.

## First node

```text
MobileProfileExporter
```

## MVP behavior

- Load workflow JSON from a file path or pasted JSON text
- Detect basic nodes
- Create a minimal `app_profile.json`
- Put prompt / seed / steps / cfg into simple UI when found
- Keep unknown nodes in the workflow
- Save a zip into `ComfyUI/output/mobile_profiles/`

## Planned API

```text
GET /mobile_analyzer/profiles
GET /mobile_analyzer/profiles/{id}/download
```

## Install later

Eventually this folder should become its own installable ComfyUI custom node repository.

For now, this is stored inside `comfyui-mobile-system` as a development draft.
