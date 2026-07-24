# Project Direction Guardrails

## Purpose

This file protects the original direction of the ComfyUI Mobile System project.

External repositories, examples, tools, and ideas may be studied, but they must not change the core goal of this project.

## Core direction

The project direction is:

```text
Use ComfyUI to analyze workflows,
export a safe mobile profile,
let a smartphone app edit only the main allowed parameters,
submit the patched workflow back to ComfyUI,
and display the generated result.
```

## What this project is

```text
A smartphone-friendly execution layer for ComfyUI workflows.
```

It should help the user:

```text
- Connect to ComfyUI from a phone.
- Download analyzed workflow profiles from ComfyUI.
- Open profiles in a mobile app.
- Edit only safe, important parameters.
- Generate images without using the full ComfyUI desktop UI.
```

## What this project is not

```text
- Not a full ComfyUI replacement.
- Not a full workflow editor.
- Not a ComfyUI Manager replacement.
- Not an automatic custom node installer.
- Not an automatic model downloader.
- Not a cloud sync product yet.
- Not a project that depends on another repository as its core identity.
```

## External reference rule

External repositories can be used as references only.

```text
External references may inform design.
They must not define the product direction.
```

For example, `comfy-portal-endpoint` may be useful as a reference for UI workflow to API workflow conversion, but it must not turn this project into a general ComfyUI workflow management server.

## Anti-drift rules

Do not allow external references to shift the project into:

```text
- A full REST API clone of another project.
- A full workflow storage server.
- A browser automation project first.
- A Playwright/Chromium-first system.
- A generic ComfyUI portal.
- A desktop-first tool.
- A tool that requires heavy dependencies before the mobile MVP is proven.
```

## Decision priority

When choosing between approaches, prioritize in this order:

```text
1. Smartphone usability.
2. Safe workflow patching.
3. Minimal runtime path.
4. Compatibility with ComfyUI.
5. Clear user control.
6. Low-cost RunPod operation.
7. Extensibility after MVP proof.
```

## Allowed influence from external projects

External projects may influence:

```text
- Endpoint naming ideas.
- Conversion strategy ideas.
- Runtime validation ideas.
- Edge case awareness.
- API response shape ideas.
- Documentation structure.
```

External projects must not override:

```text
- app_profile.json as the shared contract.
- patch_targets-only editing.
- preserving original workflows.
- no automatic installs before user approval.
- no automatic downloads before user approval.
- Android-first Flutter MVP.
- Claude runtime validation before feature expansion.
```

## Current stance on comfy-portal-endpoint

```text
Use as reference only.
Do not integrate into the current PR.
Do not copy code.
Do not make Playwright/Chromium a required dependency for the MVP.
Study the UI workflow conversion idea after runtime validation.
If needed, implement our own version from our own requirements.
```

## One-sentence guardrail

```text
Do not let reference projects change the goal: this is a mobile-first ComfyUI workflow execution system, not a clone of another workflow portal.
```
