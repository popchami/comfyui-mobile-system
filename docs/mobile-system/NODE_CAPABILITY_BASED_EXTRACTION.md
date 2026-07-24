# Node Capability Based Extraction Strategy

## Purpose

This document records an important correction to the Analyzer strategy.

The Analyzer must not depend only on the features the product owner already knows about.

The product owner may mention image generation, video generation, audio generation, LoRA, wildcard, Ollama, Gemma, subgraphs, and bypass as examples. However, ComfyUI and custom nodes can expose many more capabilities that may become user-operated fields.

Therefore, the Analyzer must discover possible user operation points from the actual ComfyUI environment and workflow structure.

## Core decision

```text
Human-known feature list = helpful examples
Actual ComfyUI node definitions = source of truth
Workflow graph connections = execution meaning
Validator = final safety gate
```

The Analyzer must not be limited to a manually maintained list such as:

```text
PromptDetector
KSamplerDetector
LoRADetector
ControlNetDetector
WildcardDetector
VideoDetector
AudioDetector
```

Those are useful, but incomplete.

The Analyzer also needs a generic capability-based pass.

## Why this is required

ComfyUI is not only an image generation UI.

ComfyUI built-in nodes already include broad categories such as:

```text
3D
Advanced
API Node
Audio
Conditioning
Experimental
Image
Latent
Loader
Model
Partner
Sampling
Text
Utilities
Video
```

Custom nodes can add even more node classes, widgets, file inputs, model inputs, branch controls, and output types.

A user may bring a workflow that uses features the product owner has never heard of.

Those features may still expose user-editable values.

## Required Analyzer structure

```text
Workflow Parser
  ↓
Runtime Node Definition Reader
  ↓
Generic Input Analyzer
  ↓
Known Node Semantic Detector
  ↓
Unknown-but-editable Detector
  ↓
Workflow Structure Analyzer
  ↓
Subgraph / Bypass / Switch Analyzer
  ↓
Output Type Analyzer
  ↓
Safety Validator
  ↓
app_profile.json
```

## Runtime node definition reading

The Analyzer should inspect the ComfyUI runtime environment when possible.

It should read available node definitions through ComfyUI's object information, equivalent runtime node metadata, or internal node registry data.

For each workflow node, it should identify:

```text
class_type
node title / metadata
input names
input data types
widget types
required inputs
optional inputs
hidden inputs
return types
category
whether it is an output node
```

This lets the Analyzer identify operation candidates even for unknown custom nodes.

## Generic Input Analyzer

The Analyzer must inspect input types before relying on known node names.

Examples:

```text
STRING  → prompt, system prompt, filename, tag, style text, wildcard text, URL, caption, template
INT     → seed, steps, width, height, frame count, batch count, index, skip frames, repeat count
FLOAT   → cfg, denoise, strength, weight, fps, temperature, volume, threshold, blur, scale
BOOLEAN → ON/OFF, save, loop, randomize, enable feature, use mask, use audio
COMBO   → model picker, sampler picker, scheduler picker, preset picker, mode picker, format picker
IMAGE   → image upload, reference image, img2img input, ControlNet input, IPAdapter input
MASK    → mask upload, paint mask, inpaint area, segmentation mask
AUDIO   → audio upload, voice reference, BGM, speech source
VIDEO   → video upload, reference video, video-to-video source
```

These are operation candidates, not automatically safe fields.

## Known Node Semantic Detector

Known nodes should still receive better labels and UI grouping.

Examples:

```text
CLIPTextEncode.text             → prompt / negative prompt candidate
KSampler.seed                   → seed
KSampler.steps                  → steps
KSampler.cfg                    → CFG
KSampler.sampler_name           → sampler
KSampler.scheduler              → scheduler
KSampler.denoise                → denoise
LoadImage.image                 → image upload
SaveImage.filename_prefix       → output filename prefix
LoraLoader.strength_model       → LoRA model strength
LoraLoader.strength_clip        → LoRA CLIP strength
ControlNet apply strength       → ControlNet strength
Video load frame settings       → video input controls
Video combine format/fps        → video output controls
LLM prompt/system/model fields  → text/LLM controls
```

Known detectors are for meaning, grouping, and safer UX.

They are not the only detection mechanism.

## Unknown-but-editable Detector

Unknown custom nodes can still contain fields that users may want to edit.

If a node is unknown but its input definition is safe and widget-like, the app can expose it under an Expert or Unknown editable section.

Candidate examples:

```text
STRING multiline
INT with min/max/step
FLOAT with min/max/step
BOOLEAN
COMBO dropdown
```

The UI should show:

```text
node title
class_type
input name
input type
current value
warning that the field is not semantically classified
```

Example:

```text
Unknown Custom Node: SomePromptMixer
input: style_text
type: STRING
current value: cinematic lighting
section: Expert / Unknown editable inputs
```

