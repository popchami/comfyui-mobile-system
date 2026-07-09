# app_profile.json v2 Draft

## Purpose

This document defines the long-term `app_profile.json` direction for workflows that may include:

```text
image
video
audio
text
json
svg
3d
file
zip
unknown outputs
subgraphs
bypass / mute / switch states
wildcards
LoRA
ControlNet
IPAdapter
LLM / Ollama / Gemma
Partner / external API nodes
unknown custom nodes
```

This is a draft for the next large architecture step.

It must not break the current MVP profile schema.

## Core principle

```text
workflow.json = preserved execution body
app_profile.json = smartphone operation map
patch_targets = exact safe edit targets
```

The app must not recreate the workflow.

The app must not become a full ComfyUI graph editor.

The app should render shared controls from profile fields, patch only safe targets, submit the preserved workflow to ComfyUI, and display results by output type.

## Compatibility with v1

v2 should remain compatible with the existing v1 ideas:

```text
schema_version
profile_id
profile_name
workflow_id
compatibility
ui
patch_targets
nodes
warnings
missing_nodes
missing_models
```

v2 expands the structure instead of replacing the concept.

## Top-level structure

Recommended v2 top-level fields:

```json
{
  "schema_version": "2.0-draft",
  "profile_id": "...",
  "profile_name": "...",
  "profile_version": "...",
  "workflow_id": "...",
  "workflow_format": "api",
  "created_at": "...",
  "updated_at": "...",
  "source": {},
  "compatibility": {},
  "capabilities": {},
  "ui": {},
  "fields": [],
  "patch_targets": {},
  "structure": {},
  "runtime_requirements": {},
  "outputs": [],
  "warnings": [],
  "debug": {}
}
```

## compatibility

The Analyzer must not treat all workflows as equally safe.

```json
{
  "compatibility": {
    "level": "supported",
    "safe_to_generate": true,
    "safe_to_edit": true,
    "safe_to_patch": true,
    "reasons": [],
    "unsupported_reasons": [],
    "partial_reasons": []
  }
}
```

Allowed levels:

```text
supported
partial
unsupported
invalid
```

Rules:

```text
supported   -> safe controls and known output handling
partial     -> some safe controls, warnings, risky controls disabled
unsupported -> preserve and explain, do not unsafe-generate
invalid     -> cannot parse or cannot preserve workflow safely
```

## capabilities

The profile should describe what types of operation points were found.

```json
{
  "capabilities": {
    "input_types": ["text", "number", "select", "image", "mask"],
    "output_types": ["image"],
    "has_subgraphs": true,
    "has_bypass_states": true,
    "has_switches": false,
    "has_wildcards": true,
    "has_llm_nodes": false,
    "has_external_api_nodes": false,
    "has_unknown_custom_nodes": true,
    "has_expert_editable_fields": true
  }
}
```

The app should use this to decide warning cards, visible sections, and validation state.

## fields

`fields` is the main list of app-renderable controls.

Each field should describe one operation point.

```json
{
  "field_id": "main_prompt",
  "label": "Prompt",
  "description": "Main positive prompt",
  "control_type": "textarea",
  "value_type": "string",
  "section": "core",
  "visibility": "visible",
  "state": "active",
  "default": "a cinematic portrait",
  "current": "a cinematic portrait",
  "patch_target_ids": ["pt_main_prompt"],
  "source": {
    "node_id": "6",
    "class_type": "CLIPTextEncode",
    "input": "text",
    "role": "positive_prompt",
    "known": true
  },
  "safety": {
    "editable": true,
    "semantic_confidence": "high",
    "requires_warning": false,
    "warnings": []
  }
}
```

## field sections

Recommended sections:

```text
core
basic
advanced
subgraph
branch
wildcard
model
media
output
expert_unknown
debug
hidden
```

Rules:

```text
core             -> prompt, main media input, generate action, main result
basic            -> seed, steps, CFG, denoise, sampler, scheduler, size
advanced         -> LoRA, ControlNet, IPAdapter, video/audio settings
subgraph         -> exposed or scoped subgraph controls
branch           -> safe bypass / switch / mode controls
wildcard         -> wildcard and template controls
model            -> checkpoint, LoRA, VAE, CLIP, video/audio/LLM models
media            -> image / mask / audio / video / file inputs
output           -> output format and output target selection
expert_unknown   -> unknown but simple typed editable controls
debug            -> raw node and analysis info
hidden           -> preserved but not app-editable
```

## control_type

Controls should be shared across output types.

Allowed draft values:

```text
text
textarea
integer
float
slider
seed
switch
select
multi_select
image_upload
mask_editor
audio_upload
video_upload
file_upload
folder_picker
model_picker
strength_slider
range
branch_toggle
subgraph_group
wildcard_picker
output_target_picker
readonly
warning
unknown
```

These are app components, not ComfyUI node names.

## value_type

Allowed draft values:

```text
string
integer
float
boolean
combo
image
mask
audio
video
file
json
unknown
```

`value_type` should be close to the ComfyUI runtime node input type or app-normalized equivalent.

## field state

A field can exist but not be active.

```text
active
inactive_by_bypass
inactive_by_switch
disabled_missing_requirement
disabled_unsafe_patch
disabled_unknown_behavior
readonly
hidden
```

Rules:

```text
Do not show inactive branch fields as normal active controls.
If branch state changes, dependent fields should update state.
```

## patch_targets

Patch targets must remain exact.

```json
{
  "patch_targets": {
    "pt_main_prompt": {
      "target_id": "pt_main_prompt",
      "scope": "workflow",
      "node_id": "6",
      "input": "text",
      "path": ["6", "inputs", "text"],
      "value_type": "string",
      "allowed_control_types": ["textarea"],
      "safe": true,
      "reason": "Known CLIPTextEncode text input",
      "validator": {
        "required": true,
        "allow_connection_inputs": false
      }
    }
  }
}
```

