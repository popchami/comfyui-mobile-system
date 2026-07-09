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
```

## Analysis stance

The Analyzer should separate two views:

```text
1. Preserved workflow view
   - the exact workflow saved into workflow.json
   - must preserve all nodes, including bypassed/unknown/subgraph areas

2. App execution/control view
   - the safer interpretation used to build app_profile.json
   - includes subgraph metadata, editable fields, bypass toggles, warnings, and output info
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
- allow the user to expand it
- show internal node list when expanded
- show node class_type values used inside
- show editable text fields and parameters when supported
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
      "internal_nodes": [
        {
          "node_id": "42/internal/1",
          "class_type": "CLIPTextEncode",
          "label": "Prompt encoder"
        },
        {
          "node_id": "42/internal/2",
          "class_type": "KSampler",
          "label": "Sampler"
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
  }
}
```

Important:

```text
A subgraph field must not become editable unless the Analyzer can write a valid nested patch target.
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
```

## Bypass analysis strategy

When a node or branch appears bypassed/disabled/muted:

```text
- Preserve it in workflow.json.
- Record its status in analysis_report.
- Record whether bypass ON/OFF is supported.
- If supported, create a bypass toggle field in app_profile.json.
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
      "bypass_toggle_supported": true,
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
  }
}
```

If representation is not validated:

```text
- show bypass status
- do not provide toggle
- show warning that bypass editing is unsupported for this workflow format
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
      "1": { "state": "active", "confidence": "high" },
      "2": { "state": "bypassed", "confidence": "medium" },
      "42/internal/8": {
        "state": "subgraph_internal",
        "subgraph_id": "subgraph_1",
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
- patch target is clear
- output path uses that field
- confidence is high enough
```

Subgraph Core Inputs may be shown inside the subgraph card if they are safe.

### Basic / Advanced

Expose when:

```text
- node is likely active or clearly subgraph_internal
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
- safe subgraph fields can be edited and patched correctly
- bypass ON/OFF works only when validated
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

Stage 2: App awareness
- app shows subgraph cards
- app can expand readable subgraphs
- app lists internal node types

Stage 3: Safe nested editing
- expose editable text/parameters inside readable subgraphs
- write validated nested patch_targets

Stage 4: Bypass controls
- expose bypass ON/OFF when representation is validated
- use explicit graph-control patch_targets

Stage 5: Advanced validation
- test many workflow formats and custom-node subgraph styles
```

## Product guardrail

```text
Subgraphs are first-class workflow structures, not warnings only.
Bypass ON/OFF is a desired graph-control feature, but only with validated patch targets.
When the Analyzer is unsure, preserve and warn.
When the Analyzer is sure, expose the correct app controls with explicit context.
Correctness is more important than exposing every possible control early.
```
