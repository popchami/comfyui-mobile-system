# V2 Validated Debug Tests Added

## Purpose

This document records the first fixture-based static tests for the v2 validated debug exporter.

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

The first test file covers:

```text
basic txt2img-style direct values
connection inputs are ignored
sensitive api_key field is disabled
URL-like field requires review
unknown custom STRING becomes Expert editable, not normal supported
SaveImage output is detected as image output
validated profile pieces include validation/compatibility data
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

## Next target

```text
Add more fixtures for LoRA, ControlNet, video output, audio output, missing runtime definitions, and external API warning behavior.
```
