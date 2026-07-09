# App Profile Evolution Plan

## Purpose

This file prepares how `app_profile.json` can evolve for future features without breaking the current MVP contract.

This is a planning document only. Do not implement schema changes before RunPod GPU + Android validation passes.

## Current contract that must not break

Current MVP depends on:

```text
app_profile.json
workflow.json
patch_targets
ui.simple
```

Rules:

```text
- Existing profile fields must remain backwards compatible.
- The Android app must patch only fields listed in patch_targets.
- Unknown workflow nodes must be preserved.
- The saved original workflow must not be mutated directly.
- Generation should patch a copy of the workflow.
```

## Versioning rule

Use additive schema changes first.

```text
Good:
- add optional fields
- add metadata blocks
- add warnings
- add compatibility sections

Avoid:
- renaming existing fields
- changing patch target paths
- changing meaning of ui.simple
- removing fields without migration
```

Suggested version behavior:

```text
profile_version: app-facing profile format version
schema_version: structural schema identifier
analyzer_version: Analyzer output version
```

## Proposed future top-level sections

These sections may be added later as optional fields.

```json
{
  "runtime_requirements": {},
  "model_checks": {},
  "node_metadata": {},
  "input_metadata": {},
  "warnings": [],
  "storage_hints": {},
  "preview": {},
  "history_policy": {},
  "compatibility": {}
}
```

## 1. runtime_requirements

Intent:

```text
Record what the workflow needs before generation can work.
```

Possible shape:

```json
{
  "runtime_requirements": {
    "comfyui_api": ["/prompt", "/ws", "/history/{prompt_id}", "/view"],
    "optional_api": ["/object_info", "/models"],
    "requires_image_upload": true,
    "requires_mask_upload": false,
    "requires_existing_models": true
  }
}
```

Use:

```text
The app can show a preflight checklist before generation.
```

Do not:

```text
Do not use this to auto-install anything.
```

## 2. model_checks

Intent:

```text
Record detected model references and whether they exist in the running ComfyUI environment.
```

Possible shape:

```json
{
  "model_checks": {
    "status": "unverified",
    "items": [
      {
        "type": "checkpoint",
        "node_id": "4",
        "field": "ckpt_name",
        "name": "example.safetensors",
        "status": "missing",
        "folder": "checkpoints"
      }
    ]
  }
}
```

Allowed statuses:

```text
unknown
unverified
exists
missing
folder_unknown
```

User-facing behavior:

```text
Show missing model warnings before generation.
```

Do not:

```text
Do not auto-download missing models.
```

## 3. node_metadata

Intent:

```text
Record useful metadata about workflow nodes without exposing all node internals to the app.
```

Possible shape:

```json
{
  "node_metadata": {
    "12": {
      "class_type": "KSampler",
      "title": "Sampler",
      "role": "sampler",
      "visibility": "advanced",
      "source": "api_workflow"
    }
  }
}
```

Possible roles:

```text
prompt
negative_prompt
sampler
latent
image_input
model_loader
lora_loader
vae_loader
controlnet
ipadapter
upscale
face_detailer
save_image
unknown
```

## 4. input_metadata

Intent:

```text
Use /object_info to describe input fields accurately.
```

Possible shape:

```json
{
  "input_metadata": {
    "12.steps": {
      "node_id": "12",
      "input_name": "steps",
      "type": "INT",
      "required": true,
      "min": 1,
      "max": 150,
      "default": 20,
      "source": "/object_info"
    },
    "12.sampler_name": {
      "node_id": "12",
      "input_name": "sampler_name",
      "type": "COMBO",
      "choices": ["euler", "dpmpp_2m"],
      "source": "/object_info"
    }
  }
}
```

Use:

```text
The app can render safer controls without hardcoded assumptions.
```

## 5. warnings

Intent:

```text
Give user-readable problems and next actions.
```

Possible shape:

```json
{
  "warnings": [
    {
      "code": "model_missing",
      "severity": "blocking",
      "message": "Required checkpoint is missing.",
      "node_id": "4",
      "field": "ckpt_name",
      "technical_detail": "example.safetensors not found in /models/checkpoints"
    }
  ]
}
```

Severity levels:

```text
info
warning
needs_attention
blocking
```

Do not:

```text
Do not use dangerous unless a real safety/security issue is identified.
The project convention prefers needs_attention for normal workflow warnings.
```

## 6. storage_hints

Intent:

```text
Help the app decide whether shared_preferences is enough or file storage is needed.
```

Possible shape:

```json
{
  "storage_hints": {
    "estimated_workflow_bytes": 125000,
    "large_profile": true,
    "recommended_storage": "file",
    "contains_image_inputs": true
  }
}
```

Use:

```text
Move large profiles to app-local files when needed.
```

## 7. preview

Intent:

```text
Allow saved profiles to show a preview image later.
```

Possible shape:

```json
{
  "preview": {
    "type": "generated_image",
    "filename": "preview.png",
    "source": "latest_successful_generation"
  }
}
```

Rules:

```text
- Preview is optional.
- Do not force cloud sync.
- Be careful with NSFW image storage.
```

## 8. history_policy

Intent:

```text
Control whether generation history is saved locally.
```

Possible shape:

```json
{
  "history_policy": {
    "save_generation_history": false,
    "max_local_items": 20,
    "cloud_sync": false
  }
}
```

Default:

```text
Do not automatically sync generated images to cloud storage.
```

## 9. compatibility

Intent:

```text
Record Analyzer confidence and compatibility notes.
```

Possible shape:

```json
{
  "compatibility": {
    "status": "partial",
    "confidence": "medium",
    "requires_review": true,
    "unsupported_features": ["subgraph", "bypass"],
    "notes": ["Model existence not verified yet"]
  }
}
```

Allowed status:

```text
supported
partial
needs_attention
unsupported
```

## Migration rule

When schema changes later:

```text
1. Keep old profiles readable.
2. Add migration functions in the app if necessary.
3. Never silently drop patch_targets.
4. If a profile is too old, show a clear message and ask for re-export.
```

## First schema additions after validation

After RunPod + Android validation passes, consider this order:

```text
1. warnings
2. model_checks
3. input_metadata from /object_info
4. storage_hints
5. compatibility details
6. preview/history later
```

## Do not implement before validation

```text
- No schema-breaking changes.
- No automatic downloads.
- No automatic installs.
- No full workflow editor metadata.
```
