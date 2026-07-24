# V2 Validated Debug Exporter Implemented

## Purpose

This document records the next Analyzer implementation step:

```text
operation_candidates
  ↓
validator
  ↓
validated v2 debug fields
  ↓
validated v2 debug patch_targets
```

## Added node

```text
Mobile Profile V2 Validated Debug Exporter
```

Source file:

```text
analyzer/ComfyUI-Mobile-Analyzer/nodes_v2_validated_debug.py
```

Registered through:

```text
analyzer/ComfyUI-Mobile-Analyzer/__init__.py
```

## Why this exists

The previous v2 debug exporter converted operation candidates directly into fields.

That was useful for schema exploration, but it did not clearly separate:

```text
candidate
safe editable field
expert editable field
review-required field
preserve-only field
disabled field
```

This new exporter introduces a validator layer between operation candidate extraction and v2 field creation.

## New zip output

The validated debug exporter writes:

```text
workflow.json
app_profile_v2_validated_debug.json
analysis_debug.json
README.txt
```

It does not replace the existing MVP `app_profile.json`.

## What app_profile_v2_validated_debug.json includes

```text
schema_version = 2.0-validated-debug
compatibility
capabilities
ui
fields[]
patch_targets{}
structure
runtime_requirements
outputs[]
warnings[]
validation
  summary
  results
debug
```

## Validator statuses

The validator classifies each operation candidate as one of:

```text
safe_editable
expert_editable
review_required
preserve_only
disabled
```

Only these become editable debug fields:

```text
safe_editable
expert_editable
```

`expert_editable` remains warning-gated and should stay in Expert/Unknown UI until explicitly supported.

## Checks currently performed

The first validator pass checks:

```text
- target node exists
- target input exists
- target input is a direct value, not a connection
- sensitive credential-like fields are disabled
- file path / URL-like fields require review
- unknown value/control types are preserve-only
- connection-oriented runtime types are preserve-only
- missing runtime node definitions add warnings
- expert_unknown fields are not treated as normal supported fields
```

## Important limitation

This is still debug output.

```text
Validated debug does not mean production app-ready.
```

The current smartphone app should continue using the existing v1 `app_profile.json` from `Mobile Profile Exporter`.

## Current node stack

```text
Mobile Profile Exporter
- current MVP-compatible exporter
- writes app_profile.json

Mobile Profile V2 Debug Exporter
- writes app_profile_v2_debug.json
- converts operation_candidates to fields without full validator maturity

Mobile Profile V2 Validated Debug Exporter
- writes app_profile_v2_validated_debug.json
- classifies candidates through validator before creating fields
```

## Next implementation target

```text
Add fixture-based static tests for the v2 validated debug exporter.
```

Test fixtures should cover:

```text
basic txt2img
unknown custom node with STRING
sensitive api_key field
URL/path-like field
connection input ignored
output detection
missing runtime definition warning
```
