# V2 Debug Exporter Implemented

## Purpose

This document records the next implementation step after capability-based operation candidate extraction.

A separate debug exporter node was added so v2 profile output can be tested without breaking the current MVP exporter.

## Added node

```text
Mobile Profile V2 Debug Exporter
```

Source file:

```text
analyzer/ComfyUI-Mobile-Analyzer/nodes_v2_debug.py
```

Registered through:

```text
analyzer/ComfyUI-Mobile-Analyzer/__init__.py
```

## Why a separate node

The current MVP node remains:

```text
Mobile Profile Exporter
```

It still produces the current MVP-compatible output.

The new v2 debug node produces a separate package for schema and Analyzer validation.

This avoids breaking the existing smartphone app while enabling v2 work to continue.

## New zip output

The v2 debug exporter writes:

```text
workflow.json
app_profile_v2_debug.json
analysis_debug.json
README.txt
```

It does not write or replace the MVP `app_profile.json`.

## What app_profile_v2_debug.json includes

```text
schema_version = 2.0-debug
compatibility
capabilities
ui
fields[]
patch_targets{}
structure
runtime_requirements
outputs[]
warnings[]
debug
```

## What changed from previous step

Previous step:

```text
operation_candidates were only written to analysis_debug.json.
```

This step:

```text
selected operation_candidates are converted into v2 debug fields[] and patch_targets{}.
```

## Safety rule

This is still debug output.

```text
v2 debug fields are not yet production app controls.
```

The current MVP app should continue using the existing v1 `app_profile.json` output from `Mobile Profile Exporter`.

## Current limitations

```text
- No RunPod runtime validation yet.
- No Android app migration yet.
- Subgraph/bypass/switch structures are placeholders.
- v2 output is for inspection and schema development.
- The validator is still basic and must become stricter before production use.
```

## Next implementation target

```text
Add real validator logic that decides which v2 fields can move from debug-only to app-safe.
```

Validator must check:

```text
exact patch target path
value type compatibility
connection vs value input
active/inactive branch state
subgraph scope
sensitive fields
external API risk
output handling
runtime requirements
```
