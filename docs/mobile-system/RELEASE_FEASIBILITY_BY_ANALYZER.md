# Release Feasibility by Analyzer Accuracy

## Purpose

This file records the current product judgment:

```text
The system is complex, but the user already owns the completed workflow/data.
If analysis and safe patching work well, release becomes realistic.
```

The product does not need to create every generation workflow.

The product needs to make existing user workflows safely usable from a smartphone.

## Core thesis

```text
The user's workflow is the completed generation asset.
The Analyzer is the bridge.
The smartphone app is the safe control surface.
```

Correct flow:

```text
User owns a working ComfyUI workflow
  ↓
Analyzer reads and preserves it
  ↓
Analyzer identifies safe controls
  ↓
Analyzer writes exact patch_targets
  ↓
Smartphone app renders those controls
  ↓
Smartphone app patches only those targets
  ↓
ComfyUI official API runs the workflow
  ↓
User reviews generated output
```

## What this means for release

The first releasable version does not need to support every possible workflow.

It needs to do two things very well:

```text
1. Supported workflows run safely.
2. Unsupported workflows fail safely without corruption.
```

This is enough for a practical release path.

## Release-critical areas

The release quality depends mostly on:

```text
- preserving workflow.json exactly
- detecting editable inputs correctly
- generating correct patch_targets
- detecting active vs bypass-OFF areas
- detecting subgraph context when relevant
- detecting output type and fetch strategy
- showing clear warnings for unsupported/unknown areas
- never pretending uncertainty is safe
```

## UI vs Analyzer priority

The UI can improve after release.

Analyzer safety cannot be weak at release.

```text
UI 70% complete may be acceptable.
Analyzer 70% correct is dangerous.
```

Reason:

```text
A rough UI is inconvenient.
A wrong Analyzer changes the wrong node, hides the wrong input, or corrupts the workflow.
```

## Safe release model

The system can release with limited workflow support if it has strict compatibility boundaries.

Example release behavior:

```text
Supported profile
- import succeeds
- controls are shown
- generation works
- output is shown

Partially supported profile
- core controls may work
- unsupported parts are clearly marked
- risky controls are not exposed

Unsupported profile
- workflow is preserved
- app shows why it cannot safely run/edit
- no unsafe patching happens
```

## What counts as success

A release candidate should prove:

```text
- at least one real user-provided workflow can be analyzed
- generated app_profile.json is valid
- patch_targets are correct
- smartphone app can edit exposed fields
- RunPod ComfyUI can generate from the patched workflow
- generated output can be reviewed
- unsupported fields stay inactive or warning-only
```

## What must not happen

```text
- Do not release if unsupported workflows are silently treated as supported.
- Do not release if patch_targets can point to the wrong node.
- Do not release if bypass-OFF fields appear as active inputs.
- Do not release if subgraph fields lose their context.
- Do not release if output type is guessed incorrectly as image.
- Do not release if the app mutates the workflow outside patch_targets.
```

## Product guardrail

```text
The product value is not workflow creation.
The product value is safe smartphone control of completed ComfyUI workflows.
If Analyzer accuracy is strong and unsupported cases fail safely, release is realistic even if the UI is still simple.
```
