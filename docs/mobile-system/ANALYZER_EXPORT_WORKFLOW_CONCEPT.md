# Analyzer Export Workflow Concept

## Purpose

This file records the corrected need for a dedicated Analyzer export workflow.

The user still prepares any ComfyUI generation workflow, but the project also needs a dedicated workflow whose purpose is to load/analyze/export that user workflow.

## Correct structure

There are two different workflows:

```text
1. User generation workflow
   - Prepared by the user.
   - Can be any valid ComfyUI workflow.
   - It is the workflow that actually generates images.

2. Analyzer export workflow
   - Prepared by this project.
   - Contains the dedicated Analyzer/custom node.
   - Its job is to read/load the user generation workflow.
   - It exports workflow.json + app_profile.json as a mobile profile zip.
```

## Correct flow

```text
User prepares any ComfyUI workflow
  ↓
User opens/runs the Analyzer export workflow
  ↓
Analyzer export workflow contains the dedicated custom node
  ↓
User provides or selects the prepared workflow JSON
  ↓
Dedicated custom node analyzes that workflow
  ↓
Dedicated custom node exports:
    - workflow.json
    - app_profile.json
    - mobile_profile_export.zip
  ↓
Smartphone app downloads/imports profile zip
  ↓
Smartphone app renders safe UI and patches only patch_targets
```

## Meaning of dedicated workflow

In this project, "dedicated workflow" means:

```text
A fixed Analyzer/export workflow used to convert user-provided workflows into mobile profiles.
```

It does not mean:

```text
A fixed image-generation workflow that users must use for all generation.
```

## What the user prepares

The user prepares:

```text
- Any normal ComfyUI workflow they want to use for generation.
```

The user does not need to prepare:

```text
- app_profile.json
- patch_targets
- Flutter UI
- Android code
```

## What the project prepares

The project prepares:

```text
- ComfyUI-Mobile-Analyzer custom node
- Analyzer export workflow
- profile zip output convention
- app_profile.json schema
- smartphone app import/render/patch/submit flow
```

## Analyzer export workflow requirements

The Analyzer export workflow should include the dedicated custom node, such as:

```text
Mobile Profile Exporter
```

The workflow must provide a way for the user to feed in the user generation workflow.

Supported or future input methods:

```text
- Paste API workflow JSON text into the node.
- Load workflow JSON from a file path.
- Select a workflow from a known ComfyUI folder.
- Later: drag/drop or route-based upload if ComfyUI UI support allows it.
```

## Minimum MVP input method

For MVP, the safest input method is:

```text
Paste API workflow JSON text into Mobile Profile Exporter.
```

Reason:

```text
- It avoids file picker complexity inside ComfyUI.
- It works with exported API workflow JSON.
- It is easy to validate on RunPod.
```

## Output requirements

The Analyzer export workflow must output:

```text
workflow.json
app_profile.json
mobile_profile_export.zip
```

The export zip must be available through:

```text
/mobile_analyzer/profiles
/mobile_analyzer/profiles/{id}/download
```

## Safety rules

```text
- Do not modify the user generation workflow destructively.
- Preserve unknown nodes.
- Preserve custom nodes even if they are not understood.
- Do not auto-download models.
- Do not auto-install custom nodes.
- Do not force the user to use a project-owned generation workflow.
- Do not make the smartphone app a full workflow editor.
```

## Validation impact

RunPod validation must include:

```text
1. Prepare or select a real user generation workflow.
2. Open/run the Analyzer export workflow.
3. Feed the user workflow into Mobile Profile Exporter.
4. Export profile zip.
5. Confirm workflow.json is preserved.
6. Confirm app_profile.json is generated.
7. Confirm profile zip appears in /mobile_analyzer/profiles.
8. Confirm profile zip downloads.
9. Confirm Android app can import and run that generated profile.
```

## Product guardrail

```text
The dedicated workflow is for analysis/export.
The user generation workflow remains user-provided.
```
