# Workflow Compatibility Report Template

## Purpose

Use this template to evaluate whether a ComfyUI workflow can be safely used by the mobile system.

The goal is not to support every workflow immediately. The goal is to classify workflows clearly:

```text
supported
partial
needs_attention
unsupported
```

## Compatibility rule

```text
A workflow is mobile-compatible only if the Analyzer can preserve the workflow and expose safe patch_targets without turning the app into a full workflow editor.
```

## Basic report

```text
Workflow name:
Source:
- local
- GitHub
- Civitai
- ComfyUI export
- unknown

Workflow format:
- API workflow
- UI workflow
- unknown

Date tested:
Reviewer:
Analyzer branch/commit:
ComfyUI version/commit if known:

Overall status:
- supported
- partial
- needs_attention
- unsupported
```

## Workflow type

```text
Main type:
- text-to-image
- image-to-image
- inpaint
- upscale
- face detail
- ControlNet
- IPAdapter
- background removal
- multi-stage
- unknown

Uses image input:
- yes / no / unknown

Uses mask input:
- yes / no / unknown

Uses multiple outputs:
- yes / no / unknown
```

## Required models

```text
Checkpoint:
LoRA:
VAE:
ControlNet:
Upscale model:
IPAdapter model:
FaceDetailer model:
Other:
```

Model check result:

```text
- all found
- some missing
- unverified
- not checked
```

Missing models:

```text
- model 1:
- model 2:
```

## Required custom nodes

```text
Custom nodes detected:
- node/class 1:
- node/class 2:

Missing custom nodes:
- node/class 1:
- node/class 2:

Custom node check result:
- all found
- some missing
- unverified
- not checked
```

## Analyzer output

```text
Profile zip generated: yes / no
workflow.json included: yes / no
app_profile.json included: yes / no
app_profile parsed: yes / no
patch_targets count:
ui.simple field count:
warnings count:
compatibility.status:
```

## Exposed controls

```text
Prompt: exposed / hidden / not detected
Negative prompt: exposed / hidden / not detected
Seed: exposed / hidden / not detected
Steps: exposed / hidden / not detected
CFG: exposed / hidden / not detected
Sampler: exposed / hidden / not detected
Scheduler: exposed / hidden / not detected
Width: exposed / hidden / not detected
Height: exposed / hidden / not detected
Batch: exposed / hidden / not detected
Image input: exposed / hidden / not detected
Denoise: exposed / hidden / not detected
```

## Safety checks

```text
Unknown nodes preserved: yes / no / unknown
Workflow structure changed: yes / no / unknown
Only patch_targets patched: yes / no / unknown
Original workflow mutated: yes / no / unknown
Generation copy used: yes / no / unknown
```

## Runtime result

```text
/prompt accepted: yes / no / not tested
/ws progress received: yes / no / not tested
/history result available: yes / no / not tested
/view image fetched: yes / no / not tested
Android app displayed image: yes / no / not tested
```

## Failure notes

```text
Failure step:
Error message:
Technical details:
Likely cause:
```

## Decision

```text
Use in MVP:
- yes
- no
- only as test fixture
- defer

Reason:
```

## Next action

```text
- no action
- update Analyzer detection
- add warning
- add model check
- add custom node check
- require manual conversion
- defer until UI workflow conversion exists
- defer until advanced workflow support exists
```

## Example final classification

```text
supported:
Flat API workflow, known nodes, safe patch_targets, generation succeeds.

partial:
Profile exports and simple fields work, but model/custom node checks are unverified.

needs_attention:
Workflow may run, but missing model/custom node/advanced branch needs user action.

unsupported:
Workflow requires features the app should not handle yet, such as complex graph editing or unsupported conversion.
```
