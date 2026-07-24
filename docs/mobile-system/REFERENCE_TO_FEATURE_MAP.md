# Reference to Feature Map

## Purpose

This file explains each reference area in beginner-friendly terms and maps it to the features it can influence.

This is not an implementation plan. It is a bridge between reference study and future feature design.

## Timing rule

```text
Do not implement features from this file before RunPod GPU + Android real-device validation passes.
```

## 1. Official ComfyUI server/API behavior

### What it is

ComfyUI already has server APIs for generation, progress, image upload, image viewing, model lists, node information, queue handling, and interruption.

### Main API features

```text
/prompt
  Start generation.

/ws
  Watch generation progress.

/history/{prompt_id}
  Get generation result information.

/view
  Fetch or display generated images.

/upload/image
  Send input images to ComfyUI.

/upload/mask
  Send masks for inpaint/mask workflows.

/system_stats
  Check whether ComfyUI is reachable.

/object_info
  Get node class and input metadata.

/models
  Get available model categories or model files.

/queue
  Check queue state.

/interrupt
  Stop running generation.
```

### How it affects this project

```text
- The Android app should use official ComfyUI APIs directly where possible.
- The Analyzer should not duplicate official ComfyUI functions.
- Custom routes should only cover the missing mobile profile layer.
```

### Future features influenced

```text
- Connection check
- Generation submit
- Progress display
- Image upload
- Generated image display
- Model existence check
- Node metadata detection
- Queue view
- Cancel/interrupt generation
```

### Do not do

```text
- Do not create custom endpoints that duplicate official APIs.
- Do not depend on internal frontend behavior unless needed.
```

## 2. Official ComfyUI API workflow examples

### What it is

These examples show the correct API-format workflow JSON shape and how to submit it to ComfyUI.

### Main ideas

```text
- API workflow JSON is what /prompt expects.
- /prompt should include client_id.
- /ws should use the same client_id.
- /history/{prompt_id} tells where output images are.
- /view fetches the actual image file.
```

### How it affects this project

```text
The Android app should not act like a full ComfyUI UI graph editor. It should load an API workflow, patch only safe values, submit it, then display the output.
```

### Future features influenced

```text
- WorkflowPatcher rules
- patch_targets safety
- generated image lookup
- retry behavior
- debug report export
- generation history
```

### Do not do

```text
- Do not require users to manually paste workflow JSON into the Android app.
- Do not patch arbitrary fields outside patch_targets.
```

## 3. comfy-portal-endpoint

### What it is

An external project that can be studied for workflow endpoint design and UI workflow to API workflow conversion ideas.

### Main ideas to study

```text
- UI workflow to API workflow conversion concept
- Use of ComfyUI frontend graphToPrompt concept
- Health/readiness endpoints
- Dedicated convert endpoint
- Cold start/readiness handling
- Separation of list/get/save/convert behavior
```

### How it affects this project

```text
It may help design an optional converter later if UI-format workflow import becomes important.
```

### Future features influenced

```text
- Optional UI workflow import/conversion
- Readiness check
- Health check
- Workflow conversion status
- Better Analyzer route design
```

### Do not do

```text
- Do not copy code.
- Do not make Playwright/Chromium required for MVP.
- Do not turn this project into a generic workflow portal.
- Do not depend on comfy-portal-endpoint as part of the product identity.
```

## 4. RunPod Pods behavior

### What it is

RunPod Pods are the current expected environment where ComfyUI runs with GPU.

### Main behavior to study

```text
- Pod start/stop lifecycle
- Web/proxy URL behavior
- SSH/Jupyter access
- Template/container behavior
- Terminate operation
- Network Volume 0GB behavior
- GPU selection
- startup/cold start time
- temporary storage behavior
```

### How it affects this project

```text
The Android app must treat the RunPod ComfyUI URL as session-based and should not assume files remain forever after termination.
```

### Future features influenced

```text
- RunPod URL history
- Connection screen warnings
- Cost awareness notes
- Re-upload image behavior
- Session notes
- Debug report export
- Profile re-run reliability
```

### Do not do

```text
- Do not claim the app can start/stop RunPod unless implemented later.
- Do not auto-download models to make setup easier.
- Do not store generated images in cloud by default.
```

## 5. RunPod Serverless

### What it is

A possible future RunPod execution model where generation is called through serverless endpoints instead of manually running a Pod.

### Main behavior to study

```text
/run
/runsync
/status
/stream
/health
worker cold start
request/response payload constraints
persistent storage limitations
```

### How it affects this project

```text
Serverless may become useful later if the profile system becomes stable enough to package generation requests cleanly.
```

### Future features influenced

```text
- Production backend option
- Cleaner mobile app connection flow
- Job status polling
- Streamed result handling
- Cost model changes
```

