# App Capability Checks

## Purpose

This file records lightweight app-side capability checks that can run before generation.

These checks do not download models, install custom nodes, or modify workflows. They only read official ComfyUI API information and show status to the user.

## Current implementation status

```text
Implemented in:
mobile-app/flutter_mvp/lib/services/comfy_api_client.dart
mobile-app/flutter_mvp/lib/screens/setup_screen.dart
```

## Official APIs prepared

```text
GET /system_stats
GET /object_info
GET /models/{folder}
```

Flutter API client:

```text
ComfyApiClient.getSystemStats()
ComfyApiClient.getObjectInfo()
ComfyApiClient.getModels(folder: 'checkpoints')
```

## Setup screen connection check

Current sequence:

```text
1. Check ComfyUI URL is not empty.
2. GET /system_stats.
3. GET /object_info.
4. Try GET /models/checkpoints.
5. Save normalized URL if ComfyUI connection and object_info succeed.
6. Show node type count and checkpoint count.
```

Important behavior:

```text
/models/checkpoints failure does not fail the entire connection check.
```

Reason:

```text
The /models route can vary by ComfyUI version or configuration.
A working ComfyUI connection should not be rejected only because model listing is unavailable.
```

## What this proves

```text
/system_stats
  - ComfyUI server is reachable.

/object_info
  - ComfyUI node/runtime capability information is available.
  - This is also useful later for sampler/scheduler/LoRA/control metadata.

/models/checkpoints
  - Gives a lightweight checkpoint count when supported.
```

## Safety rules

```text
- Do not auto-download missing models.
- Do not auto-install missing custom nodes.
- Do not mark a workflow safe only because /object_info exists.
- Do not block all connection flows if /models is unavailable.
- Keep model existence checks read-only.
```

## Deferred until RunPod + Android validation

```text
- Compare workflow model names against /models output.
- Show missing model warnings in GenerateScreen.
- Detect missing custom nodes using /object_info and app_profile warnings.
- Build sampler/scheduler select options from /object_info.
- Build LoRA select options from /object_info or /models/loras if supported.
```

## Runtime validation checklist

During RunPod + Android validation, confirm:

```text
1. Setup screen can call /system_stats.
2. Setup screen can call /object_info.
3. Setup screen shows a reasonable node type count.
4. /models/checkpoints either returns count or fails without blocking connection.
5. URL is saved after successful connection.
6. No model download or custom node install is triggered.
```
