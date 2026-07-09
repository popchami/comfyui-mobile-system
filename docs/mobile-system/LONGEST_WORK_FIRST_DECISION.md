# Longest Work First Decision

## Purpose

This document records the current execution priority.

The next work should start from the highest-cost architecture area, not from small visible app features.

## Decision

The first priority is:

```text
app_profile.json v2 schema design
+
Capability-based Analyzer implementation plan
```

This is the longest and most important work because it affects every later feature.

## Why this comes first

The app must eventually handle workflows that may include:

```text
image output
video output
audio output
text output
3D output
unknown file output
subgraphs
bypass / mute / switches
wildcards
LoRA
ControlNet
IPAdapter
LLM / Ollama / Gemma
external API / Partner nodes
unknown custom nodes
```

If the profile schema is too narrow, later support for these features will require repeated rewrites.

Therefore, the profile contract must be expanded before deeper implementation.

## Work already started

The following documents were added for this priority:

```text
docs/mobile-system/APP_PROFILE_V2_SCHEMA_DRAFT.md
docs/mobile-system/CAPABILITY_ANALYZER_IMPLEMENTATION_PLAN.md
```

These define:

```text
fields[]
structure
capabilities
outputs
runtime_requirements
warnings
patch_targets
compatibility
shared control rendering
```

## Core rule

```text
workflow.json = preserved execution body
app_profile.json = smartphone operation map
patch_targets = exact safe edit targets
```

The app must not recreate the workflow.

The Analyzer must not pretend unknown workflows are fully supported.

## Implementation order

The long work should proceed in this order:

```text
1. Preserve and parse workflow.json.
2. Read runtime node definitions from the actual ComfyUI environment.
3. Extract operation candidates by input capability.
4. Apply known semantic detectors for better labels and grouping.
5. Analyze subgraph / bypass / switch / active path state.
6. Run safety validator before exposing editable fields.
7. Generate app_profile v2 data.
8. Keep v1/MVP output compatible until the app migrates.
```

## Guardrail

```text
Do not start by adding many one-off UI features.
Do not hardcode image-only assumptions.
Do not build a full ComfyUI graph editor.
Do not auto-download models.
Do not auto-install custom nodes.
Do not replace unknown nodes.
Do not mark partial workflows as supported just because some fields are editable.
```

## Current next target

The next meaningful implementation target is:

```text
Add capability-based operation candidate extraction to the Analyzer,
preferably behind debug/v2 output so the current MVP profile remains stable.
```