### Do not do

```text
- Do not switch MVP to Serverless now.
- Do not design the Android app around Serverless before Pod validation.
- Do not hide ComfyUI before the profile flow is proven.
```

## 6. ComfyUI Manager / custom node management patterns

### What it is

ComfyUI Manager helps users manage custom nodes. This project should not replace it, but can learn how missing custom nodes appear and how users repair them.

### Main behavior to study

```text
- How custom nodes are identified.
- How missing nodes appear in workflows.
- How dependency warnings are displayed.
- How users manually install/repair missing nodes.
```

### How it affects this project

```text
The app should clearly report missing custom nodes and guide the user, but not install them automatically.
```

### Future features influenced

```text
- custom node existence reporting
- needs_attention warnings
- preflight check
- debug report export
- profile compatibility status
```

### Do not do

```text
- Do not become ComfyUI Manager.
- Do not auto-install custom nodes.
- Do not run arbitrary shell commands from the Android app.
```

## 7. Civitai workflow/model sharing behavior

### What it is

Civitai is a place where models and sometimes workflows are shared. It may be a source of user workflows and model requirements later.

### Main behavior to study

```text
- How workflows are shared.
- Whether metadata includes required models.
- How LoRA/VAE/checkpoint requirements are represented.
- Licensing concerns.
- NSFW concerns.
```

### How it affects this project

```text
The app may later help import or analyze workflows from Civitai, but should start with manual import and missing requirement warnings.
```

### Future features influenced

```text
- workflow import
- model requirement warnings
- LoRA/VAE detection
- NSFW/cloud storage safety
- profile compatibility warnings
```

### Do not do

```text
- Do not auto-download Civitai models.
- Do not create a public marketplace in MVP.
- Do not sync NSFW outputs to cloud by default.
```

## 8. GitHub workflow/profile storage patterns

### What it is

GitHub can be used as a structured place to store example workflows, app_profile examples, issue templates, and versioned specs.

### Main behavior to study

```text
- raw workflow file import
- repository file organization
- versioned profile examples
- compatibility bug issue templates
```

### How it affects this project

```text
GitHub can help organize reference workflows and examples, but normal app usage should not require GitHub.
```

### Future features influenced

```text
- example profile library
- import/export profile examples
- workflow compatibility bug reporting
- debug report template
- versioned app_profile examples
```

### Do not do

```text
- Do not require GitHub login for normal app usage.
- Do not fetch arbitrary URLs automatically.
```

## 9. Android local storage and backup patterns

### What it is

This is about how Android apps should safely store local profile data, workflow files, preview images, and backups.

### Main behavior to study

```text
- app-local files
- backup/export zip format
- Android scoped storage
- user-controlled delete/export
- privacy defaults
```

### How it affects this project

```text
Profiles and generated images should be stored locally by default, with explicit export and easy deletion.
```

### Future features influenced

```text
- production-safe profile storage
- profile backup/export
- generated history
- preview images
- local-only safety mode
- storage cleanup
```

### Do not do

```text
- Do not enable automatic cloud sync by default.
- Do not keep unlimited generation history without user control.
```

## 10. Prompt preset / style preset patterns

### What it is

This is about helping non-expert users generate better prompts without editing raw JSON or complex node settings.

### Main behavior to study

```text
- prompt fragment presets
- positive/negative prompt pairing
- profile-specific presets
- last-used values
```

### How it affects this project

```text
The app can later provide simple profile-specific prompt presets such as product photo, pixel art, icon style, realistic lighting, or cute style.
```

### Future features influenced

```text
- prompt presets per profile
- last-used values
- lightweight prompt builder
- positive/negative prompt pairing
```

### Do not do

```text
- Do not turn the app into a generic prompt marketplace.
- Do not overwrite original profile defaults.
```

## Study order

After RunPod + Android validation passes, study in this order:

```text
1. Official ComfyUI server/API behavior
2. Official ComfyUI API workflow examples
3. RunPod Pods behavior
4. /object_info and /models details
5. ComfyUI Manager missing-node patterns
6. comfy-portal-endpoint conversion design
7. Civitai workflow/model sharing behavior
8. GitHub profile/workflow storage patterns
9. Android local storage and backup patterns
10. Prompt/style preset patterns
11. RunPod Serverless
```

## Summary

```text
ComfyUI official references
  = use official APIs correctly and avoid duplicate custom code

comfy-portal-endpoint
  = optional UI workflow conversion reference

RunPod references
  = real operation, URL, storage, cost, session behavior

ComfyUI Manager / Civitai / GitHub references
  = missing requirements, workflow sharing, examples, issue templates

Android storage / prompt presets
  = app usability, local safety, beginner-friendly generation
```