### subgraph patch target

```json
{
  "target_id": "pt_subgraph_prompt",
  "scope": "subgraph",
  "subgraph_id": "sg_12",
  "node_id": "45",
  "input": "text",
  "path": ["subgraphs", "sg_12", "nodes", "45", "inputs", "text"],
  "value_type": "string",
  "safe": true
}
```

### branch / bypass patch target

```json
{
  "target_id": "pt_controlnet_branch",
  "scope": "workflow_state",
  "state_type": "bypass",
  "node_id": "32",
  "path": ["32", "state", "bypassed"],
  "value_type": "boolean",
  "safe": true
}
```

Branch/bypass paths may differ by workflow format. If not safely addressable, do not expose the toggle.

## structure

The profile should describe workflow structure without requiring the app to become a graph editor.

```json
{
  "structure": {
    "nodes": [],
    "edges": [],
    "subgraphs": [],
    "branches": [],
    "switches": [],
    "bypass_states": [],
    "active_paths": [],
    "set_get_links": [],
    "output_nodes": []
  }
}
```

## subgraphs

Subgraphs should be first-class structure.

```json
{
  "subgraphs": [
    {
      "subgraph_id": "sg_12",
      "label": "Character Detailer",
      "state": "active",
      "exposed_field_ids": ["sg_prompt", "sg_strength"],
      "internal_node_count": 8,
      "nested_subgraph_ids": [],
      "warnings": []
    }
  ]
}
```

Rules:

```text
Subgraph exposed inputs should be preferred over raw internals.
Internal controls can be exposed only when safely scoped and patchable.
Unknown internals should be preserved and warned.
```

## branches / switches / bypass_states

Branch state must be separated from normal boolean node inputs.

```json
{
  "branches": [
    {
      "branch_id": "controlnet_branch",
      "label": "ControlNet",
      "state": "active",
      "control_field_id": "controlnet_branch_toggle",
      "dependent_field_ids": ["controlnet_image", "controlnet_strength"],
      "warnings": []
    }
  ]
}
```

Rules:

```text
Node existence is not the same as active execution.
Inactive branch fields should be disabled, hidden, or shown inactive.
```

## unknown editable fields

Unknown custom nodes can still produce safe app controls.

```json
{
  "field_id": "unknown_style_text_1",
  "label": "SomePromptMixer / style_text",
  "control_type": "textarea",
  "value_type": "string",
  "section": "expert_unknown",
  "patch_target_ids": ["pt_unknown_style_text_1"],
  "source": {
    "node_id": "91",
    "class_type": "SomePromptMixer",
    "input": "style_text",
    "known": false
  },
  "safety": {
    "editable": true,
    "semantic_confidence": "unknown",
    "requires_warning": true,
    "warnings": ["Unknown custom node field. Meaning is not classified."]
  }
}
```

Rules:

```text
Unknown + simple typed widget + exact patch target -> Expert editable with warning.
Unknown + complex connection / unclear behavior -> preserve only, no edit.
Unknown + external API / credentials / file/network risk -> warning and disabled unless explicitly supported.
```

## runtime_requirements

The profile should describe what the ComfyUI environment must have.

```json
{
  "runtime_requirements": {
    "models": [],
    "loras": [],
    "vae": [],
    "clip": [],
    "controlnet": [],
    "upscale_models": [],
    "custom_nodes": [],
    "python_packages": [],
    "external_services": [],
    "credentials": []
  }
}
```

Rules:

```text
Do not auto-install models.
Do not auto-install custom nodes.
Show missing requirements clearly.
```

## external API / Partner node warnings

External or hosted nodes need explicit warnings.

```json
{
  "warnings": [
    {
      "warning_id": "external_api_1",
      "severity": "high",
      "type": "external_api",
      "message": "This workflow may send inputs to an external provider.",
      "related_node_ids": ["120"],
      "requires_user_attention": true
    }
  ]
}
```

Potential warning types:

```text
external_api
privacy
cost
credential_required
missing_model
missing_custom_node
unknown_output
unsafe_patch
unsupported_subgraph
inactive_branch
```

## outputs

The app must not assume image only.

```json
{
  "outputs": [
    {
      "output_id": "main_image",
      "output_type": "image",
      "node_id": "9",
      "class_type": "SaveImage",
      "viewer": "image_viewer",
      "safe_to_display": true,
      "safe_to_save": true,
      "warnings": []
    }
  ]
}
```

Allowed draft output types:

```text
image
video
audio
text
json
svg
3d
mask
file
zip
unknown
```

## UI rendering rule

The app should render fields from profile data.

```text
profile.fields[]
  -> FieldRenderer
  -> shared control component
  -> patch target
  -> workflow JSON patch
```

The app should not hardcode one UI per known node.

## MVP bridge rule

The current MVP can continue using:

```text
ui.simple
ui.advanced
ui.expert
patch_targets
```

But new work should prepare a migration path to:

```text
fields[]
structure
capabilities
outputs
runtime_requirements
warnings
```

## Longest implementation areas

The slowest work will be:

```text
1. v2 profile schema support
2. Analyzer capability-based extraction
3. shared field renderer in app
4. branch/subgraph state mapping
5. output-type viewer abstraction
6. unknown custom node expert controls
7. warning and compatibility logic
```

## Final rule

```text
The app should be generic by control capability, not specific by output type.
```

This is the foundation for supporting image first while keeping a path for video, audio, text, 3D, LLM, wildcard, subgraph, bypass, external API, and unknown custom node workflows.
