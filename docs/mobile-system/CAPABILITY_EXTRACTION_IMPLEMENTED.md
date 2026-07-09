# Capability Extraction Implemented

## Purpose

This document records the first source-level implementation step for the longest-work-first plan.

## Implemented change

`analyzer/ComfyUI-Mobile-Analyzer/nodes.py` now emits a debug-only capability extraction file inside exported profile zips:

```text
analysis_debug.json
```

The existing MVP output remains:

```text
workflow.json
app_profile.json
source_info.json
README.txt
```

The existing `app_profile.json` is still v1-compatible and is not migrated to v2 yet.

## What analysis_debug.json contains

```text
schema_version
workflow_summary
runtime_node_definitions
operation_candidates
candidate_summary
safety_note
```

## New behavior

During profile export, the Analyzer now:

```text
1. Parses and preserves workflow.json.
2. Collects workflow class_type values.
3. Best-effort reads runtime node definitions from the ComfyUI environment.
4. Extracts operation candidates from non-connection inputs.
5. Normalizes possible input types into shared app control candidates.
6. Writes the result to analysis_debug.json.
```

## Candidate extraction examples

The new candidate extraction maps likely input capabilities like this:

```text
STRING  -> text / textarea candidate
INT     -> integer / seed candidate
FLOAT   -> float / slider candidate
BOOLEAN -> switch candidate
COMBO   -> select / model_picker candidate
IMAGE   -> image_upload candidate
MASK    -> mask_editor candidate
AUDIO   -> audio_upload candidate
VIDEO   -> video_upload candidate
JSON    -> readonly candidate
```

## Important safety rule

```text
operation_candidates are not final editable fields.
```

They are only debug-visible candidates.

Before a candidate becomes a real app control, it must still pass:

```text
semantic detector
exact patch target generation
validator
compatibility/warning logic
```

## Why this is safe for MVP

The current app reads `app_profile.json`.

This implementation keeps `app_profile.json` v1-compatible and adds `analysis_debug.json` as a separate ZIP file.

That means the current MVP app should not need to change just because this debug data exists.

## Current limitation

This has not yet been runtime-validated on RunPod.

The runtime node definition reader is best-effort:

```text
If ComfyUI runtime metadata is available, use it.
If it is unavailable, infer candidate types from current workflow input values and input names.
```

## Next source-level target

```text
Turn selected operation_candidates into v2 fields[] behind a separate v2/debug output path.
Do not replace the current v1 app_profile.json yet.
```
