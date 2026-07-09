# Existing Platforms Review

## Purpose

This file records what ComfyUI and RunPod already provide, so this project does not rebuild existing platform features unnecessarily.

The goal is to keep the project focused on what is actually missing:

```text
mobile profile generation
smartphone-friendly UI
safe patch_targets-only editing
profile zip export/download
beginner-friendly operation
```

## High-level conclusion

```text
A complete mobile profile system is not already provided.

However:
- ComfyUI already provides most of the generation API foundation.
- RunPod already provides most of the GPU hosting and operational foundation.
- This project should focus on the missing mobile-friendly layer.
```

## ComfyUI official foundation

Official source:

```text
https://docs.comfy.org/development/comfyui-server/comms_routes
https://docs.comfy.org/development/comfyui-server/api-examples
```

### ComfyUI routes that directly support this project

ComfyUI already provides these routes:

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

### Already covered by ComfyUI

These should not be treated as unique custom work unless the project adds a mobile-specific layer on top:

```text
- Submit API-format workflows.
- Monitor generation progress.
- Read generation history.
- Retrieve generated images.
- Upload input images and masks.
- Retrieve node type metadata.
- Retrieve available model folders and models.
- Add custom routes through ComfyUI PromptServer.
```

### Important official API behavior

ComfyUI posts workflow execution requests to `/prompt`. It validates the prompt, queues it, and returns either `prompt_id`/queue number or validation errors.

ComfyUI `/ws` provides real-time messages such as:

```text
status
execution_start
execution_cached
executing
progress
executed
```

The recommended official pattern for most API clients is:

```text
1. Export workflow in API format.
2. POST workflow to /prompt with client_id.
3. Connect to /ws?clientId=...
4. Wait for executing node == null for the matching prompt_id.
5. GET /history/{prompt_id}.
6. GET /view for each output image.
```

This matches the current Flutter MVP direction.

## ComfyUI official APIs that should change our priority

### 1. /object_info should become more important

This project should not manually guess all node input types forever.

`/object_info` and `/object_info/{node_class}` can provide node metadata.

Future Analyzer should use this to improve:

```text
- field type detection
- combo option detection
- required/optional input detection
- custom node compatibility checks
- safer UI generation
```

### 2. /models and /models/{folder} should be used for model checks

The Analyzer should not only parse model names from workflow JSON.

It should compare detected model references against ComfyUI's model list routes.

Use cases:

```text
- checkpoint existence check
- LoRA existence check
- VAE existence check
- model folder availability
- beginner-friendly missing model warnings
```

### 3. /workflow_templates may be useful later

`/workflow_templates` can support later template discovery or example profile creation.

It is not MVP-critical.

## What ComfyUI does not provide

ComfyUI does not appear to provide this full mobile product layer out of the box:

```text
- smartphone-friendly profile zip export
- app_profile.json contract
- automatic extraction of only important mobile fields
- patch_targets-only safe editing policy
- mobile UI schema
- local mobile profile storage
- beginner-friendly profile list/download flow
```

This remains this project's core value.

## RunPod official foundation

Official sources:

```text
https://docs.runpod.io/pods/overview
https://docs.runpod.io/serverless/endpoints/send-requests
```

### RunPod Pods

RunPod Pods provide on-demand GPU/CPU resources and allow control over software, storage, and networking.

Useful official Pod capabilities:

```text
- GPU hosting for ComfyUI
- web proxy for exposed web services
- SSH access
- JupyterLab access
- VS Code/Cursor access
- templates
- custom containers
- storage options
```

This matches the current near-term direction:

```text
RunPod Pod
  ↓
ComfyUI
  ↓
Smartphone app connects to ComfyUI URL
```

### RunPod Serverless

RunPod Serverless queue-based endpoints support:

```text
/runsync
/run
/status
/stream
/cancel
/retry
/purge-queue
/health
```

Serverless may be useful later, but it should not replace Pods for the current validation stage.

Why Pods remain first:

```text
- ComfyUI UI is still useful during workflow/profile creation.
- Analyzer custom node needs ComfyUI runtime validation.
- The current goal is not pure black-box inference yet.
- Smartphone app still connects directly to ComfyUI server APIs.
```

Serverless becomes more attractive later if the product changes to:

```text
Smartphone app
  ↓
RunPod Serverless endpoint
  ↓
ComfyUI worker
  ↓
Result only
```

## What RunPod does not provide

RunPod does not provide the mobile profile system itself.

It provides hosting and endpoint operation, not:

```text
- workflow analysis
- app_profile.json
- mobile UI generation
- patch_targets-only workflow editing
- beginner-friendly ComfyUI workflow operation
```

## Project role after this review

The project should become less of a full custom workflow runner and more of a translation/adaptation layer:

```text
ComfyUI official APIs
  ↓
ComfyUI-Mobile-Analyzer
  ↓
mobile app profile contract
  ↓
Flutter smartphone UI
```

Better wording:

```text
The Analyzer is not a complete replacement for ComfyUI internals.
The Analyzer translates official ComfyUI runtime information into a safe mobile profile.
```

## Priority adjustment

### S rank: prove official runtime flow

```text
/prompt
/ws
/history/{prompt_id}
/view
/upload/image
/system_stats
```

### A rank: use official metadata APIs

```text
/object_info
/object_info/{node_class}
/models
/models/{folder}
```

### B rank: later ComfyUI/RunPod platform features

```text
/workflow_templates
/userdata
/queue
/interrupt
/free
RunPod Serverless /run and /status
RunPod cached models
custom containers
```

### C rank: not now

```text
ComfyUI Cloud API
ComfyUI Manager publication
RunPod Serverless production architecture
full workflow portal behavior
```

## Key decision

Do not throw away the current system.

Do change the emphasis:

```text
Before:
Analyzer manually detects workflow fields as much as possible.

After:
Analyzer uses ComfyUI official APIs where available, and only adds the mobile-specific profile layer that ComfyUI does not provide.
```

## Claude handoff implication

The Claude handoff should be updated.

Instead of only asking Claude to run runtime validation, Claude should first perform a short architecture alignment check:

```text
1. Review current system.
2. Review official ComfyUI routes that overlap with our custom work.
3. Confirm whether /object_info and /models should be moved earlier.
4. Confirm which current custom Analyzer routes are still necessary.
5. Only then run runtime validation or make minimal corrections.
```
