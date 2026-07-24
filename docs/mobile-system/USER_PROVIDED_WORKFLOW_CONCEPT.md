# User-Provided Workflow Concept

## Purpose

This file records the corrected product concept for workflows.

The app is not meant to ship only a small set of app-owned dedicated workflows.

The user prepares any ComfyUI workflow. The system analyzes that workflow and exports an app-readable profile.

## Correct concept

```text
User prepares any ComfyUI workflow
  ↓
Dedicated custom node is added/used inside ComfyUI
  ↓
The custom node reads/analyzes the user workflow
  ↓
The custom node exports workflow.json + app_profile.json as profile zip
  ↓
The smartphone app imports the profile zip
  ↓
The smartphone app renders safe controls from app_profile.json
  ↓
The smartphone app patches only patch_targets
  ↓
The smartphone app submits the workflow to ComfyUI
```

## What the user needs to do

```text
Prepare the workflow only.
```

The user should not need to:

```text
- write app_profile.json manually
- decide patch_targets manually
- create a mobile UI manually
- edit Flutter code
- rebuild the app per workflow
```

## Meaning of dedicated workflow in this project

The phrase "dedicated workflow" must not mean:

```text
The developer prepares a fixed app-owned workflow such as flux_normal and the app only supports that workflow.
```

In this project, the correct meaning is:

```text
A user-provided ComfyUI workflow that is passed through the dedicated Analyzer/custom-node export path so it becomes usable by the smartphone app.
```

## Meaning of dedicated custom node

The dedicated custom node is:

```text
ComfyUI-Mobile-Analyzer
```

Its job is not to replace the user's workflow.

Its job is to:

```text
- load/read the user workflow
- inspect nodes and inputs
- detect safe editable fields
- detect model references
- detect custom node references
- create app_profile.json
- preserve the original workflow.json
- create patch_targets
- export a profile zip
- expose profile list/download routes
```

## What must stay true

```text
- Any valid ComfyUI workflow should be analyzable eventually.
- Unknown nodes must be preserved.
- The workflow should not be simplified destructively.
- The app must patch only fields described in patch_targets.
- The app must not become a full workflow editor.
- The app must not require a new Flutter build for each workflow.
- The user should only prepare the workflow.
```

## What may be provided later

The project may still provide example workflows later, but only as examples or test fixtures.

Examples:

```text
- sample flux workflow
- sample pixel art workflow
- sample icon workflow
- sample img2img workflow
```

These examples must not become the only supported path.

## Product direction guardrail

```text
Do not narrow the product into a fixed set of app-owned workflows.
The goal is user-provided workflow import and mobile profile generation.
```

## Validation impact

During validation, test at least one user-provided workflow path:

```text
1. User prepares or selects an existing ComfyUI workflow.
2. Analyzer reads/exports it.
3. App imports generated profile zip.
4. App displays editable fields.
5. App submits generation without destroying unknown workflow structure.
```
