# Analyzer Workflow and Custom Node Roadmap

## Purpose

This roadmap defines how to build the dedicated Analyzer export workflow and the dedicated custom node system.

The most important goal is:

```text
A user can prepare any ComfyUI workflow,
pass it through the Analyzer export workflow,
export an app-readable profile,
load it on the smartphone app,
and generate the intended output without changing or breaking the user's workflow.
```

This must eventually support more than images.

Target output types include:

```text
- images
- videos
- audio
- masks
- animations
- SVG/vector outputs
- text files
- metadata files
- arbitrary output files produced by ComfyUI workflows
```

## Core product rule

```text
The user prepares the generation workflow.
The project prepares the Analyzer export workflow and custom node.
```

The product must not become a fixed set of app-owned image generation workflows.

## Two-workflow structure

There are two different workflow types.

### 1. User generation workflow

```text
Prepared by the user.
Can be any valid ComfyUI workflow.
May generate images, video, audio, or other files.
Must be preserved as much as possible.
```

Examples:

```text
- FLUX image workflow
- SDXL image workflow
- img2img workflow
- inpaint / mask workflow
- ControlNet workflow
- LoRA workflow
- video generation workflow
- audio generation workflow
- SVG/icon workflow
- background removal workflow
- upscale workflow
```

### 2. Analyzer export workflow

```text
Prepared by this project.
Opened/run inside ComfyUI.
Contains the dedicated custom node.
Loads or receives the user generation workflow.
Exports workflow.json + app_profile.json + metadata as a profile zip.
```

This workflow is not an image generation workflow.

It is a conversion/export workflow.

## Dedicated custom node role

The dedicated custom node is the engine inside the Analyzer export workflow.

Initial node:

```text
Mobile Profile Exporter
```

Its job:

```text
1. Receive the user workflow.
2. Parse the workflow safely.
3. Detect editable inputs.
4. Detect output nodes and output types.
5. Detect image, mask, img2img, and inpaint inputs.
6. Detect model references.
7. Detect custom node dependencies.
8. Detect warnings and unknown nodes.
9. Produce app_profile.json.
10. Preserve workflow.json.
11. Export profile zip.
12. Expose profile list/download routes.
```

## Non-negotiable correctness goal

The system must avoid corrupting the user's workflow.

```text
Do not delete unknown nodes.
Do not simplify the graph destructively.
Do not replace the user's workflow with an app-owned workflow.
Do not assume every workflow produces images.
Do not assume every output is fetched through /view as an image.
Do not assume every workflow has prompt, seed, width, or height.
Do not assume every image workflow is text-to-image.
Do not ignore image input, mask input, img2img, or inpaint paths.
```

## Related focused design docs

Read these together with this roadmap:

```text
docs/mobile-system/I2I_MASK_INPAINT_REUSE_AND_API_PLAN.md
docs/mobile-system/SUBGRAPH_AND_BYPASS_ANALYSIS.md
docs/mobile-system/LLM_ASSISTED_WORKFLOW_ANALYSIS.md
```

## Phase 0: Concept lock

Goal:

```text
Lock the correct mental model before writing more code.
```

Deliverables:

```text
- USER_PROVIDED_WORKFLOW_CONCEPT.md
- ANALYZER_EXPORT_WORKFLOW_CONCEPT.md
- ANALYZER_WORKFLOW_AND_NODE_ROADMAP.md
- I2I_MASK_INPAINT_REUSE_AND_API_PLAN.md
```

Acceptance criteria:

```text
- Docs clearly say the user prepares the generation workflow.
- Docs clearly say the project prepares the Analyzer export workflow.
- Docs clearly separate user generation workflow from Analyzer export workflow.
- Docs explicitly state that output is not image-only.
- Docs explicitly state that image input / mask / img2img / inpaint workflows are first-class cases.
```

Status:

```text
IN PROGRESS / documentation phase
```

## Phase 1: Minimal Analyzer export workflow MVP

Goal:

