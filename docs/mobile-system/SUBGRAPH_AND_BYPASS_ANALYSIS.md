# Subgraph and Bypass Analysis

## Purpose

This file records how the Analyzer and smartphone app should handle subgraphs, bypassed nodes, muted nodes, disabled branches, grouped workflow areas, and other graph-control behavior.

This is important because the smartphone app must not expose controls for the wrong execution path or corrupt the user's workflow.

## Updated product requirement

Subgraph and bypass handling are not just warning-only features.

They are required product capabilities.

The system must eventually support:

```text
- reading subgraphs
- analyzing subgraphs
- writing subgraph metadata into app_profile.json
- making the smartphone app aware that a section is a subgraph
- expanding a subgraph in the app to see what nodes it uses
- exposing editable text inputs and parameters inside a subgraph when safe
- preserving nested patch targets exactly
- allowing bypass ON/OFF when the bypass representation is validated
- making bypass ON/OFF state visually obvious in the smartphone app
- excluding bypass-OFF nodes/branches from normal text input and parameter editing
```

## Core risk

Subgraphs and bypass states can change what actually runs.

If the Analyzer ignores them, the smartphone app may:

```text
- expose controls for nodes that are not executed
- hide controls for nodes that are executed inside a subgraph
- patch values in a branch that is bypassed
- misunderstand output nodes
- misclassify output type
- break a workflow by flattening or rewriting hidden structure
- let the user edit text/parameters that will not affect generation because the node is OFF
```

## Main rule

```text
Do not destructively flatten, delete, or rewrite subgraphs/bypassed areas during analysis.
```

The Analyzer should:

```text
- preserve the original workflow
- read subgraph structure when available
- analyze subgraph internals when readable
- write subgraph metadata into app_profile.json
- mark execution state when known
- report uncertainty when not known
- expose editable subgraph controls only when patch targets are safe
- allow bypass ON/OFF only when representation and patching are validated
- mark bypass-OFF fields as inactive/edit-excluded in app_profile.json
```

## Terms

Use these working terms even if each workflow/custom node represents them differently:

```text
active node
- likely participates in the current execution path

bypassed node
- present in the workflow but intentionally skipped or disabled

muted node
- present but not intended to execute or affect output

inactive branch
- a connected area that exists but is not part of the current run path

subgraph
- a nested or grouped workflow structure that may contain internal nodes, inputs, parameters, outputs, and dependencies

subgraph input
- an exposed input on a subgraph boundary or an editable internal input that can be safely mapped to the app

subgraph output
- an output produced by a subgraph or by a node inside a subgraph

unknown execution state
- Analyzer cannot prove whether the node runs or not

bypass-OFF edit exclusion
- text inputs and parameters inside a bypassed/OFF node or branch must not be treated as active editable generation controls
```

## Analysis stance

The Analyzer should separate two views:

```text
1. Preserved workflow view
   - the exact workflow saved into workflow.json
   - must preserve all nodes, including bypassed/unknown/subgraph areas

2. App execution/control view
   - the safer interpretation used to build app_profile.json
   - includes subgraph metadata, editable fields, bypass toggles, visual state, inactive edit rules, warnings, and output info
```

## Subgraph analysis strategy

When a workflow contains subgraph-like structures:

```text
- Preserve the subgraph structure.
- Read the subgraph.
- Analyze inside the subgraph if the structure is readable.
- Record the subgraph as a distinct object in app_profile.json.
- Mark internal nodes with a subgraph path.
- Record what node types are used inside the subgraph.
- Record editable text inputs and parameters inside the subgraph when patching is safe.
- Record whether those editable fields are currently active or bypass-OFF/inactive.
- Record outputs inside the subgraph.
- Do not flatten it destructively.
- If the Analyzer cannot inspect inside, mark it as unsupported/unknown with a clear warning.
```

## Smartphone app subgraph requirements

The smartphone app must be able to show that a section is a subgraph.

App behavior should include:

```text
- show a subgraph card/section
- label it as Subgraph
- show subgraph name/id
- show status: supported / partially supported / unsupported
- show active/bypassed/OFF visual state when known
- allow the user to expand it
- show internal node list when expanded
- show node class_type values used inside
- show editable text fields and parameters when supported and active
- visually disable or hide editable fields when their node/branch is bypass-OFF
- show warnings for unsupported internal nodes or unsafe patch targets
```

The app must not make a subgraph look like an ordinary flat node.

## Subgraph metadata shape

Potential app_profile shape:

```json
{
  "subgraphs": [
    {
      "subgraph_id": "subgraph_1",
      "name": "Face Detail Pass",
      "node_id": "42",
      "status": "supported",
      "execution_state": "active",
      "visual_state": "on",
      "internal_nodes": [
        {
          "node_id": "42/internal/1",
          "class_type": "CLIPTextEncode",
          "label": "Prompt encoder",
          "execution_state": "active"
        },
        {
          "node_id": "42/internal/2",
          "class_type": "KSampler",
          "label": "Sampler",
          "execution_state": "active"
        }
      ],
      "editable_fields": [
        "subgraph_1_prompt",
        "subgraph_1_steps"
      ],
      "outputs": [
        "subgraph_1_output_1"
      ],
      "warnings": []
    }
  ]
}
```

