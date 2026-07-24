# Capability Analyzer Implementation Plan

## Purpose

This document turns the v2 profile direction into an implementation sequence.

The goal is to build the Analyzer around actual workflow and runtime node capabilities, not only around known node names.

## Primary goal

```text
Preserve workflow.json.
Read runtime node definitions.
Extract operation candidates by input capability.
Classify known nodes semantically.
Expose only safe patch_targets.
Warn on unknown or risky behavior.
```

## Why this is the longest work

This is the highest-cost part because it affects:

```text
app_profile.json schema
Analyzer internals
smartphone field renderer
subgraph handling
bypass/switch handling
multi-output support
unknown custom node handling
warning/compatibility logic
```

If this is wrong, every later feature becomes a patchwork.

## Implementation layers

```text
Layer 1: Workflow preservation and parsing
Layer 2: Runtime node definition reader
Layer 3: Generic input capability extraction
Layer 4: Known semantic detectors
Layer 5: Structure analysis
Layer 6: Safety validator
Layer 7: app_profile v2 builder
Layer 8: Debug report and test fixtures
```

## Layer 1: Workflow preservation and parsing

Required work:

```text
- Accept workflow JSON input.
- Detect API workflow vs UI workflow vs converted workflow.
- Preserve original workflow exactly.
- Build a node index.
- Build an edge/connection index.
- Keep unknown nodes.
- Keep unknown fields.
- Do not normalize the workflow in a way that changes execution.
```

Output:

```text
workflow_index
node_index
edge_index
source_format
preserved_workflow_json
```

## Layer 2: Runtime node definition reader

Required work:

```text
- Read ComfyUI runtime node definitions when possible.
- Use /object_info or internal runtime metadata.
- Map workflow class_type to runtime node metadata.
- Record input names, input types, widget metadata, required/optional/hidden flags, return types, category, and output status.
```

Output:

```text
runtime_node_defs
missing_node_defs
node_capability_map
```

Rules:

```text
If a node definition is missing, do not delete the node.
If a node definition is missing, mark node as unknown/missing and preserve it.
```

## Layer 3: Generic input capability extraction

Required work:

```text
- Inspect every node input using runtime definition when available.
- Detect simple typed editable inputs.
- Normalize input types into app value types.
- Create operation candidates before semantic labeling.
```

Input type mapping:

```text
STRING  -> text / textarea
INT     -> integer / seed / slider candidate
FLOAT   -> float / slider candidate
BOOLEAN -> switch candidate
COMBO   -> select / model_picker / format_picker candidate
IMAGE   -> image_upload candidate
MASK    -> mask_editor candidate
AUDIO   -> audio_upload candidate
VIDEO   -> video_upload candidate
FILE    -> file_upload candidate
```

Output:

```text
operation_candidates[]
```

Each operation candidate should include:

```text
candidate_id
node_id
class_type
input
raw_type
normalized_value_type
candidate_control_type
current_value
source_confidence
requires_runtime_definition
```

Rules:

```text
Operation candidate does not mean safe UI field.
Operation candidate does not mean supported workflow.
All candidates must pass validator before becoming editable fields.
```

## Layer 4: Known semantic detectors

Known detectors add meaning, labels, grouping, and confidence.

Initial semantic detectors:

```text
PromptDetector
NegativePromptDetector
SamplerDetector
SeedDetector
SizeDetector
BatchDetector
LoadImageDetector
SaveImageDetector
ModelLoaderDetector
LoRADetector
ControlNetDetector
IPAdapterDetector
MaskInpaintDetector
WildcardDetector
LLMDetector
VideoIODetector
AudioIODetector
OutputDetector
```

Each detector should:

```text
- consume operation_candidates
- identify known node patterns
- assign role
- assign label
- assign section
- assign confidence
- propose patch target
- add warnings if needed
```

Rules:

```text
Known detectors improve UX.
Known detectors are not the only source of editable fields.
Unknown simple fields can still become Expert fields.
```

## Layer 5: Structure analysis

Required analyzers:

```text
SubgraphAnalyzer
BypassAnalyzer
SwitchAnalyzer
ActivePathAnalyzer
SetGetAnalyzer
OutputPathAnalyzer
PartialExecutionAnalyzer
```

### SubgraphAnalyzer

Responsibilities:

```text
- Detect subgraphs when represented in workflow data.
- Prefer subgraph-exposed inputs.
- Inspect internals only when available and safely addressable.
- Support nested subgraph metadata.
- Create scoped patch targets when safe.
```

### BypassAnalyzer

Responsibilities:

```text
- Detect bypass/mute state when represented in workflow data.
- Mark dependent fields active or inactive.
- Avoid showing inactive branch fields as normal controls.
- Expose branch toggles only when safe patch targets are known.
```

### SwitchAnalyzer

Responsibilities:

```text
- Detect known switch/select branch nodes.
- Identify selected branch when possible.
- Mark dependent controls.
- Expose mode/branch selector when safe.
```

### OutputPathAnalyzer

Responsibilities:

```text
- Detect output nodes.
- Detect output type candidates.
- Map outputs to viewer types.
- Mark unknown outputs clearly.
```

## Layer 6: Safety validator

The validator is the final gate before any field becomes editable.

Validation questions:

```text
Can the target path be addressed exactly?
Is the input a value input, not a connection input?
Is the value type compatible?
Is the node active or intentionally toggleable?
Is the field inside a safely scoped subgraph?
Is the field external API / credential / file / network sensitive?
Is the output handling understood?
Is generation safe enough, or only editing/display safe?
```

Validator outputs:

```text
safe_field
readonly_field
expert_warning_field
disabled_field
preserve_only
unsupported_reason
```

Rules:

```text
Prefer preserve-only over unsafe editable.
Prefer partial over fake supported.
Prefer warning over silent risk.
```

## Layer 7: app_profile v2 builder

Responsibilities:

```text
- Build compatibility block.
- Build capabilities block.
- Build fields[].
- Build patch_targets{}.
- Build structure block.
- Build runtime_requirements block.
- Build outputs[].
- Build warnings[].
- Include debug data in debug mode.
```

Compatibility decision should depend on:

```text
workflow preserved
profile valid
safe fields available
required runtime nodes present
required models present or warned
output handling known
external API risk acknowledged
unknown risky nodes handled
```

## Layer 8: Debug report and test fixtures

Required fixture categories:

```text
basic txt2img
img2img
inpaint / mask
LoRA
ControlNet
wildcard
subgraph prompt
subgraph inactive branch
bypass ControlNet branch
unknown custom node simple STRING
unknown custom node risky file/path input
video output
video input
LLM prompt node
external API node warning
multiple output types
unknown output type
```

Each fixture should validate:

```text
workflow preservation
operation candidates
fields
patch_targets
warnings
compatibility
outputs
```

## First implementation milestone

Do this first:

```text
1. Add v2 schema builder behind a flag or debug mode.
2. Keep existing v1 output unchanged for current MVP.
3. Add runtime node definition reading.
4. Add generic input capability extraction.
5. Emit operation_candidates in analysis_debug.json.
6. Add expert_unknown fields only in v2/debug output.
```

Reason:

```text
This proves the Analyzer can see beyond known node names without breaking current app behavior.
```

## Second milestone

```text
1. Convert known detectors to consume operation_candidates.
2. Add shared control_type assignment.
3. Add v2 fields[].
4. Add patch target validator.
5. Add warnings for unknown editable and missing runtime definitions.
```

## Third milestone

```text
1. Add subgraph metadata.
2. Add bypass/mute metadata.
3. Add active/inactive field state.
4. Add branch toggle candidates only when safe.
5. Add output_type detection beyond image.
```

## Fourth milestone

```text
1. Update smartphone app to render fields[] through shared controls.
2. Keep v1 simple UI compatibility.
3. Add OutputViewer abstraction.
4. Add WarningCard system.
5. Add Expert / Unknown section.
```

## Do not do during this work

```text
- Do not auto-download models.
- Do not auto-install custom nodes.
- Do not replace unknown nodes.
- Do not rewrite workflow graph connections.
- Do not collapse all unknown fields into unsupported.
- Do not mark unknown workflows supported just because some fields are editable.
- Do not build a full graph editor.
```

## Final goal

```text
A user can bring a workflow with known and unknown nodes.
The Analyzer preserves the workflow.
The Analyzer reads actual runtime node capabilities.
The app exposes safe common controls.
Unknown simple controls can appear in Expert with warnings.
Risky or unclear behavior is preserved but not edited.
The workflow is submitted to ComfyUI with exact safe patches only.
```