```text
Create the simplest dedicated Analyzer export workflow that can load a user workflow and export a profile zip.
```

Analyzer export workflow contents:

```text
Mobile Profile Exporter node only
```

Minimum node inputs:

```text
workflow_json
profile_name
```

Minimum node output:

```text
export_path
```

MVP user operation:

```text
1. User exports/copies an API workflow JSON from ComfyUI.
2. User opens the Analyzer export workflow.
3. User pastes the workflow JSON into Mobile Profile Exporter.
4. User enters a profile name.
5. User queues the Analyzer export workflow.
6. Node exports mobile_profile_export.zip.
7. Smartphone app downloads/imports the zip.
```

MVP zip contents:

```text
workflow.json
app_profile.json
```

Optional later zip contents:

```text
metadata.json
preview.json
validation_report.json
```

Acceptance criteria:

```text
- User-provided workflow JSON is preserved as workflow.json.
- app_profile.json is generated.
- zip is created under output/mobile_profiles.
- /mobile_analyzer/profiles lists the profile.
- /mobile_analyzer/profiles/{id}/download downloads it.
- Unknown workflow nodes are preserved.
```

## Phase 2: Output type awareness

Goal:

```text
Stop treating all workflows as image workflows.
```

The Analyzer must detect or describe output candidates.

Initial output categories:

```text
image
video
audio
text
svg
mask
file
unknown
```

app_profile.json should include an output section such as:

```json
"outputs": [
  {
    "output_id": "output_1",
    "type": "image",
    "node_id": "9",
    "class_type": "SaveImage",
    "fetch_strategy": "view"
  }
]
```

Potential fetch strategies:

```text
view        - ComfyUI /view image fetch
file        - generic file download route if available
history     - parse output info from /history
manual      - show path/instructions when app cannot fetch directly
unknown     - app warns that output type is not supported yet
```

Acceptance criteria:

```text
- Image workflows still work.
- Non-image workflows are not falsely displayed as images.
- App can show a clear unsupported-output message when needed.
- app_profile.json records output type and fetch strategy.
```

## Phase 3: Editable input detection expansion

Goal:

```text
Detect useful editable fields across many workflow types without hardcoding one workflow family.
```

Input groups:

```text
Core Inputs
- prompt
- negative prompt
- input image
- input video
- input audio
- mask

Generation Settings
- seed
- steps
- cfg
- sampler
- scheduler
- denoise

Size / Duration / Output
- width
- height
- frame count
- fps
- duration
- sample rate
- batch size
- output prefix

Advanced
- LoRA strength
- ControlNet strength
- IPAdapter image
- upscale factor
- rembg toggle
- inpaint mask
- video motion settings
- audio conditioning settings

Expert / Debug
- unknown editable inputs
- raw node warnings
```

Acceptance criteria:

```text
- Image, video, and audio workflows can expose different appropriate fields.
- Image input, mask, img2img, and inpaint workflows expose correct upload fields.
- Missing fields are allowed.
- The app does not assume prompt/seed/size always exist.
- patch_targets remain the only app-editable graph locations.
```

## Phase 3A: Image input / mask / img2img / inpaint support

Goal:

```text
Carry forward full HTML i2i/mask/inpaint behavior into the workflow-driven app architecture.
```

Reference:

```text
docs/mobile-system/I2I_MASK_INPAINT_REUSE_AND_API_PLAN.md
```

Analyzer must detect:

```text
- image input fields
- LoadImage or equivalent nodes
- img2img paths such as LoadImage -> VAEEncode
- mask input fields
- inpaint paths such as LoadImage + mask + InpaintModelConditioning
- denoise fields related to img2img/inpaint
- image/mask fields inside subgraphs
- image/mask fields behind bypass-OFF branches
```

Smartphone app must support:

```text
- image picker
- selected image preview
- /upload/image before /prompt
- mask editor when profile requires mask
- paint / erase / clear
- brush size
- mask upload before /prompt
- patching returned filenames only through patch_targets
```

Acceptance criteria:

