# UI Priority and Analyzer Accuracy Principle

## Purpose

This file records the current product thinking about smartphone app UI and Analyzer priority.

The UI is not fixed yet.

However, the most important user-facing operations are clear:

```text
1. Enter or edit prompts.
2. Upload required input data such as images.
3. Use required image tools such as mask and paint when the workflow needs them.
4. Use workflow helper controls such as wildcards when the workflow/profile exposes them.
5. Review generated data.
6. Change needed parameters.
```

Everything else can be secondary, hidden, collapsed, or moved to another page if needed.

## Core UI direction

The smartphone app does not need to expose the whole workflow graph as the main screen.

The main generation screen should focus on:

```text
- prompt input
- negative prompt when available
- required input files such as image/mask/video/audio
- image upload when the workflow needs it
- mask / paint controls when the workflow needs them
- wildcard controls when the profile exposes them
- essential generation parameters
- generate button
- generated result display
```

Complex node details can be placed elsewhere:

```text
- separate node detail page
- subgraph detail page
- advanced/debug page
- collapsible expert section
- profile analysis report page
```

## One workflow graph behind multiple UI pages

The app may split the UI into visible and less-visible pages.

But internally, those pages must still operate on the same analyzed workflow graph.

```text
Main page controls
Advanced page controls
Graph / Node page controls
Subgraph detail page controls
Debug / report page information
```

All of these are different views over the same source:

```text
workflow.json
app_profile.json
patch_targets
execution_map
subgraph metadata
bypass state metadata
```

Important:

```text
Separate UI pages do not mean separate workflows.
Separate UI pages do not mean disconnected node logic.
Every visible or hidden control must still map back to the correct node/input through Analyzer-generated patch_targets.
```

## Visible vs less-visible controls

Some controls should be easy to reach:

```text
- prompt
- negative prompt when available
- required image upload
- required mask / paint controls
- important parameters
- generate button
- generated output review
```

Some controls can be less visible:

```text
- full node list
- subgraph internals
- bypass ON/OFF
- rare parameters
- raw analyzer report
- unknown node warnings
```

But less visible does not mean less connected.

Less visible controls still affect the same workflow graph when enabled and safely patchable.

## Important implication

Because complex node information may be hidden or moved to a less visible page, the Analyzer must be even more accurate.

If the UI is simple, the user may not notice that the app is patching the wrong node or ignoring an important branch.

Therefore:

```text
Simple UI increases the need for precise analysis.
```

## Main principle

```text
UI convenience must not hide Analyzer uncertainty.
```

If the Analyzer is unsure, the app must not silently expose a field as safe.

The app should either:

```text
- show only validated controls
- move uncertain fields to Expert / Debug
- show warnings
- require validation before exposing risky controls
```

## Node complexity handling

A workflow can be very complex internally.

That does not mean the main app UI must be complex.

Preferred UX:

```text
Main page:
- prompt
- important input uploads
- required mask / paint tools
- important parameters
- generated output

Advanced page:
- detailed parameter groups
- LoRA / ControlNet / FaceDetailer / inpaint / mask controls
- wildcard controls when they are optional or large

Graph / Node page:
- node list
- subgraph expansion
- bypass ON/OFF controls
- execution state
- warnings
- raw analyzer report
```

## Image upload / mask / paint UI implication

When the workflow/profile needs image input, mask, or paint-like editing, those controls are primary user actions.

They should not be treated as hidden debug-only features.

Possible controls:

```text
- image upload
- selected image preview
- clear selected image
- mask editor
- paint brush
- erase brush
- clear mask
- brush size
- mask preview overlay
```

Rules:

```text
- Show image upload when the workflow has an active image input.
- Show mask/paint tools when the workflow has an active mask or inpaint requirement.
- If the image/mask branch is bypass-OFF, show it as inactive and do not treat it as an active input.
- Do not expose mask/paint tools if Analyzer cannot produce safe upload strategy and patch_targets.
```

## Wildcard UI implication

Wildcards are user-facing workflow helper controls when the workflow/profile exposes them.

They may affect prompt construction, randomization, presets, or dynamic text expansion.

Possible controls:

```text
- wildcard ON/OFF
- wildcard category selector
- random wildcard option
- selected wildcard preview
- generated/expanded prompt preview when available
```

Rules:

```text
- Wildcards should be shown only when Analyzer or profile metadata identifies them.
- Wildcard expansion must not silently overwrite the user's prompt.
- If wildcard expansion changes the prompt sent to ComfyUI, the app should make that clear.
- If wildcard behavior depends on a custom node, missing-node warnings must be shown.
- If wildcard branch is bypass-OFF, wildcard controls are inactive.
```

## Subgraph UI implication

Subgraphs do not need to dominate the main screen.

But the app must still support:

```text
- showing that something is a subgraph
- expanding the subgraph on a separate/detail page
- listing internal node types
- exposing safe editable fields inside subgraphs
- marking unsupported or uncertain areas
```

The subgraph can be visually secondary, but its analysis cannot be secondary.

## Bypass UI implication

Bypass ON/OFF can live under Graph Controls or a node detail page.

But its state must still be clear.

Rules:

```text
- OFF/bypassed branches must look inactive.
- OFF/bypassed text or parameter fields are not active generation inputs.
- OFF/bypassed image upload, mask, paint, or wildcard controls are not active generation inputs.
- ON/OFF changes must update active/inactive controls immediately.
```

## Parameter UI implication

Common parameters should be easy to access when they exist:

```text
- negative prompt
- seed
- steps
- CFG
- denoise
- sampler
- scheduler
- guidance
- LoRA strength
- batch
```

But the app should only show them as active controls when Analyzer has safe patch_targets.

## Generated data review

Generated output review is a primary user task.

The app should support output review by output type:

```text
image -> preview / large preview / history
video -> file entry / preview when safe
audio -> file entry / playback when safe
text/json -> readable view or file entry
unknown/file -> safe file entry and warning
```

## Analyzer accuracy requirement

The Analyzer must prioritize correctness over UI simplicity.

Analyzer must know or safely report:

```text
- what inputs are active
- what inputs are bypass-OFF
- what fields are inside subgraphs
- what image uploads are required
- what mask/paint controls are required
- what wildcard controls exist
- what parameters are safe to edit
- what output type is produced
- what dependencies are required
- what is unknown or unsupported
```

## Product guardrail

```text
The app UI can stay simple.
The node graph can be hidden or secondary.
But Analyzer accuracy cannot be secondary.
A simple UI must be backed by exact patch_targets, exact execution-state awareness, correct upload/mask/wildcard handling, and clear warnings.
Visible and less-visible UI pages are only different views of one connected workflow graph.
```
