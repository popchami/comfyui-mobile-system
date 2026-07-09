# Analyzer Export Workflow Node Composition

## Purpose

This file records the proposed minimum node composition for the dedicated Analyzer export workflow.

The dedicated workflow is not a generation workflow.
It is the workflow that loads a user-provided workflow, analyzes it, and packages it for the smartphone app.

## User idea to preserve

The dedicated Analyzer export workflow may only need three core nodes:

```text
1. Workflow Load Node
2. Dedicated Custom Analyzer Node
3. Smartphone App ZIP Export Node
```

This is the preferred mental model for the first design pass.

## Proposed node chain

```text
[Workflow Load Node]
        ↓
[Dedicated Custom Analyzer Node]
        ↓
[Smartphone App ZIP Export Node]
```

## 1. Workflow Load Node

Role:

```text
Receive or load the user's ComfyUI workflow.
```

Possible input methods:

```text
- Paste API workflow JSON text.
- Load workflow JSON from a file path.
- Select a workflow file from a known folder.
- Later: upload from smartphone or a custom route.
```

MVP method:

```text
Paste API workflow JSON text.
```

Possible outputs:

```text
workflow_json
workflow_name
source_type
source_path_or_label
load_warnings
```

Important rules:

```text
- Do not modify the workflow.
- Do not assume it is image-only.
- Validate JSON enough to avoid passing broken data forward.
- Preserve the original workflow content for export.
```

## 2. Dedicated Custom Analyzer Node

Role:

```text
Analyze the loaded workflow and create smartphone app metadata.
```

This is the core custom node logic.

It should inspect:

```text
- nodes
- class_type
- inputs
- links / references
- model names
- custom node dependencies
- likely editable values
- output nodes
- output types
- unsupported or unknown areas
```

Possible outputs:

```text
app_profile_json
normalized_workflow_json
analysis_report_json
missing_models
missing_nodes
warnings
outputs
patch_targets
```

Important rules:

```text
- Do not delete unknown nodes.
- Do not rewrite the workflow destructively.
- Do not auto-download models.
- Do not auto-install custom nodes.
- Do not assume prompt/seed/width/height always exist.
- Do not assume output is always image.
```

## 3. Smartphone App ZIP Export Node

Role:

```text
Package the preserved workflow and app metadata into a smartphone-readable profile zip.
```

Input:

```text
workflow_json
app_profile_json
analysis_report_json optional
profile_name
profile_id optional
```

Output:

```text
export_path
profile_id
zip_filename
```

Minimum zip contents:

```text
workflow.json
app_profile.json
```

Future zip contents:

```text
metadata.json
analysis_report.json
compatibility_report.json
preview.json
```

Important rules:

```text
- Keep zip structure stable.
- Do not put generated output files in the profile zip by default.
- Do not include private/local absolute paths unless needed for debugging.
- Make the zip discoverable through /mobile_analyzer/profiles.
- Make the zip downloadable through /mobile_analyzer/profiles/{id}/download.
```

## MVP simplification option

For the earliest MVP, these three roles can be inside one node:

```text
Mobile Profile Exporter
```

But the conceptual design should still treat them as three roles:

```text
load
analyze
zip export
```

This makes it easier to split the node later without changing the product direction.

## Why three nodes may be better later

Separating the workflow into three nodes gives clearer responsibilities:

```text
Workflow Load Node
- handles input and validation

Dedicated Custom Analyzer Node
- handles workflow analysis and app_profile generation

Smartphone App ZIP Export Node
- handles packaging, profile IDs, and download registration
```

This also makes debugging easier when a workflow fails.

## First implementation recommendation

Start with one existing MVP node if needed:

```text
Mobile Profile Exporter
```

But internally structure the code as:

```text
load_workflow()
analyze_workflow()
build_app_profile()
export_profile_zip()
```

Then later expose these as separate nodes if useful.

## Acceptance criteria

The dedicated Analyzer export workflow is successful when:

```text
- A user-provided workflow can be loaded.
- The workflow is preserved.
- app_profile.json is produced.
- patch_targets are produced.
- output types are recorded or safely marked unknown.
- missing models/custom nodes are recorded.
- a profile zip is created.
- the smartphone app can import the zip.
- the smartphone app can submit generation without corrupting the workflow.
```

## Product guardrail

```text
The user should prepare the generation workflow only.
The dedicated Analyzer export workflow should handle loading, analysis, and zip packaging.
```
