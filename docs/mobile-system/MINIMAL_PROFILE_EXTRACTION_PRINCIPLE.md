# Minimal Profile Extraction Principle

## Purpose

This file records an important clarification about the smartphone app and Analyzer scope.

The smartphone app does not need to deeply understand every part of the workflow.

The Analyzer also does not need to turn the entire workflow into a full app UI.

The core requirement is:

```text
Keep the original workflow intact.
Extract only the parts the user is likely to operate.
Patch only those parts.
Send the workflow to ComfyUI.
Receive the generated result.
```

## Correct understanding

```text
The smartphone app does not need to load every node as an editable UI.
```

Instead:

```text
workflow.json
  = original execution body

app_profile.json
  = smartphone operation map

patch_targets
  = places that can be safely edited
```

The app reads the profile to know what controls to show.

The app keeps the workflow as the execution body.

## What the Analyzer must extract

The Analyzer should prioritize fields that users commonly change:

```text
- prompt
- negative prompt
- seed
- steps
- CFG
- denoise
- sampler
- scheduler
- width
- height
- batch
- uploaded image input
- mask image input
- paint/mask editing requirement
- wildcard controls
- LoRA strength when safely identifiable
- ControlNet image/strength when safely identifiable
```

These should become app-facing fields only when safe patch_targets can be produced.

## What the Analyzer can leave as non-editable

The Analyzer can leave most of the workflow as non-editable but preserved:

```text
- node graph structure
- model loading structure
- VAE structure
- sampler input wiring
- custom node internals
- complex subgraph internals
- advanced post-processing chain
- save/output node structure
```

These remain inside workflow.json.

They do not need to become main app controls unless they are clearly safe and useful.

## Main app responsibility

The smartphone app should not become a full ComfyUI graph editor.

It should:

```text
1. Read app_profile.json.
2. Render only useful/safe controls.
3. Keep workflow.json as the execution source.
4. Apply only patch_targets.
5. Submit the patched workflow to ComfyUI /prompt.
6. Receive output through /history and /view or equivalent output handling.
```

## Why this matters

This reduces the scope dramatically.

The product does not need to understand every internal node to be useful.

It needs to correctly identify and safely expose what the user actually changes.

That means the first releasable app can be realistic if:

```text
- original workflows are preserved
- common user inputs are extracted
- unsupported fields are not exposed
- output handling works
- generation is delegated to ComfyUI
```

## Important guardrail

```text
Not shown in the app does not mean removed from the workflow.
Not editable in the app does not mean ignored by ComfyUI.
The full workflow is still sent to ComfyUI.
The app only changes selected safe values before sending.
```

## Product guardrail

```text
Do not build a full graph editor.
Do not recreate the workflow.
Do not simplify the workflow into a different workflow.
Preserve the user's workflow and expose only the operation points needed for smartphone use.
```
