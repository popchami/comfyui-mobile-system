# ComfyUI-Mobile-Analyzer Spec

## Role

ComfyUI-Mobile-Analyzer is a ComfyUI custom node pack that analyzes workflows and exports smartphone-app-friendly profile packages.

It runs inside ComfyUI.

The Analyzer is the release-critical bridge between completed user workflows and the smartphone app.

```text
User owns the completed workflow.
Analyzer must preserve it, understand it, and expose only safe controls.
```

## First custom node

Start with one integrated node:

```text
MobileProfileExporter
```

The workflow should stay simple. The analysis logic should live inside the custom node.

## MobileProfileExporter responsibilities

- Load workflow JSON
- Preserve original workflow JSON
- Detect workflow format
- Detect API / UI workflow format
- Analyze node list
- Analyze node connections
- Analyze active vs bypass-OFF state when possible
- Analyze subgraph context when possible
- Detect image upload / mask / paint / wildcard controls when present
- Check whether nodes exist in current ComfyUI
- Check missing nodes
- Check missing models
- Classify nodes for mobile UI
- Assign `ui_visibility`
- Assign compatibility level
- Generate safe `patch_targets`
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

## Compatibility levels

The Analyzer must not treat all workflows as equally safe.

It should classify a profile into one of these levels:

```text
supported
- Analyzer can preserve workflow.json.
- app_profile.json is valid.
- key inputs have safe patch_targets.
- output handling is understood.
- app can run/edit the workflow safely.

partial
- Some safe controls are available.
- Some parts are unknown or unsupported.
- Risky controls are not exposed.
- App can warn clearly.

unsupported
- Workflow can be preserved, but safe app editing/running is not proven.
- App must not expose risky patch_targets.
- App should show why the workflow is unsupported.
```

Potential app_profile section:

```json
{
  "compatibility": {
    "level": "partial",
    "reasons": [
      "Unknown custom node inside subgraph",
      "Output type could not be confirmed"
    ],
    "safe_to_generate": false,
    "safe_to_edit": true
  }
}
```

## Release safety rule

The Analyzer can enable release by supporting a limited set of workflows well.

The release model should be:

```text
Supported workflows run safely.
Unsupported workflows fail safely.
```

Do not release behavior where unknown workflows are silently treated as supported.

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
- Preserve workflow JSON
- List nodes
- Classify KSampler / CLIPTextEncode / LoadImage / SaveImage
- Detect prompt / negative prompt / seed / steps / cfg / denoise / sampler / scheduler
- Detect image input and basic mask/inpaint patterns when obvious
- Put prompt / seed / steps / cfg into simple UI when patch_targets are safe
- Put other nodes into expert or hidden
- Generate app_profile.json
- Include compatibility level
- Include warnings for unsupported/unknown areas
- Zip workflow.json and app_profile.json
- Save zip
- Return profile list via API
- Return zip via download API

## Design decision

Keep the dedicated workflow simple. Put smart behavior inside the custom node.

## Product guardrail

```text
The Analyzer must prefer safe unsupported over unsafe supported.
The app can be simple.
The workflow must not be corrupted.
Patch targets must be exact.
```