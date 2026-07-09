# app_profile.json v1.0

## Purpose

`app_profile.json` is the contract between ComfyUI-Mobile-Analyzer and the smartphone app.

The Analyzer writes this file. The smartphone app reads it to build the UI, validate the profile, patch safe values into `workflow.json`, and submit the workflow to ComfyUI.

## Top-level structure

Required fields:

- `schema_version`
- `profile_id`
- `profile_name`
- `profile_version`
- `workflow_id`
- `workflow_format`
- `created_at`
- `updated_at`
- `source`
- `compatibility`
- `ui`
- `patch_targets`
- `nodes`
- `missing_nodes`
- `missing_models`
- `attention_nodes`
- `warnings`

## workflow_format

Allowed values:

- `api`
- `ui`
- `converted_api`
- `unknown`

`converted_api` means the Analyzer converted a ComfyUI UI workflow into a workflow that can be sent to `/prompt`.

## compatibility.status

Allowed values:

- `ready`
- `partial`
- `missing_requirements`
- `needs_attention`
- `invalid`

Use `needs_attention` for external API nodes, unusual file access nodes, or special nodes that may require user review. Do not use a hard-blocking status name for normal imported workflow nodes.

## ui groups

The `ui` field contains three groups:

- `simple`
- `advanced`
- `expert`

Hidden nodes are not placed in `ui`, but they remain listed in `nodes` and remain inside `workflow.json`.

## ui field shape

A UI field should contain:

- `field_id`
- `label`
- `type`
- `section`
- `ui_visibility`
- `node_id`
- `input`
- `default`
- optional `min`
- optional `max`
- optional `step`
- optional `options`
- optional `patch_target_id`
- optional `node_color`
- optional `node_bgcolor`

`node_color` and `node_bgcolor` are copied from the source workflow node metadata when available. They let the app tint the field or node card to match the original ComfyUI workflow.

## UI types for MVP

- `text`
- `textarea`
- `number`
- `slider`
- `switch`
- `select`
- `image`
- `readonly`

## nodes shape

Each node entry should include:

- `node_id`
- `class_type`
- `category`
- `known`
- `exists_in_comfyui`
- `ui_visibility`
- `editable`
- `role`
- optional `color`
- optional `bgcolor`

`color` and `bgcolor` should preserve ComfyUI node colors when the source workflow contains them.

Example:

```json
{
  "node_id": "10",
  "class_type": "KSampler",
  "category": "sampler",
  "known": true,
  "exists_in_comfyui": true,
  "ui_visibility": "simple",
  "editable": true,
  "role": "main_sampler",
  "color": "#223344",
  "bgcolor": "#334455"
}
```

## node color handling

The Analyzer should copy node color metadata when it can access a UI-format workflow.

Rules:

- Preserve original ComfyUI node color values when available.
- Do not invent exact colors when the source does not include them.
- If color is missing, app should use a fallback color by node category.
- API-format workflows may not contain UI node color data. In that case `color` and `bgcolor` may be omitted.
- App-side node cards may use `bgcolor` as the card tint and `color` as a border or accent.
- Color metadata is visual only. It must not affect workflow patching.

Fallback category examples:

```text
sampler -> orange accent
prompt -> blue/purple accent
image -> green accent
model -> gray accent
unknown -> neutral accent
```

## ui_visibility

Allowed values:

- `simple`
- `advanced`
- `expert`
- `hidden`

## MVP simple fields

The MVP should expose only these fields when they exist in the workflow:

- prompt
- negative
- seed
- steps
- cfg
- sampler
- scheduler
- denoise
- width
- height
- batch

## MVP known nodes

Initial known nodes:

- KSampler
- CLIPTextEncode
- LoadImage
- SaveImage
- PreviewImage
- EmptyLatentImage
- CheckpointLoaderSimple
- UNETLoader
- DualCLIPLoader
- VAELoader
- VAEEncode
- VAEDecode
- LoraLoader

## Rules

- Do not remove workflow nodes.
- Do not change node connections in MVP.
- Only fields listed in `patch_targets` may be patched.
- Connection inputs are read-only by default.
- Hidden nodes remain in `workflow.json`.
- Unknown nodes remain in `workflow.json`.
- Missing nodes and models are not installed by the smartphone app in MVP.
- If requirements are missing, the user should fix the ComfyUI environment and run the Analyzer again.
