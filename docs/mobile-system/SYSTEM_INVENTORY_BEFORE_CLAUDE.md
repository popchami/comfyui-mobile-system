# System Inventory Before Claude Handoff

## Purpose

This file compares three systems before handing the PR to Claude:

```text
1. Current ComfyUI Mobile System
2. External reference: comfy-portal-endpoint
3. Official platform capabilities: ComfyUI and RunPod
```

The goal is to avoid building unnecessary custom functionality and to keep the project focused before implementation hardens.

## 1. Current ComfyUI Mobile System

### Current goal

```text
ComfyUI workflow
  ↓
ComfyUI-Mobile-Analyzer
  ↓
mobile profile zip
  ↓
Flutter smartphone app
  ↓
patch allowed fields only
  ↓
submit to ComfyUI
  ↓
show generated image
```

### Current strengths

```text
- Mobile-first direction is clear.
- app_profile.json exists as a shared contract.
- patch_targets-only editing rule exists.
- Original workflow preservation rule exists.
- Profile zip idea is clear.
- Flutter MVP already follows /prompt → /ws → /history → /view direction.
- Analyzer custom route idea is aligned with ComfyUI custom routes.
```

### Current weaknesses

```text
- Analyzer still manually guesses many field types.
- /object_info is not yet used.
- /models and /models/{folder} are not yet used.
- UI workflow to API workflow conversion is not implemented.
- Runtime validation is not complete.
- SharedPreferences storage is temporary.
- Error handling is basic.
```

### Keep

```text
- app_profile.json
- patch_targets
- mobile_profile_export.zip
- Flutter Android-first MVP
- profile download from ComfyUI
- no automatic installs
- no automatic model downloads
- workflow preservation rules
```

### Reconsider before implementation hardens

```text
- Move /object_info support earlier.
- Move /models support earlier.
- Decide whether UI conversion should be optional.
- Confirm which custom routes are needed beyond official ComfyUI APIs.
```

## 2. External reference: comfy-portal-endpoint

Repository:

```text
https://github.com/ShunL12324/comfy-portal-endpoint
```

### Useful concepts

```text
- UI workflow to API workflow conversion using the real ComfyUI frontend.
- /health endpoint for converter readiness.
- Dedicated /convert endpoint.
- get-and-convert flow.
- Cold start awareness.
- Custom node compatibility through frontend conversion.
```

### Do not copy

```text
- Code.
- Project identity.
- Full workflow portal direction.
- Playwright/Chromium as MVP-required dependency.
- Automatic dependency installation behavior.
```

### Best use in this project

```text
Optional UI Converter reference after core runtime validation.
```

### Risk if overused

```text
This project may drift into a generic ComfyUI workflow management server instead of staying mobile-first.
```

## 3. Official ComfyUI capabilities

Official routes include:

```text
/ws
/prompt
/history
/history/{prompt_id}
/view
/upload/image
/upload/mask
/system_stats
/object_info
/object_info/{node_class}
/models
/models/{folder}
/workflow_templates
/queue
/interrupt
/free
/userdata
```

### Should be used directly

```text
/prompt
/ws
/history/{prompt_id}
/view
/upload/image
/system_stats
```

These are already aligned with the Flutter MVP.

### Should be promoted earlier

```text
/object_info
/object_info/{node_class}
/models
/models/{folder}
```

These can reduce manual guessing in Analyzer.

### Later support

```text
/workflow_templates
/userdata
/queue
/interrupt
/free
```

Useful, but not MVP blockers.

### Important design correction

The Analyzer should not become a replacement for ComfyUI internals.

Better role:

```text
Use official ComfyUI runtime information,
then translate it into a safe smartphone profile.
```

## 4. Official RunPod capabilities

### Pods

Useful for current phase:

```text
- GPU hosting
- web proxy
- SSH
- JupyterLab
- VS Code/Cursor
- templates
- custom containers
- storage options
```

Pods are still the correct near-term target because ComfyUI itself remains visible and testable.

### Serverless

Useful later:

```text
/runsync
/run
/status
/stream
/cancel
/health
```

Serverless is not the current MVP target.

Possible later architecture:

```text
Smartphone app
  ↓
RunPod Serverless endpoint
  ↓
ComfyUI worker
  ↓
result only
```

## 5. What exists vs what must be built

### Already exists in ComfyUI

```text
- workflow execution API
- progress websocket
- history retrieval
- image retrieval
- image/mask upload
- node metadata API
- model listing API
- custom route support
```

### Already exists in RunPod

```text
- GPU compute
- web access
- templates
- storage choices
- serverless jobs
- endpoint health/status patterns
```

### Still must be built by this project

```text
- mobile profile schema
- profile zip export/download UX
- safe field extraction
- safe patch_targets-only editing
- smartphone UI generation
- beginner-friendly missing model/node display
- profile save/open/re-run behavior
```

## 6. Recommended Claude handoff change

The Claude handoff should change from:

```text
Run runtime validation immediately.
```

to:

```text
First perform architecture inventory and official API alignment.
Then run runtime validation.
```

Claude should explicitly answer:

```text
1. Which current custom logic duplicates official ComfyUI APIs?
2. Should /object_info be implemented before deeper field detection?
3. Should /models be implemented before model warning logic expands?
4. Should UI workflow conversion remain optional for now?
5. What is the minimum blocker-free path to validate current MVP?
```

## 7. Final direction after inventory

The direction does not change.

The implementation strategy does change:

```text
Do not build everything from scratch.
Use ComfyUI and RunPod foundations first.
Build only the missing mobile profile layer.
```
