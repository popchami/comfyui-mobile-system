# Analyzer Export Workflow Node Composition

## Purpose

This file records how to think about the node composition for the dedicated Analyzer export workflow.

The dedicated workflow is not a generation workflow.
It is the workflow that loads a user-provided workflow, analyzes it, and packages it for the smartphone app.

## Important correction

Do not decide too early that the Analyzer export workflow must use exactly three nodes.

The earlier three-node idea is useful as a simple mental model, but it is not a fixed design.

```text
If more nodes are needed for correctness, clarity, validation, preview, output-type handling, or debugging, use more nodes.
```

The priority is not node count.

The priority is:

```text
A user-provided workflow is loaded, analyzed, exported, imported by the smartphone app, and generated without being corrupted.
```

## Flexible role model

The Analyzer export workflow needs to cover these responsibilities.

They may be implemented as three nodes, one node, or many nodes.

```text
1. Workflow input/load
2. Workflow validation
3. Workflow normalization/preservation
4. Workflow analysis
5. Editable input detection
6. Output type detection
7. Dependency detection
8. Compatibility/warning report
9. app_profile.json generation
10. profile metadata generation
11. ZIP packaging
12. Profile registration for download routes
13. Debug/preview output
```

## Simple three-role model

The simple version is still useful as a starting explanation:

```text
[Workflow Load Role]
        ↓
[Analyzer Role]
        ↓
[ZIP Export Role]
```

But this is only a role model.

It should not block adding more nodes.

## Possible node designs

### Option A: One-node MVP

```text
[Mobile Profile Exporter]
```

The single node internally handles:

```text
load_workflow()
validate_workflow()
analyze_workflow()
build_app_profile()
export_profile_zip()
register_profile()
```

Pros:

```text
- Simple to build first.
- Simple to test in RunPod.
- Fewer ComfyUI graph connection issues.
```

Cons:

```text
- Harder to debug each stage visually.
- Large node may become too complex.
- Harder to reuse parts later.
```

### Option B: Three-node workflow

```text
[Workflow Load Node]
        ↓
[Dedicated Custom Analyzer Node]
        ↓
[Smartphone App ZIP Export Node]
```

Pros:

```text
- Easy to understand.
- Responsibilities are separated.
- Debugging is clearer than one node.
```

Cons:

```text
- May still be too coarse.
- Analyzer node may remain overloaded.
- Output type handling may need separate nodes later.
```

### Option C: Expanded multi-node workflow

```text
[Workflow Input Node]
        ↓
[Workflow JSON Validator]
        ↓
[Workflow Preserver / Normalizer]
        ↓
[Workflow Analyzer]
        ↓
[Editable Input Detector]
        ↓
[Output Type Detector]
        ↓
[Dependency Detector]
        ↓
[Compatibility Report Builder]
        ↓
[App Profile Builder]
        ↓
[Smartphone ZIP Exporter]
        ↓
[Profile Registry / Download Publisher]
```

Pros:

```text
- Best separation of responsibilities.
- Easier to test each stage.
- Better for image/video/audio/file support.
- Easier to add debug previews.
```

Cons:

```text
- More nodes to maintain.
- More complicated ComfyUI export workflow.
- Not necessary until the simpler version proves limits.
```

## Current design stance

```text
Do not lock the node count yet.
Start from the smallest version that can be validated.
Keep code structured so roles can be split into more nodes later.
```

## Role details

### 1. Workflow input/load

Role:

```text
Receive or load the user's ComfyUI workflow.
```

Possible input methods:

```text
- Paste API workflow JSON text.
- Load workflow JSON from a file path.
- Select a workflow file from a known folder.
- Upload workflow JSON through a custom route.
- Later, if technically safe, read the currently open ComfyUI workflow.
```

MVP method:

```text
Paste API workflow JSON text.
```

Important rules:

```text
- Do not modify the workflow.
- Do not assume it is image-only.
- Validate JSON enough to avoid passing broken data forward.
- Preserve the original workflow content for export.
```

