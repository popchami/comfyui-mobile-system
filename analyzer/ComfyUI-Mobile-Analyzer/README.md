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

- Load workflow JSON from pasted JSON text
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

## Temporary install test

Copy this folder into ComfyUI custom nodes:

```text
ComfyUI/custom_nodes/ComfyUI-Mobile-Analyzer/
```

Then restart ComfyUI.

Expected result:

```text
Mobile Profile Exporter
```

appears in the node menu under:

```text
mobile_analyzer
```

## Smoke test

1. Open ComfyUI.
2. Add `Mobile Profile Exporter` node.
3. Open `examples/minimal_api_workflow.json`.
4. Copy the JSON text.
5. Paste it into `workflow_json_text`.
6. Set profile name to `Minimal API Workflow`.
7. Queue the workflow.
8. Check output folder:

```text
ComfyUI/output/mobile_profiles/
```

Expected zip:

```text
minimal_api_workflow_YYYYMMDD_HHMMSS.zip
```

Inside the zip:

```text
workflow.json
app_profile.json
source_info.json
README.txt
```

## Current limitations

- ComfyUI `object_info` check is not implemented yet.
- Missing model file check is not implemented yet.
- UI workflow to API workflow conversion is not implemented yet.
- Current opened workflow capture is not implemented yet.
- ZIP download API needs runtime validation.

## Install later

Eventually this folder should become its own installable ComfyUI custom node repository.

For now, this is stored inside `comfyui-mobile-system` as a development draft.
