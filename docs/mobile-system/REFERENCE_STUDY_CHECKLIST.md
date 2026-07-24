# Reference Study Checklist

## Purpose

This file defines what to check when studying each reference area.

Use this after RunPod GPU + Android real-device validation passes, or when one of these topics becomes a blocker.

## Rule

```text
Study first. Then decide. Then implement only the minimum needed.
```

Do not use reference study as a reason to rewrite the project before MVP validation.

## 1. Official ComfyUI server/API behavior checklist

### Goal

Confirm how the Android app and Analyzer should use official ComfyUI APIs without duplicating them.

### Check items

```text
- /prompt payload shape
- /prompt response shape
- /ws connection format
- /ws message types
- /history/{prompt_id} output image structure
- /view required query parameters
- /upload/image request/response shape
- /upload/mask request/response shape
- /system_stats response shape
- /object_info response shape
- /object_info/{node_class} response shape
- /models response shape
- /models/{folder} response shape
- /queue response shape
- /interrupt behavior and scope
```

### Decision output

```text
- Which official APIs are already enough.
- Which custom Analyzer routes are still necessary.
- Which custom routes should not be added.
```

## 2. Official ComfyUI API workflow examples checklist

### Goal

Confirm the exact workflow format that the Android app should patch and submit.

### Check items

```text
- Minimal text-to-image API workflow
- Image-to-image workflow with LoadImage
- Inpaint/mask workflow if needed
- KSampler positive/negative links
- EmptyLatentImage width/height/batch structure
- SaveImage output lookup through history
- client_id usage
- whether prompt_id is always returned
```

### Decision output

```text
- Minimal workflow examples to keep in repo.
- What patch_targets should look like for common fields.
- Which workflow shapes are unsupported for MVP.
```

## 3. RunPod Pods behavior checklist

### Goal

Confirm the operational assumptions for using ComfyUI from Android.

### Check items

```text
- Does the ComfyUI URL change after Pod restart?
- Does the proxy URL require special path/port handling?
- What files persist after Terminate with Network Volume 0GB?
- Where are ComfyUI input/output folders located?
- Are uploaded images preserved across restart/terminate?
- How long does ComfyUI cold start take?
- How should the user know when to stop the Pod?
- Which GPU/test model is used for validation?
```

### Decision output

```text
- URL handling rules.
- Re-upload image rules.
- Cost warning wording.
- Storage persistence assumptions.
```

## 4. /object_info and /models checklist

### Goal

Design Analyzer metadata improvements based on live ComfyUI runtime information.

### Check items

```text
- What node input types are returned by /object_info?
- How are COMBO choices represented?
- Are min/max/default values available?
- How do custom nodes appear?
- What does /models return for checkpoints?
- What does /models return for LoRA, VAE, ControlNet, upscale models?
- How do missing models appear at generation time?
```

### Decision output

```text
- input_metadata shape.
- model_checks shape.
- warning codes.
- preflight check behavior.
```

## 5. ComfyUI Manager / missing custom node checklist

### Goal

Learn how to report missing custom node problems without installing anything automatically.

### Check items

```text
- How missing nodes appear when loading a workflow.
- Whether class_type is enough to identify missing nodes.
- What info a user needs to manually fix missing nodes.
- How dependency errors appear in ComfyUI logs/UI.
```

### Decision output

```text
- custom node warning format.
- debug report fields.
- user-facing guidance wording.
```

## 6. comfy-portal-endpoint checklist

### Goal

Study UI workflow conversion and endpoint separation as reference only.

### Check items

```text
- How UI workflow is converted to API workflow.
- What graphToPrompt depends on.
- Whether conversion needs frontend/runtime context.
- How health/readiness is represented.
- Whether cold start state is useful for this app.
- Which endpoint separation ideas are useful.
```

### Decision output

```text
- Whether optional UI workflow conversion is worth adding later.
- Whether a conversion endpoint should exist.
- Which dependencies are unacceptable for MVP.
```

### Hard rule

```text
Do not copy code.
Do not make Playwright/Chromium required.
```

## 7. Civitai workflow/model sharing checklist

### Goal

Understand how external workflows and model requirements are shared.

### Check items

```text
- Can workflows be downloaded manually?
- What metadata identifies required checkpoint/LoRA/VAE?
- Are licenses visible enough for the user?
- How is NSFW content marked?
- Is there a stable way to warn about missing requirements?
```

### Decision output

```text
- Manual import rules.
- Missing model warning behavior.
- NSFW/cloud sync safety wording.
```

### Hard rule

```text
Do not auto-download models.
Do not build a public marketplace for MVP.
```

## 8. GitHub workflow/profile storage checklist

### Goal

Use GitHub for examples/specs/issues without making it required for normal users.

### Check items

```text
- How to organize example workflows.
- How to version app_profile examples.
- What issue template is useful for compatibility bugs.
- Whether raw workflow files can be manually imported later.
```

### Decision output

```text
- example profile folder structure.
- issue template draft.
- compatibility report format.
```

## 9. Android local storage and backup checklist

### Goal

Decide safe local storage for profiles, workflows, previews, and histories.

### Check items

```text
- shared_preferences size/shape limits in practice.
- app-local file storage API choice.
- backup zip structure.
- delete/export UX.
- Android scoped storage implications.
- privacy defaults.
```

### Decision output

```text
- final profile storage design.
- backup/export structure.
- history retention policy.
```

## 10. Prompt/style preset checklist

### Goal

Design beginner-friendly prompt helpers without changing profile defaults.

### Check items

```text
- profile-specific presets
- positive/negative pairing
- last-used prompt values
- reset to default behavior
- preset apply vs append behavior
```

### Decision output

```text
- prompt preset data shape.
- last-used values storage shape.
- UX wording.
```

## 11. RunPod Serverless checklist

### Goal

Evaluate Serverless only after Pod-based MVP works.

### Check items

```text
- /run request shape
- /runsync behavior
- /status polling
- /stream support
- /health behavior
- cold start expectations
- file/model persistence constraints
- output image retrieval pattern
```

### Decision output

```text
- keep Pod-only
- add optional Serverless mode later
- defer indefinitely
```

## Study completion rule

Each study should end with:

```text
- What we learned
- What we will adopt
- What we will not adopt
- Which doc/spec changes are needed
- Which GitHub Issue should be opened later
```

## Recommended first study set

Do these first after RunPod + Android validation:

```text
1. Official ComfyUI server/API behavior
2. Official ComfyUI API workflow examples
3. RunPod Pods behavior
4. /object_info and /models checklist
```

Reason:

```text
These directly affect the core generation path and Analyzer accuracy.
```
