# ComfyUI-Mobile-Analyzer Spec

## Role

ComfyUI-Mobile-Analyzer is a ComfyUI custom node pack that analyzes workflows and exports smartphone-app-friendly profile packages.

It runs inside ComfyUI.

## First custom node

Start with one integrated node:

```text
MobileProfileExporter
```

The workflow should stay simple. The analysis logic should live inside the custom node.

## MobileProfileExporter responsibilities

- Load workflow JSON
- Detect workflow format
- Detect API / UI workflow format
- Analyze node list
- Analyze node connections
- Check whether nodes exist in current ComfyUI
- Check missing nodes
- Check missing models
- Classify nodes for mobile UI
- Assign `ui_visibility`
- Generate `app_profile.json`
- Package `workflow.json` and `app_profile.json` into zip
- Save zip to `ComfyUI/output/mobile_profiles/`

## Inputs

Initial inputs:

- `workflow_source`
- `profile_name`
- `export_mode`
- `include_preview`
- `visibility_mode`

Initial implementation should prioritize workflow file input.

## export_mode

Options:

- `zip`
- `json_only`
- `debug`

Initial implementation may fix this to `zip`.

## visibility_mode

Options:

- `simple_first`
- `show_more`
- `expert`

Initial value: `simple_first`.

## Dedicated workflow

Provide one workflow first:

```text
examples/mobile_profile_export_basic.json
```

It should be basically one node:

```text
[MobileProfileExporter]
```

## Output package

```text
mobile_profile_export.zip
  workflow.json
  app_profile.json
  source_info.json
  README.txt
```

Optional:

```text
preview.png
thumbnail.png
analysis_debug.json
```

## Output directory

```text
ComfyUI/output/mobile_profiles/
```

## Smartphone API

The analyzer pack should expose:

```text
GET /mobile_analyzer/profiles
GET /mobile_analyzer/profiles/{id}/download
```

## Suggested repository structure

```text
ComfyUI-Mobile-Analyzer/
  __init__.py
  nodes.py
  server.py
  requirements.txt
  README.md
  examples/
    mobile_profile_export_basic.json
    output_app_profile_example.json
  docs/
    APP_PROFILE_SCHEMA.md
    SECURITY_POLICY.md
```

## Minimum implementation

- Load workflow JSON
- List nodes
- Classify KSampler / CLIPTextEncode / LoadImage / SaveImage
- Put prompt / seed / steps / cfg into simple UI
- Put other nodes into expert or hidden
- Generate app_profile.json
- Zip workflow.json and app_profile.json
- Save zip
- Return profile list via API
- Return zip via download API

## Design decision

Keep the dedicated workflow simple. Put smart behavior inside the custom node.
