# Subgraph and Bypass Analysis

## Purpose

This file records how the Analyzer should think about subgraphs, bypassed nodes, muted nodes, disabled branches, grouped workflow areas, and other graph-control behavior.

This is important because the smartphone app must not expose controls for the wrong execution path or corrupt the user's workflow.

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
- mark execution state when known
- report uncertainty when not known
- expose only safe controls by default
- keep risky or uncertain controls in Expert / Debug or warnings
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
- a nested or grouped workflow structure that may contain internal nodes and outputs

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
   - only exposes controls that are likely safe and relevant
```

## Bypass analysis strategy

When a node or branch appears bypassed/disabled/muted:

```text
- Preserve it in workflow.json.
- Record its status in analysis_report.
- Do not expose its fields as normal Core/Basic controls by default.
- If useful, place it under Expert / Debug with a warning.
- Do not delete it.
- Do not reconnect around it unless this is proven to match ComfyUI behavior.
```

Potential app_profile field:

```json
{
  "node_states": {
    "12": {
      "execution_state": "bypassed",
      "confidence": "medium",
      "reason": "node appears disabled or bypassed in source workflow"
    }
  }
}
```

## Subgraph analysis strategy

When a workflow contains subgraph-like structures:

```text
- Preserve the subgraph structure.
- Analyze inside it if the structure is readable.
- Mark fields with a subgraph path.
- Do not flatten it destructively.
- If output is inside the subgraph, record the output path.
- If the Analyzer cannot inspect inside, mark it as unknown/needs attention.
```

Potential patch target shape:

```json
{
  "field_id": "prompt_1",
  "target": {
    "node_id": "subgraph_node_4",
    "subgraph_path": ["subgraph_node_4", "internal_node_8"],
    "input": "text"
  }
}
```

Important:

```text
Do not introduce subgraph patch_targets until the app and Analyzer can prove that patching nested paths is safe.
```

For MVP, if nested patching is uncertain:

```text
- show a warning
- preserve workflow
- avoid exposing nested field as normal editable control
```

## Execution path analysis

The Analyzer should eventually build an execution path map.

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
      "3": { "state": "unknown", "confidence": "unknown" }
    },
    "edges": [],
    "warnings": []
  }
}
```

## UI exposure rules

### Core Inputs

Only expose fields in Core Inputs when:

```text
- node is likely active
- patch target is clear
- output path uses that field
- confidence is high enough
```

### Basic / Advanced

Expose when:

```text
- node is likely active
- field is known and safe
- confidence is medium or high
```

### Expert / Debug

Place here when:

```text
- node is bypassed
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
- nested subgraph patching is unsupported
- node is inactive and irrelevant to output
```

## Output detection with bypass/subgraph

Output detection must consider execution state.

Rules:

```text
- Prefer active output nodes.
- Do not assume every SaveImage-like node is the final output.
- A bypassed output node should not be treated as primary output.
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
      "output_id": "output_2",
      "type": "unknown",
      "node_id": "subgraph_3",
      "subgraph_path": ["subgraph_3", "internal_output_2"],
      "execution_state": "subgraph_internal",
      "confidence": "low",
      "fetch_strategy": "unknown"
    }
  ]
}
```

## Bypass toggle support

Do not add bypass toggles to the smartphone app in MVP.

Reason:

```text
Toggling bypass changes workflow execution structure.
That is closer to workflow editing than safe parameter editing.
```

Future support may be possible only if:

```text
- ComfyUI representation is understood
- patching bypass state is safe
- app_profile explicitly marks the toggle as safe
- validation proves it does not corrupt workflow
```

## Subgraph editing support

Do not add subgraph editing in MVP.

Possible future levels:

```text
Level 0: Preserve only
- keep subgraph in workflow.json
- no app controls inside it

Level 1: Read-only analysis
- show that subgraph exists
- show warnings and outputs

Level 2: Safe exposed fields
- expose known safe fields inside subgraph
- only with validated nested patch_targets

Level 3: Advanced editing
- not MVP
- avoid unless there is a strong need
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
- bypassed node
- muted/disabled node
- inactive branch
- multiple output nodes
- subgraph or group-like nested structure
- custom node with internal workflow behavior
- unknown output inside nested structure
```

For each case validate:

```text
- workflow.json is preserved
- bypassed/inactive nodes are not exposed as normal controls
- active controls still work
- outputs are not misclassified
- app does not crash
- warnings are understandable
```

## MVP decision

For MVP:

```text
- Preserve subgraphs and bypassed areas.
- Detect obvious bypass/mute/disabled states when possible.
- Avoid normal editable controls for uncertain paths.
- Show warnings instead of guessing.
- Do not flatten subgraphs.
- Do not add bypass toggles.
- Do not add nested subgraph patching unless validated.
```

## Product guardrail

```text
When the Analyzer is unsure, preserve and warn.
Do not guess and mutate.
Correctness is more important than exposing every possible control.
```
