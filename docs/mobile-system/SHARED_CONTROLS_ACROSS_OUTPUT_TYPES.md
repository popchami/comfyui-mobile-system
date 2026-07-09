# Shared Controls Across Output Types

## Purpose

This document records a product and architecture decision:

```text
When output types differ, prioritize shared app controls and shared Analyzer logic before building output-specific UI.
```

A workflow may output:

```text
image
video
audio
text
json
svg
3d
file
zip
unknown
```

Even when outputs differ, many user operation points share the same input patterns.

The app should not be built as separate image/video/audio apps.

It should be built from reusable control components driven by `app_profile.json`.

## Core principle

```text
Different output type does not always mean different input UI.
```

The app should prioritize common control types:

```text
STRING  -> TextControl
INT     -> IntegerControl / SeedControl
FLOAT   -> FloatControl / SliderControl
BOOLEAN -> ToggleControl
COMBO   -> DropdownControl
IMAGE   -> ImageUploadControl / ImagePreview
MASK    -> MaskEditorControl
AUDIO   -> AudioUploadControl / AudioPreview
VIDEO   -> VideoUploadControl / VideoPreview
FILE    -> FileUploadControl
OUTPUT  -> OutputViewer
```

## Why this matters

Image, video, audio, text, 3D, and external API workflows may all contain:

```text
prompt-like text
system prompt
filename prefix
seed
randomize toggle
strength
weight
model selection
format selection
reference media input
branch ON/OFF
output preview
warnings
history
```

These should be implemented once as shared app controls.

## Shared controls to prioritize

### Text controls

```text
TextControl
MultilineTextControl
PromptEditor
NegativePromptEditor
SystemPromptEditor
TextTemplateEditor
WildcardTextEditor
FilenamePrefixEditor
URLInputControl
```

Possible uses:

```text
image prompt
video prompt
audio prompt
LLM prompt
system prompt
caption
style text
wildcard text
save filename
external API prompt
```

### Numeric controls

```text
IntegerControl
FloatControl
SliderControl
SeedControl
RangeControl
```

Possible uses:

```text
seed
steps
CFG
denoise
strength
weight
fps
frame count
width
height
batch
volume
temperature
top_p
threshold
blur
scale
loop count
```

### Boolean controls

```text
BooleanControl
FeatureToggleControl
```

Possible uses:

```text
save output
loop
randomize
use audio
use mask
enable feature
high quality
metadata on/off
```

Important distinction:

```text
BooleanControl
= a normal node input boolean

BranchStateControl
= bypass / mute / switch / branch state
```

Do not mix them internally.

### Dropdown / picker controls

```text
DropdownControl
ModelPickerControl
FormatPickerControl
PresetPickerControl
ModePickerControl
ProviderPickerControl
VoicePickerControl
```

Possible uses:

```text
checkpoint
LoRA
VAE
CLIP
ControlNet model
upscale model
video model
audio model
LLM model
sampler
scheduler
format
quality
aspect ratio
provider
voice
speaker
mode
```

### Media input controls

```text
MediaUploadControl
ImageUploadControl
MaskEditorControl
AudioUploadControl
VideoUploadControl
FileUploadControl
PreviewControl
```

Possible uses:

```text
reference image
img2img input
ControlNet input
IPAdapter input
mask / inpaint area
voice reference
BGM
audio source
video source
video-to-video input
wildcard txt
CSV
JSON
```

### Strength / weight controls

```text
StrengthSlider
WeightSlider
InfluenceSlider
StartEndStepControl
```

Possible uses:

```text
LoRA strength
ControlNet strength
IPAdapter weight
denoise
style strength
detailer strength
mask strength
motion strength
audio effect strength
LLM temperature-like control
```

### Branch / switch / bypass controls

```text
BranchToggleControl
SubgraphToggleControl
SwitchControl
ModeControl
ActivePathIndicator
```

Possible uses:

```text
LoRA branch ON/OFF
ControlNet branch ON/OFF
Upscale branch ON/OFF
FaceDetailer branch ON/OFF
RemBG branch ON/OFF
Wildcard branch ON/OFF
LLM branch ON/OFF
video branch ON/OFF
audio branch ON/OFF
save branch ON/OFF
preview branch ON/OFF
```

Rules:

```text
If a branch is inactive, its controls should be disabled, hidden, or shown as inactive.
If the Analyzer cannot safely patch the branch state, do not expose the toggle.
```

### Subgraph control groups

```text
SubgraphControlGroup
SubgraphAdvancedGroup
SubgraphExpertGroup
```

Possible uses:

```text
exposed prompt
exposed image input
exposed mask input
exposed strength
exposed model picker
exposed mode selector
exposed ON/OFF
nested subgraph controls
```

Rules:

```text
Subgraph controls can be grouped separately.
Subgraph internals should not flood the main UI.
Exposed safe controls should be prioritized.
Unknown internals should be preserved and warned.
```

### Warning controls

```text
WarningCard
MissingModelWarning
MissingCustomNodeWarning
ExternalApiWarningCard
CostWarningCard
PrivacyWarningCard
CredentialRequiredWarning
UnsupportedOutputWarning
UnknownPatchTargetWarning
```

Possible uses:

```text
missing checkpoint
missing LoRA
missing custom node
external API call
third-party provider
credits / cost risk
credential required
unknown output type
unsupported field
unsafe patch target
```

Warnings are shared across all output types.

### Output viewers

```text
OutputViewer
ImageViewer
VideoViewer
AudioPlayer
TextViewer
JsonViewer
SvgViewer
FileViewer
UnknownOutputViewer
```

Rules:

```text
The app should not assume only image output.
The app should select viewer based on output_type.
If the output type is unknown, preserve/download/display metadata where possible and warn.
```

## Recommended app architecture

```text
app_profile.json
  ↓
Field renderer
  ↓
Shared control components
  ↓
patch_targets
  ↓
workflow.json patch
  ↓
ComfyUI /prompt
  ↓
OutputViewer by output_type
```

Do not build separate hardcoded screens for image, video, audio, text, and 3D first.

Build reusable controls first.

## Priority order

### Highest priority shared controls

```text
TextControl
NumberControl
BooleanControl
DropdownControl
MediaUploadControl
OutputViewer
SeedControl
ModelPickerControl
StrengthSlider
WarningCard
History
Queue / Stop
```

### Next priority shared controls

```text
SubgraphControlGroup
BranchToggleControl
SwitchControl
WildcardControl
MaskEditorControl
FilePickerControl
FormatPickerControl
PresetManager
```

### Later shared controls

```text
3D viewer
advanced audio editor
advanced video timeline
full JSON editor
full graph editor
cloud sync
marketplace
```

## Product guardrail

```text
Do not create one-off UI for every known node first.
Do not build only an image generation UI.
Do not assume output file type determines every control.
Do not turn the app into a full ComfyUI graph editor.
```

Instead:

```text
Build shared controls from input capability types.
Group them by profile section.
Render them from app_profile.json.
Patch only safe patch_targets.
Display output through output-type viewers.
```

## Final principle

```text
The reusable app layer is more important than any single output type.
```

This lets the app support image workflows first while still being architecturally ready for video, audio, text, 3D, wildcard, LLM, API, subgraph, bypass, and unknown custom node workflows.