## Nested patch targets

Editable fields inside subgraphs must use explicit nested patch targets.

Potential patch target shape:

```json
{
  "field_id": "subgraph_1_prompt",
  "target": {
    "node_id": "42",
    "subgraph_path": ["42", "internal_node_8"],
    "input": "text"
  },
  "safety": {
    "patch_supported": true,
    "confidence": "high"
  },
  "active_when": {
    "bypass_state": "on"
  }
}
```

Important:

```text
A subgraph field must not become editable unless the Analyzer can write a valid nested patch target.
If its node/branch is bypass-OFF, it must not be shown as an active text/parameter input.
```

## Editable subgraph fields

If a subgraph contains text input or parameter controls, the Analyzer should detect and expose them when safe.

Examples:

```text
- prompt text inside subgraph
- negative prompt text inside subgraph
- seed inside subgraph
- steps inside subgraph
- cfg inside subgraph
- denoise inside subgraph
- image/video/audio input inside subgraph
- width/height/frame/fps/duration parameter inside subgraph
- LoRA strength inside subgraph
- ControlNet strength inside subgraph
```

Rules:

```text
- Editable fields inside subgraphs must keep their subgraph context.
- App labels should make it clear that the field belongs to a subgraph.
- Patching must target the correct internal node.
- The original subgraph must remain preserved.
- If the editable field belongs to a bypass-OFF node/branch, it is inactive and must not be treated as an active input.
```

## Bypass analysis strategy

When a node or branch appears bypassed/disabled/muted:

```text
- Preserve it in workflow.json.
- Record its status in analysis_report.
- Record whether bypass ON/OFF is supported.
- If supported, create a bypass toggle field in app_profile.json.
- Record visual state metadata so the app can make ON/OFF obvious.
- If bypass is OFF, mark all text inputs and parameters under that node/branch as inactive/edit-excluded.
- If unsupported, show it as read-only status with a warning.
- Do not delete it.
- Do not reconnect around it unless this is proven to match ComfyUI behavior.
```

Potential app_profile field:

```json
{
  "node_states": {
    "12": {
      "execution_state": "bypassed",
      "visual_state": "off",
      "bypass_toggle_supported": true,
      "edit_exclusion": true,
      "confidence": "high",
      "reason": "validated bypass state path exists in source workflow"
    }
  }
}
```

## Bypass ON/OFF support

Bypass ON/OFF is a desired app feature.

It must be implemented carefully because toggling bypass changes workflow execution.

Rules:

```text
- Do not guess bypass representation.
- Only expose bypass ON/OFF when the Analyzer can prove where the bypass state is stored.
- Create an explicit patch_target for bypass state.
- Mark the field as a graph-control field, not a normal generation parameter.
- Show warning text in the app that bypass changes execution path.
- Make ON/OFF visually obvious in the app.
- When OFF, the node/branch must look inactive, dimmed, disabled, collapsed, or clearly marked OFF.
- When OFF, any text input or parameter inside that node/branch is excluded from active editing.
- Preserve original workflow structure.
```

Potential field:

```json
{
  "field_id": "node_12_bypass",
  "type": "boolean",
  "label": "Bypass node 12",
  "group": "Graph Controls",
  "target": {
    "node_id": "12",
    "input_or_property": "bypass"
  },
  "safety": {
    "patch_supported": true,
    "changes_execution_path": true,
    "confidence": "high"
  },
  "visual": {
    "on_label": "ON / active",
    "off_label": "OFF / bypassed",
    "off_fields_behavior": "disabled"
  }
}
```

If representation is not validated:

```text
- show bypass status
- do not provide toggle
- show warning that bypass editing is unsupported for this workflow format
```

## Bypass visual state requirements

The smartphone app must make bypass state visible at a glance.

Required behavior:

```text
- ON/active state should look usable.
- OFF/bypassed state should look inactive.
- OFF/bypassed nodes/sections should not look like normal editable controls.
- OFF/bypassed sections should show a clear label such as OFF, Bypassed, Disabled, or Inactive.
- OFF/bypassed fields should be disabled, dimmed, hidden behind an inactive section, or otherwise clearly not editable.
- If the user turns bypass ON, eligible inputs become active again.
- If the user turns bypass OFF, eligible inputs become inactive immediately.
```

Important:

```text
Even if a prompt/text field has saved text, it is not an active input while its node/branch is bypass-OFF.
The app must not suggest that editing that text will affect generation until the branch is ON/active.
```

## Execution path analysis

The Analyzer should build an execution path map.

Possible states:

```text
active
bypassed
muted
inactive
subgraph_internal
unknown
```

Possible visual states:

```text
on
off
partial
unknown
```

Possible confidence levels:

```text
high
medium
low
unknown
```

Candidate metadata:

```json
{
  "execution_map": {
    "nodes": {
      "1": { "state": "active", "visual_state": "on", "confidence": "high" },
      "2": { "state": "bypassed", "visual_state": "off", "confidence": "medium" },
      "42/internal/8": {
        "state": "subgraph_internal",
        "subgraph_id": "subgraph_1",
        "visual_state": "on",
        "confidence": "high"
      }
    },
    "edges": [],
    "warnings": []
  }
}
```

## UI exposure rules

### Core Inputs

Expose fields in Core Inputs when:

```text
- node is likely active
- node/branch is not bypass-OFF
- patch target is clear
- output path uses that field
- confidence is high enough
```

Subgraph Core Inputs may be shown inside the subgraph card if they are safe and active.

### Basic / Advanced

Expose when:

```text
- node is likely active or clearly subgraph_internal
- node/branch is not bypass-OFF
- field is known and safe
- patch target is explicit
- confidence is medium or high
```

### Graph Controls

Bypass ON/OFF should live under Graph Controls, not normal generation settings.

Expose when:

```text
- bypass representation is validated
- patch target is explicit
- changing it is understood to affect execution path
```

### Expert / Debug

Place here when:

```text
- node is bypassed but toggle is unsupported
- node is inside uncertain subgraph
- execution state is unknown
- patch target is ambiguous
- LLM only suggested it but deterministic rules did not confirm it
```

### Hidden / not exposed

Do not expose when:

```text
- patching may break workflow
- target path cannot be resolved
- nested subgraph patching is unsupported for that field
- node is inactive and irrelevant to output
- node/branch is bypass-OFF and the field is a normal text/parameter input
```

## Output detection with bypass/subgraph

Output detection must consider execution state.

Rules:

```text
- Prefer active output nodes.
- Do not assume every SaveImage-like node is the final output.
- A bypassed output node should not be treated as primary output unless bypass state makes it active after toggle.
- If multiple outputs exist, list all candidates with confidence.
- If output is inside a subgraph, record subgraph path and support status.
- If output type is unknown, mark as unknown rather than image.
```

Candidate output metadata:

```json
{
  "outputs": [
    {
      "output_id": "output_1",
      "type": "image",
      "node_id": "9",
      "execution_state": "active",
      "confidence": "high",
      "fetch_strategy": "view"
    },
    {
      "output_id": "subgraph_1_output_1",
      "type": "image",
      "node_id": "42",
      "subgraph_path": ["42", "internal_output_2"],
      "execution_state": "subgraph_internal",
      "confidence": "high",
      "fetch_strategy": "view"
    }
  ]
}
```

## LLM assistance for subgraph/bypass

LLM can help explain ambiguous graph areas, but must not decide final execution state alone.

Allowed LLM help:

```text
- explain what an unknown subgraph may do
- suggest human-readable warnings
- suggest possible field labels
- summarize complex graph sections
```

Not allowed:

```text
- final active/bypassed decision without deterministic evidence
- final nested patch_target creation
- deleting or flattening subgraphs
- declaring output supported without validation
```

## Validation requirements

The validation matrix must include workflows with:

```text
- readable subgraph
- unsupported/unknown subgraph
- editable prompt inside subgraph
- editable numeric parameter inside subgraph
- output inside subgraph
- bypassed node
- bypass ON/OFF supported node
- bypass state present but unsupported for editing
- bypass-OFF node with existing text input
- bypass-OFF node with existing numeric parameter
- muted/disabled node
- inactive branch
- multiple output nodes
- custom node with internal workflow behavior
- unknown output inside nested structure
```

For each case validate:

```text
- workflow.json is preserved
- subgraph metadata is written
- app shows subgraph as subgraph
- app can expand subgraph and list internal node types when readable
- safe subgraph fields can be edited and patched correctly when active
- bypass ON/OFF works only when validated
- bypass state is visually obvious
- bypass-OFF fields are not active text/parameter inputs
- unsupported bypass states are read-only with warning
- outputs are not misclassified
- app does not crash
- warnings are understandable
```

## MVP staging

Subgraph/bypass support may be staged, but the direction is not optional.

Suggested stages:

```text
Stage 1: Preserve + detect
- preserve subgraphs and bypassed areas
- detect obvious subgraph/bypass states
- show warnings
- mark bypass visual state when known

Stage 2: App awareness
- app shows subgraph cards
- app can expand readable subgraphs
- app lists internal node types
- app shows bypass ON/OFF visually

Stage 3: Safe nested editing
- expose editable text/parameters inside readable subgraphs
- write validated nested patch_targets
- exclude bypass-OFF fields from active editing

Stage 4: Bypass controls
- expose bypass ON/OFF when representation is validated
- use explicit graph-control patch_targets
- immediately update visual state and active/inactive inputs

Stage 5: Advanced validation
- test many workflow formats and custom-node subgraph styles
```

## Product guardrail

```text
Subgraphs are first-class workflow structures, not warnings only.
Bypass ON/OFF is a desired graph-control feature, but only with validated patch targets.
Bypass state must be visually obvious in the app.
Bypass-OFF text inputs and parameters are not active editing targets.
When the Analyzer is unsure, preserve and warn.
When the Analyzer is sure, expose the correct app controls with explicit context.
Correctness is more important than exposing every possible control early.
```