### 2. Workflow validation

Role:

```text
Check that the workflow is parseable and usable enough to analyze.
```

Checks:

```text
- valid JSON
- API workflow shape
- node map exists
- node ids are readable
- class_type fields exist where expected
- links/inputs can be traversed or safely ignored
```

### 3. Workflow preservation / normalization

Role:

```text
Keep the original workflow safe while allowing app_profile generation.
```

Rules:

```text
- Preserve unknown nodes.
- Preserve unknown inputs.
- Preserve custom node references.
- Do not destructively simplify.
- If normalization is needed, keep the preserved original separately.
```

### 4. Workflow analysis

Role:

```text
Understand the workflow enough to expose safe smartphone controls.
```

Inspect:

```text
- nodes
- class_type
- inputs
- links / references
- model names
- custom node dependencies
- likely editable values
- output nodes
- output types
- unsupported or unknown areas
```

### 5. Editable input detection

Role:

```text
Find fields that can safely become smartphone controls.
```

Examples:

```text
- prompt
- negative prompt
- seed
- steps
- cfg
- sampler
- scheduler
- width
- height
- input image
- input video
- input audio
- mask
- frame count
- fps
- duration
- output prefix
```

Important:

```text
Do not assume every workflow has these fields.
```

### 6. Output type detection

Role:

```text
Identify what the workflow produces.
```

Output categories:

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

Important:

```text
Do not treat every output as an image.
```

### 7. Dependency detection

Role:

```text
Record what the workflow needs from the ComfyUI environment.
```

Examples:

```text
- checkpoints
- diffusion models
- LoRAs
- VAEs
- CLIP models
- ControlNet models
- upscale models
- custom node class types
```

### 8. Compatibility / warning report

Role:

```text
Explain what the app can or cannot safely support.
```

Examples:

```text
- unsupported output type
- missing model reference
- missing custom node type
- no obvious editable controls
- no recognized output node
- app can import but cannot preview output yet
```

### 9. app_profile.json generation

Role:

```text
Build the contract used by the smartphone app.
```

Must include or support:

```text
profile_id
profile_name
schema_version
ui.simple
patch_targets
outputs
missing_models
missing_nodes
warnings
compatibility
```

### 10. ZIP packaging

Role:

```text
Package the preserved workflow and app metadata into a smartphone-readable profile zip.
```

Minimum zip contents:

```text
workflow.json
app_profile.json
```

Future zip contents:

```text
metadata.json
analysis_report.json
compatibility_report.json
preview.json
```

### 11. Profile registration / download publishing

Role:

```text
Make exported profiles available to the smartphone app.
```

Routes:

```text
/mobile_analyzer/profiles
/mobile_analyzer/profiles/{id}/download
```

## Implementation recommendation

Start with whichever node count is easiest to validate, but code should be modular.

Internal functions should be separated even if the UI exposes one node first:

```text
load_workflow()
validate_workflow()
preserve_workflow()
analyze_workflow()
detect_editable_inputs()
detect_outputs()
detect_dependencies()
build_compatibility_report()
build_app_profile()
export_profile_zip()
register_profile()
```

This prevents the first implementation from becoming a dead end.

## Acceptance criteria

The dedicated Analyzer export workflow is successful when:

```text
- A user-provided workflow can be loaded.
- The workflow is preserved.
- app_profile.json is produced.
- patch_targets are produced.
- output types are recorded or safely marked unknown.
- missing models/custom nodes are recorded.
- compatibility warnings are recorded.
- a profile zip is created.
- the smartphone app can import the zip.
- the smartphone app can submit generation without corrupting the workflow.
```

## Product guardrail

```text
The user should prepare the generation workflow only.
The dedicated Analyzer export workflow should handle loading, analysis, reporting, and zip packaging.
Use as many nodes as needed to make that reliable.
Do not optimize for fewer nodes at the cost of correctness.
```
