# UI Visibility Rules v1.0

## Purpose

Convert complex ComfyUI workflow nodes into a smartphone-friendly UI.

The smartphone app must not display every node by default. It should display only useful controls and keep pass-through/internal nodes hidden from normal users.

## UI levels

- `simple`
- `advanced`
- `expert`
- `hidden`

## simple

Normal generation screen.

Typical fields:

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
- input image

## advanced

Optional detailed settings.

Typical categories:

- LoRA
- ControlNet
- IPAdapter
- FaceID
- FaceDetailer
- Upscale
- RemBG
- Inpaint
- Mask
- Wildcard
- Ollama / LLM

MVP may create the sections but leave most advanced implementations for later.

## expert

For review and advanced troubleshooting.

Typical content:

- unknown nodes
- custom nodes
- pass-through nodes
- raw inputs
- analyzed node list
- debug information

## hidden

Not shown in the UI, but kept inside `workflow.json`.

Typical content:

- Reroute
- Note
- UI position data
- comments
- group metadata
- pure internal pass-through nodes

## UI field shape

Example:

```json
{
  "field_id": "steps",
  "label": "Steps",
  "type": "number",
  "section": "basic_sampling",
  "ui_visibility": "simple",
  "node_id": "10",
  "input": "steps",
  "default": 20,
  "min": 1,
  "max": 100,
  "step": 1,
  "patch_target_id": "patch_steps"
}
```

## sections

### simple sections

- `prompt`
- `image_input`
- `basic_sampling`
- `size`
- `output`

### advanced sections

- `lora`
- `controlnet`
- `ipadapter`
- `faceid`
- `facedetailer`
- `upscale`
- `rembg`
- `inpaint`
- `wildcard`
- `llm`

### expert sections

- `unknown_nodes`
- `pass_through_nodes`
- `all_nodes`
- `raw_inputs`
- `debug`

## UI types

MVP supports:

- `text`
- `textarea`
- `number`
- `slider`
- `switch`
- `select`
- `image`
- `readonly`

## Display rules

Show fields when:

- the user can meaningfully change the value
- the field is listed in `patch_targets`
- it is a number, text, select, switch, or image input
- it strongly affects the generation result
- it belongs to a known node with dedicated UI support

Hide or move to expert when:

- input is connection-only
- node only passes data through
- node only converts data
- node is UI metadata
- node is a comment or note
- node is required for the workflow but not useful for user control

## Unknown nodes

Unknown nodes should not appear in `simple` by default.

Rules:

- Unknown node with editable value inputs: show in `expert`.
- Unknown node with only connections: hide or show in `expert`.
- User-defined classification may move it to `advanced` later.

Example:

```text
User marks an unknown node as Upscale
  ↓
Next import can show it under advanced / upscale
```

## Pass-through nodes

Pass-through nodes are hidden from normal UI.

Examples:

- VAEEncode
- VAEDecode
- Reroute
- ConditioningCombine
- latent conversion
- image format conversion

Expert display may show:

- node id
- class_type
- source nodes
- target nodes
- editable status

## Principles

- Do not remove nodes from workflow.
- Hidden nodes remain in workflow.
- Simple UI only contains the main controls.
- Advanced UI contains optional generation features.
- Expert UI is for inspection and troubleshooting.
- Connection inputs are read-only by default.
- Fields outside `patch_targets` are not editable.
