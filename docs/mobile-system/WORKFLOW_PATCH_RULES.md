# Workflow Patch Rules v1.0

## Purpose

The smartphone app must safely apply user changes to `workflow.json` before sending it to ComfyUI.

The app must not freely edit the whole workflow. It may only modify fields listed in `app_profile.json.patch_targets`.

## Basic rule

```text
UI field value
  ↓
patch_target_id
  ↓
node_id + input
  ↓
workflow[node_id].inputs[input]
```

## patch_target shape

Required fields:

- `patch_target_id`
- `field_id`
- `node_id`
- `input`
- `value_type`

Example:

```json
{
  "patch_target_id": "patch_steps",
  "field_id": "steps",
  "node_id": "10",
  "input": "steps",
  "value_type": "INT"
}
```

This points to:

```text
workflow["10"].inputs.steps
```

## value_type

Allowed values:

- `INT`
- `FLOAT`
- `STRING`
- `BOOLEAN`
- `COMBO`
- `IMAGE`
- `MODEL_NAME`
- `FILE_NAME`

## MVP patchable fields

MVP may patch:

- prompt
- negative
- seed
- steps
- cfg
- sampler_name
- scheduler
- denoise
- width
- height
- batch_size

## Do not patch in MVP

MVP must not patch:

- node addition
- node deletion
- node connection changes
- output slot changes
- input slot changes
- graph structure changes
- unknown node connections

## Connection inputs

ComfyUI connection inputs usually look like this:

```json
"positive": ["6", 0]
```

MVP treats connection inputs as read-only.

## Value inputs

Normal values may be patched:

```json
"steps": 20
```

```json
"cfg": 7
```

```json
"text": "masterpiece, 1girl"
```

## Image input

Image patching is allowed only for `LoadImage.image` in MVP.

Flow:

```text
1. Smartphone app uploads image to ComfyUI
2. ComfyUI returns uploaded filename
3. App patches workflow[node_id].inputs.image
4. App sends patched workflow to /prompt
```

## Validation

Before sending to `/prompt`, the app must validate:

- node_id exists
- input exists
- value type matches
- select value is inside options
- number is inside min/max
- image upload succeeded
- workflow JSON is still valid

## Failure behavior

If patch validation fails, the app must not submit the workflow.

The app should show a clear error and keep the original workflow unchanged.

## History

For every generation, save a patched workflow snapshot.

Reason:

- regenerate
- seed-fixed generation
- troubleshooting
- history review

## Principles

- Do not break the workflow.
- Do not edit anything outside `patch_targets`.
- Do not change node connections in MVP.
- Validate before submit.
- Save the patched workflow snapshot.
