# UI Priority and Analyzer Accuracy Principle

## Purpose

This file records the current product thinking about smartphone app UI and Analyzer priority.

The UI is not fixed yet.

However, the most important user-facing operations are clear:

```text
1. Enter or edit prompts.
2. Review generated data.
3. Change needed parameters.
```

Everything else can be secondary, hidden, collapsed, or moved to another page if needed.

## Core UI direction

The smartphone app does not need to expose the whole workflow graph as the main screen.

The main generation screen should focus on:

```text
- prompt input
- negative prompt when available
- required input files such as image/mask/video/audio
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
- important inputs
- important parameters
- generated output

Advanced page:
- detailed parameter groups
- LoRA / ControlNet / FaceDetailer / inpaint / mask controls

Graph / Node page:
- node list
- subgraph expansion
- bypass ON/OFF controls
- execution state
- warnings
- raw analyzer report
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
A simple UI must be backed by exact patch_targets, exact execution-state awareness, and clear warnings.
```
