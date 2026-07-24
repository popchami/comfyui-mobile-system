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

## Collapsible section rules

The app should not put every field directly on the screen.

After the workflow is analyzed, the app should render fields using this priority:

```text
Always visible:
- prompt
- negative prompt
- required image input
- connection/status messages
- Generate button
- generated result area

Collapsed by default:
- basic_sampling
- size
- advanced sections
- expert sections

Hidden:
- hidden sections
- fields outside patch_targets
- internal workflow-only nodes
```

Important rule:

```text
Do not collapse everything.
```

Reason:

```text
If every usable field is collapsed, the user opens a profile and sees no obvious place to start.
The app should show the core creative inputs first, then fold detailed settings below.
```

Recommended default layout:

```text
1. Core Inputs                 open
   - prompt
   - negative prompt
   - required image input

2. Basic Generation Settings   collapsed
   - seed
   - steps
   - cfg
   - sampler
   - scheduler
   - denoise

3. Size / Output               collapsed
   - width
   - height
   - batch
   - output filename/prefix if editable

4. Advanced Workflow Features  collapsed
   - LoRA
   - ControlNet
   - IPAdapter
   - FaceDetailer
   - Upscale
   - RemBG
   - Inpaint
   - Mask
   - Wildcard
   - LLM/Ollama

5. Expert / Debug              collapsed
   - unknown editable inputs
   - custom node warnings
   - raw analyzed node list
   - raw workflow/debug info
```

If a workflow has no prompt-like field, the app should still show the first required editable input, then fold the remaining settings.

## Collapsible metadata direction

Future `app_profile.json` may include explicit section metadata:

```json
{
  "sections": [
    {
      "section_id": "core_inputs",
      "label": "Core Inputs",
      "visibility": "simple",
      "default_expanded": true,
      "priority": 10
    },
    {
      "section_id": "basic_sampling",
      "label": "Basic Generation Settings",
      "visibility": "simple",
      "default_expanded": false,
      "priority": 20
    },
    {
      "section_id": "advanced_features",
      "label": "Advanced Workflow Features",
      "visibility": "advanced",
      "default_expanded": false,
      "priority": 30
    }
  ]
}
```

Until Analyzer emits explicit section metadata, the app may use built-in fallback grouping based on `field_id`, `label`, `type`, and `section`.

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
- Do not collapse every usable field.
- Core creative inputs should remain visible by default.
- Detailed settings should be collapsible by default.
