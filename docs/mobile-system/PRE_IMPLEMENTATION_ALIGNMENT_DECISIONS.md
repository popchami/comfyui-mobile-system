# Pre-Implementation Alignment Decisions

## Purpose

This file edits the platform/reference inventory into concrete decisions before handing the PR to Claude.

Claude should treat this file as the current decision layer above the raw inventory files.

## Status

```text
Implementation has not hardened yet.
This is the right time to adjust the plan.
```

## Main decision

Do not discard the current system.

Do adjust the implementation strategy:

```text
Before:
Analyzer manually detects as much as possible from workflow JSON.

After:
Analyzer uses official ComfyUI APIs wherever possible,
then translates the result into a safe mobile profile.
```

## Product direction remains unchanged

The project remains:

```text
A mobile-first ComfyUI workflow execution system using safe mobile profiles.
```

It is still not:

```text
- a full ComfyUI replacement
- a full workflow editor
- a generic ComfyUI portal
- a ComfyUI Manager replacement
- a Playwright/Chromium-first system
- a RunPod Serverless-first product
```

## Adopt from current system

Keep these as core project assets:

```text
- app_profile.json as the shared contract
- patch_targets-only editing
- mobile_profile_export.zip
- profile download from ComfyUI to smartphone
- original workflow preservation
- generation-copy patching
- Android-first Flutter MVP
- no automatic installs
- no automatic model downloads
```

## Adopt from official ComfyUI APIs

These should be treated as source-of-truth runtime APIs:

```text
/prompt
/ws
/history/{prompt_id}
/view
/upload/image
/upload/mask
/system_stats
```

These should move earlier than originally planned:

```text
/object_info
/object_info/{node_class}
/models
/models/{folder}
```

Reason:

```text
They reduce manual guessing and make Analyzer output more accurate.
```

Expected use:

```text
/object_info:
- node input metadata
- field types
- combo choices
- required/optional information
- custom node compatibility hints

/models:
- available model folders
- available model names
- missing checkpoint / LoRA / VAE warnings
```

## Adopt from RunPod

For now, keep RunPod Pods as the primary validation target.

Use:

```text
- Pod web proxy
- GPU hosting
- SSH / JupyterLab when needed
- templates / custom containers later
```

Do not move to Serverless yet.

Reason:

```text
Current validation still needs visible ComfyUI runtime and custom node testing.
```

Serverless remains later work.

## Adopt from comfy-portal-endpoint only as reference

Use as reference for:

```text
- UI workflow to API workflow conversion concept
- health/readiness endpoint design
- convert endpoint separation
- cold start state handling
```

Do not adopt now:

```text
- code
- project identity
- Playwright / Chromium as MVP requirement
- automatic dependency install behavior
- full workflow management server direction
```

Current stance:

```text
UI workflow conversion should remain optional and post-MVP unless Claude proves it is required for minimum validation.
```

## What should change before Claude runtime validation

Documentation and handoff should change.

Code should not be broadly rewritten before Claude checks.

Claude should first verify:

```text
1. Whether current custom routes are minimal and necessary.
2. Whether current Analyzer can still validate the MVP without /object_info.
3. Whether /object_info should be the first post-validation improvement.
4. Whether /models should be the first model-check improvement.
5. Whether the current profile zip flow is still useful.
```

## What should not change before Claude runtime validation

Do not start these before Claude alignment:

```text
- full /object_info implementation
- full /models implementation
- UI workflow conversion implementation
- Playwright/Chromium integration
- Serverless conversion
- storage migration
- advanced workflow compatibility
- ComfyUI Manager registration
```

## Revised Claude task order

Claude should follow this order:

```text
1. Read direction guardrails.
2. Read system inventory.
3. Read this decision file.
4. Confirm the current direction is still correct.
5. Identify any custom logic that should be replaced by official APIs later.
6. Do not rewrite large areas yet.
7. Run minimum runtime validation.
8. Fix only blockers.
9. Record follow-up priorities.
```

## Near-term priority after validation

If runtime validation passes, the next technical priorities should be:

```text
1. /object_info-based field metadata support
2. /models-based missing model checks
3. file-based profile storage if SharedPreferences becomes too weak
4. clearer error messages
5. optional UI workflow conversion research
```

## Final decision

```text
Use ComfyUI and RunPod foundations first.
Build only the missing mobile profile layer.
Keep external repositories as references, not as the center of the system.
```
