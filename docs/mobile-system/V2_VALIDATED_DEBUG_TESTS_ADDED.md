# V2 Validated Debug Tests Added

## Purpose

This document records fixture-based static tests for the v2 validated debug exporter.

## Added test file

```text
analyzer/ComfyUI-Mobile-Analyzer/tests/test_v2_validated_debug.py
```

## Why this matters

The v2 validated debug exporter introduces a validator between:

```text
operation_candidates
```

and:

```text
fields[]
patch_targets{}
```

The tests make sure the validator does not accidentally treat unsafe or unclear inputs as normal app controls.

## Covered cases

The test file now covers:

```text
basic txt2img-style direct values
connection inputs are ignored
sensitive api_key field is disabled
URL-like field requires review
unknown custom STRING becomes Expert editable, not normal supported
SaveImage output is detected as image output
validated profile pieces include validation/compatibility data
LoRA name and strength fields are extracted safely
LoRA model/clip connection inputs are not patched
ControlNet-like strength fields are classified as advanced
video output detection
audio output detection
external API warning behavior
missing runtime definition warning behavior
runtime definition metadata affects source confidence and required flags
no-output workflows become unsupported for generation
```

## How to run

From repository root:

```bash
python -m unittest analyzer/ComfyUI-Mobile-Analyzer/tests/test_v2_validated_debug.py
```

## Important note

These are static tests.

They do not replace:

```text
RunPod validation
ComfyUI runtime validation
Android app validation
real workflow validation
```

They only protect the Analyzer's local validator logic from basic regressions.

## Current limitation

The tests are designed to run outside a real ComfyUI process.

They do not yet prove:

```text
ComfyUI can load every new node on RunPod
ComfyUI can execute the exporter prompt on RunPod
real custom node runtime metadata is read correctly
real workflow zips import correctly into Android
```

## Next target

```text
Run the static tests in an actual environment, then fix any import/runtime issues.
```

After that, add fixture categories for:

```text
inpaint / mask
wildcard / dynamic prompt
subgraph placeholder behavior
bypass/switch placeholder behavior
multi-output workflows
unknown output type
```
