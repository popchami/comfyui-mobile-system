# i2i / Mask / Inpaint Reuse and API Plan

## Purpose

This file records how to carry forward the existing full HTML i2i / mask / inpaint work into the new user-provided-workflow architecture.

The existing full HTML has useful mobile UX and proven ComfyUI API behavior.

But the new app must not copy its fixed workflow construction directly.

## Correct reuse rule

```text
Reuse behavior patterns.
Do not reuse fixed workflow construction as the new architecture.
```

Reusable from full HTML:

```text
- i2i ON/OFF control
- i2i / inpaint mode switching
- image picker and preview
- /upload/image usage
- mask canvas UX
- paint / erase / clear mask tools
- brush size control
- mask upload before generation
- result fetch through /history and /view
```

Do not reuse directly:

```text
- fixed FLUX-only workflow construction
- fixed node ids
- fixed model names
- fixed prompt preset content
- fixed HTML visual layout as final Flutter UI
```

## Existing full HTML behavior reference

The existing `profiles/flux_full/comfyui_mobile.html` already includes:

```text
- i2i wrapper and toggle
- i2i / Inpaint mode buttons
- image upload input
- preview image
- mask canvas
- paint / erase / clear buttons
- brush size slider
```

It also uploads the selected image through:

```text
POST /upload/image
```

and stores the returned image name for workflow patching.

For inpaint, it uploads a mask before generation and uses a workflow structure similar to:

```text
LoadImage(original image)
LoadImage(mask image)
InpaintModelConditioning
KSampler
```

## Official ComfyUI API direction

The mobile app should use official ComfyUI APIs where possible:

```text
/upload/image
/upload/mask if available and validated
/prompt
/ws
/history/{prompt_id}
/view
```

Important:

```text
Do not invent a custom image-upload API unless official API behavior is insufficient.
```

## New architecture behavior

In the new architecture, the user prepares the workflow.

Analyzer detects whether the workflow contains image-input, mask-input, img2img, or inpaint behavior.

Smartphone app renders controls from app_profile.json.

Correct flow:

```text
User workflow contains image/mask/inpaint-related nodes
  ↓
Analyzer detects input image / mask / inpaint fields
  ↓
Analyzer writes app_profile.json fields and patch_targets
  ↓
Smartphone app shows image picker / mask editor only when profile requires it
  ↓
Smartphone app uploads image/mask through official ComfyUI API
  ↓
Smartphone app patches workflow.json using patch_targets
  ↓
Smartphone app submits /prompt
```

## Analyzer responsibilities

The Analyzer should detect these cases:

```text
1. Image input only
   - LoadImage or equivalent node
   - app shows image picker

2. img2img path
   - LoadImage -> VAEEncode or equivalent
   - app shows image picker and denoise controls if safe

3. Inpaint path
   - LoadImage original image
   - mask input
   - InpaintModelConditioning or equivalent inpaint node
   - app shows image picker + mask editor

4. Mask-only path
   - mask input without standard inpaint pattern
   - app shows mask upload/editor only when patch target is clear

5. Unknown image/mask custom nodes
   - preserve workflow
   - show warning or Expert/Debug metadata
   - do not guess unsafe patch targets
```

## app_profile field direction

Possible field examples:

```json
{
  "fields": [
    {
      "field_id": "input_image_1",
      "type": "image",
      "label": "Input image",
      "group": "Image Inputs",
      "upload_strategy": "upload_image",
      "target": {
        "node_id": "28",
        "input": "image"
      }
    },
    {
      "field_id": "mask_1",
      "type": "mask",
      "label": "Inpaint mask",
      "group": "Image Inputs",
      "upload_strategy": "upload_mask_or_image",
      "linked_image_field_id": "input_image_1",
      "target": {
        "node_id": "39",
        "input": "image"
      }
    },
    {
      "field_id": "denoise_1",
      "type": "number",
      "label": "Denoise",
      "group": "Basic Generation Settings",
      "target": {
        "node_id": "10",
        "input": "denoise"
      }
    }
  ]
}
```

## Smartphone app UI requirements

When app_profile contains image fields:

```text
- show image picker
- show selected image preview
- allow clear image
- upload image to ComfyUI before /prompt
- patch returned filename into workflow
```

When app_profile contains mask fields:

```text
- show mask editor linked to the source image
- allow paint / erase / clear
- allow brush size change
- show mask preview over image
- upload mask before /prompt
- patch returned mask filename into workflow
```

When app_profile contains inpaint mode:

```text
- show that this profile requires image + mask
- require source image before generation
- require or warn about missing mask depending on workflow requirement
- patch both source image and mask correctly
```

## Mask upload strategy

Preferred order:

```text
1. Use official /upload/mask if validated in target ComfyUI version.
2. If /upload/mask is not available, use /upload/image for mask PNG if the workflow's LoadImage/mask path accepts it.
3. If neither path is validated, show unsupported mask upload warning.
```

Do not assume `/upload/mask` exists in every ComfyUI environment until RunPod validation confirms it.

## Canvas mask behavior

Mask editor should eventually support:

```text
- brush paint
- brush erase
- clear mask
- brush size
- mask preview overlay
- correct canvas scaling from displayed image to original image size
- export mask as PNG
```

Important:

```text
The mask PNG dimensions must match what the workflow expects.
```

## Bypass / active-state interaction

If an image/mask/inpaint node or branch is bypass-OFF:

```text
- app must show it as inactive
- image picker / mask editor must not appear as active generation input
- saved selected image/mask may remain stored, but it is not active until the branch is ON
```

This follows `SUBGRAPH_AND_BYPASS_ANALYSIS.md`.

## Subgraph interaction

If image/mask fields exist inside a subgraph:

```text
- Analyzer must preserve subgraph context
- app must show the image/mask field inside the subgraph card
- nested patch_targets must be used
- field must not be editable unless nested patch target is validated
```

## Validation requirements

Validate with workflows covering:

```text
- simple image input
- img2img LoadImage -> VAEEncode
- inpaint with LoadImage + mask + InpaintModelConditioning
- mask-only workflow
- image/mask input inside subgraph
- image/mask input behind bypass OFF
- missing image input at generation time
- missing mask at generation time
```

For each, confirm:

```text
- Analyzer detects fields correctly
- app_profile includes upload strategy
- app shows correct UI
- upload succeeds
- workflow is patched only through patch_targets
- /prompt succeeds or fails with clear reason
- result output still follows output-type handling
```

## Product guardrail

```text
Full HTML i2i/mask behavior is a proven reference.
Official ComfyUI APIs should be used for actual upload/generation.
The new app must remain workflow-driven, not fixed-HTML-workflow-driven.
```