## Safety rules for unknown editable fields

Unknown editable does not mean fully supported.

```text
Allowed:
- show in Expert section
- patch exact simple widget values
- warn that meaning is unknown

Not allowed:
- change node connections
- replace nodes
- infer complex behavior
- mark workflow fully supported only because unknown fields are editable
```

## Subgraph handling

Subgraphs must not be ignored.

Subgraphs may contain user operation points such as:

```text
prompt fields
image inputs
mask inputs
LoRA controls
ControlNet controls
video controls
LLM controls
switches
bypassable branches
nested subgraphs
```

The Analyzer should inspect subgraph-exposed inputs first.

If subgraph internals are available and safely addressable, internal operation points can be included with scoped patch targets.

Example target:

```json
{
  "scope": "subgraph",
  "subgraph_id": "subgraph_12",
  "node_id": "45",
  "input": "text"
}
```

If a subgraph cannot be safely inspected or patched, preserve it and warn.

## Bypass / mute / branch / switch handling

The Analyzer must distinguish node existence from active execution.

A workflow may contain inactive branches.

Examples:

```text
ControlNet branch exists but is OFF
LoRA branch exists but is bypassed
FaceDetailer branch exists but is muted
Wildcard branch exists but is inactive
Video branch exists but only runs for a selected output
```

Rules:

```text
Active branch fields can be enabled.
Inactive branch fields should be disabled, hidden, or shown as inactive.
Branch/switch controls should be exposed only when their safe patch target is known.
Do not expose fields from inactive branches as normal active controls.
```

## Output type handling

The app must not assume image output only.

Output candidates include:

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

The Analyzer should detect output nodes and return output metadata.

The app should display supported outputs normally and unknown outputs with warnings.

## Partner Nodes / External API nodes

Some workflows may call external providers or hosted models through API/partner nodes.

The Analyzer should identify external API-like nodes where possible and mark them with warnings.

Potential warnings:

```text
external_api_warning
privacy_warning
cost_warning
credential_required_warning
network_required_warning
```

Rules:

```text
Do not hide external API usage.
Do not silently send user inputs to third-party services.
Do not mark such workflows as fully safe without explicit metadata and user-facing warning.
```

## Wildcard / Dynamic prompt handling

Wildcards may be implemented in different ways:

```text
App-side text expansion
ComfyUI-side wildcard custom node
Text file random line node
Dynamic prompt syntax
Prompt template / variable node
Dictionary replacement node
LLM prompt expansion node
```

The Analyzer should not assume a single wildcard implementation.

It should identify:

```text
wildcard files
text templates
random line selectors
seed/random controls
file path inputs
dynamic prompt text
previewable expansion output if available
```

Unknown wildcard-like nodes should be preserved and optionally surfaced under Expert.

## LLM / Ollama / Gemma handling

LLM nodes may be local, API-based, or custom.

Possible operation fields:

```text
prompt
system prompt
model name
temperature
top_p
max tokens
response format
seed
input image
input text file
output text connection
```

Rules:

```text
The smartphone app does not execute LLMs itself unless explicitly designed later.
If the workflow executes LLM nodes inside ComfyUI, keep that execution inside ComfyUI.
Expose only safe LLM fields.
Warn for external API nodes and credentials.
```

## app_profile.json implications

The profile should support more than simple fields.

Potential structure:

```text
fields
  core
  advanced
  expert_unknown

structure
  subgraphs
  bypass_states
  switches
  set_get_links
  output_nodes
  partial_execution_targets

capabilities
  input_types
  output_types
  external_api_nodes
  model_requirements
  custom_node_requirements

safety
  compatibility_level
  safe_to_edit
  safe_to_generate
  warnings
  external_api_warning
  privacy_warning
  cost_warning
```

## UI implication

The smartphone app should have at least three levels of visibility.

```text
Core
- prompt
- negative prompt
- main image/video/audio input
- generate/stop
- result preview

Advanced
- seed
- steps
- CFG
- denoise
- sampler
- scheduler
- LoRA
- ControlNet
- wildcard
- video/audio/output settings

Expert / Unknown
- safe simple inputs from unknown custom nodes
- subgraph-exposed fields
- switch/branch controls
- raw node labels
- warnings
```

## Product rule

```text
Unknown does not mean useless.
Unknown also does not mean safe.
```

Therefore:

```text
Unknown + simple typed widget + exact patch target
  → Expert editable with warning

Unknown + complex connection / unclear behavior
  → preserve only, no edit

Unknown + external API / credentials / file/network risk
  → warning and disabled unless explicitly supported
```

## Final principle

```text
Do not build the Analyzer around only the product owner's current knowledge.
Build it around the actual ComfyUI runtime node definitions and workflow graph.
```

The Analyzer must be capability-based first, semantic-detector-based second, and validator-gated always.