```text
- Full HTML behavior is used as a reference, not copied as fixed workflow construction.
- Official ComfyUI upload APIs are used where possible.
- App does not show image/mask inputs as active when their branch is bypass-OFF.
- Inpaint generation can patch both original image and mask when workflow supports it.
```

## Phase 4: Analyzer export workflow input improvements

Goal:

```text
Make it easier for the user to feed a workflow into the Analyzer export workflow.
```

Input method roadmap:

```text
Step 1: Paste API workflow JSON text.
Step 2: Load workflow JSON from a file path.
Step 3: Select from a known ComfyUI workflows folder.
Step 4: Upload workflow JSON through Analyzer route.
Step 5: Later, if technically safe, read the currently open ComfyUI workflow.
```

Acceptance criteria:

```text
- Paste JSON remains available as fallback.
- File/path selection does not break RunPod usage.
- Invalid JSON produces a clear error.
- UI/export workflow remains simple.
```

## Phase 5: Dependency and compatibility reporting

Goal:

```text
Tell the user what is needed before they try to run a workflow from the app.
```

Analyzer should report:

```text
- model references
- LoRA references
- VAE references
- ControlNet model references
- custom node class types
- missing/unknown node types
- image/mask/inpaint support level
- output type support level
- app compatibility warnings
```

app_profile.json sections:

```text
missing_models
missing_nodes
warnings
compatibility
outputs
```

Acceptance criteria:

```text
- App can show warnings before generation.
- Check environment can compare current ComfyUI against app_profile requirements.
- No auto-download or auto-install happens.
```

## Phase 6: Smartphone app multi-output support

Goal:

```text
The smartphone app can display or handle different output types safely.
```

UI behavior by output type:

```text
image
- show image preview
- allow large preview
- add to session history

video
- show video file entry first
- later add video player if safe
- keep download/open behavior separate from image /view

audio
- show audio file entry first
- later add audio player if safe

text/json/metadata
- show readable text or downloadable file entry

unknown/file
- show output filename/path and unsupported preview warning
```

Acceptance criteria:

```text
- Image behavior does not regress.
- Non-image outputs do not crash the app.
- App does not try to render audio/video as images.
- Session history can store output type metadata.
```

## Phase 7: Validation matrix

Goal:

```text
Prove the system works with many workflow families.
```

Required validation set:

```text
1. Simple image workflow
2. Image workflow with LoRA
3. Image workflow with ControlNet or image input
4. img2img workflow
5. inpaint / mask workflow
6. Upscale workflow
7. Background removal workflow
8. Video workflow
9. Audio workflow
10. Workflow with custom nodes
11. Workflow with missing model
12. Workflow with unsupported output type
```

For each workflow validate:

```text
- Analyzer export workflow accepts it.
- workflow.json is preserved.
- app_profile.json is created.
- app displays correct controls.
- app warnings are understandable.
- generation either succeeds or fails safely with a clear reason.
- output handling matches output type.
```

## Phase 8: Future polish

Only after validation:

```text
- Better Analyzer export workflow UI.
- Better visual design based on legacy HTML review.
- Profile preview before export.
- Output preview metadata.
- More advanced field grouping.
- Preset management.
- Local profile library improvements.
- Optional video/audio playback support.
```

## Things not to do

```text
- Do not make users use only project-provided generation workflows.
- Do not assume output is always image.
- Do not assume image workflows are always text-to-image.
- Do not auto-download models.
- Do not auto-install custom nodes.
- Do not mutate unknown nodes.
- Do not turn the smartphone app into a full workflow editor.
- Do not add serverless before Pod validation.
- Do not make UI beauty more important than workflow correctness.
```

## Primary success definition

The project is successful when:

```text
A user can bring their own ComfyUI workflow,
run it through the Analyzer export workflow,
load the generated profile on a smartphone,
edit only safe exposed controls,
upload required images/masks when the workflow needs them,
submit generation,
and receive the correct output type without the workflow being corrupted.
```
