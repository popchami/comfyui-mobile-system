# HTML Parameter Reuse and RunPod Proof

## Purpose

This file records that the existing full HTML already contains working parameter handling for generation, and that a RunPod URL was successfully used for image generation.

This is important because it proves that the project already has a working reference for ComfyUI API flow and common generation parameters.

## Short answer

```text
Yes, the parameter behavior can be reused.
```

But the reuse target is:

```text
- API flow
- parameter mapping behavior
- UI control ideas
- known working RunPod connection pattern
```

not:

```text
- fixed HTML workflow construction
- fixed node ids
- fixed FLUX-only workflow shape
- fixed prompt/preset content
```

## Existing full HTML parameter behavior

The full HTML already handles common generation parameters such as:

```text
- negative prompt
- denoise
- CFG
- steps
- sampler
- scheduler
- seed
- guidance
- LoRA name
- LoRA strength
- batch size
```

These are useful references for the smartphone app UI and Analyzer field detection.

## Existing workflow mapping pattern

The full HTML demonstrates a working parameter mapping pattern:

```text
negative prompt
  -> CLIPTextEncode.text

seed
steps
cfg
sampler_name
scheduler
denoise
  -> KSampler inputs

guidance
  -> FluxGuidance or equivalent guidance node

LoRA name / strength
  -> LoraLoader inputs
```

This mapping is valid as a reference, but must not be hardcoded to one workflow.

## RunPod proof value

The user has confirmed that image generation worked using a RunPod URL through the existing HTML.

This proves that this general flow is practical:

```text
RunPod ComfyUI URL
  ↓
/prompt
  ↓
/ws progress when available
  ↓
/history/{prompt_id}
  ↓
/view image display
```

It also supports the current app direction:

```text
Smartphone app saves RunPod URL
  ↓
Smartphone app submits workflow to /prompt
  ↓
Smartphone app listens to /ws or falls back to /history
  ↓
Smartphone app displays result through /view
```

## Analyzer responsibilities

The Analyzer should detect common parameters in user-provided workflows.

Initial detection targets:

```text
CLIPTextEncode.text
  -> prompt or negative_prompt candidate

KSampler.seed
KSampler.steps
KSampler.cfg
KSampler.sampler_name
KSampler.scheduler
KSampler.denoise
  -> generation settings

FluxGuidance.guidance or similar
  -> guidance setting

LoraLoader.lora_name
LoraLoader.strength_model
LoraLoader.strength_clip
  -> LoRA settings

EmptyLatentImage.width
EmptyLatentImage.height
EmptyLatentImage.batch_size
  -> size/output settings
```

Important:

```text
Do not assume every workflow uses these exact node class names.
Use these as known rules first, then add conservative support for equivalent custom nodes later.
```

## Smartphone app responsibilities

When app_profile.json exposes these fields, the smartphone app should render usable controls:

```text
negative prompt
  -> multiline text field

CFG
  -> number/slider field

denoise
  -> number/slider field

steps
  -> integer field/slider

sampler
  -> select/dropdown when options are known

scheduler
  -> select/dropdown when options are known

seed
  -> number field + random seed + use last seed

guidance
  -> number/slider field

LoRA strength
  -> number/slider field

batch
  -> integer field
```

The existing HTML UI can be used as a behavior reference, but the Flutter app must remain generated from app_profile.json.

## Source-of-truth rule

For the new app:

```text
app_profile.json + workflow.json are the source of truth.
```

The full HTML proves behavior.
It does not define final patch targets for user-provided workflows.

Patch targets must come from the Analyzer.

## What must not happen

```text
- Do not copy fixed HTML node ids into user workflows.
- Do not rebuild user workflows using the old HTML generator.
- Do not assume all workflows have FLUX-specific nodes.
- Do not assume CFG/denoise/guidance mean the same thing in every model family.
- Do not expose a parameter if the Analyzer cannot produce a safe patch_target.
```

## Validation requirements

Validate with real workflows that include:

```text
- negative prompt
- CFG
- denoise
- steps
- sampler
- scheduler
- seed
- guidance
- LoRA strength
- batch size
```

For each field validate:

```text
- Analyzer detects the field.
- app_profile.json includes the correct field metadata.
- patch_target points to the correct node/input.
- smartphone app renders the right control.
- changing the value changes the submitted workflow.
- generation still works on RunPod.
```

## Product guardrail

```text
The working full HTML + RunPod generation result is evidence that the API flow and parameter handling are viable.
Use it as a proven reference.
Do not turn it into a fixed architecture that overrides user-provided workflows.
```
