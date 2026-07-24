# App Queue and Error Controls

## Purpose

This file records app-side controls for official ComfyUI queue/status operations and user-friendly error messages.

These features use official ComfyUI APIs and do not change workflow patching rules.

## Current implementation status

```text
Implemented in:
mobile-app/flutter_mvp/lib/services/comfy_api_client.dart
mobile-app/flutter_mvp/lib/screens/generate_screen.dart
```

## Official APIs prepared

```text
GET  /queue
POST /interrupt
```

Flutter API client:

```text
ComfyApiClient.getQueue()
ComfyApiClient.interrupt()
```

## Generate screen controls

Current controls:

```text
Check queue
Interrupt
```

Check queue behavior:

```text
1. Calls GET /queue.
2. Reads queue_running and queue_pending when present.
3. Shows running/pending counts in the status line.
4. If ComfyUI response shape differs, falls back to 0 counts until Android/RunPod validation clarifies shape.
```

Interrupt behavior:

```text
1. Calls POST /interrupt.
2. Shows Interrupt sent when request succeeds.
3. Shows a friendly error if request fails.
```

## Friendly error handling

GenerateScreen now has a small `_friendlyError` helper.

Current behavior:

```text
Connection errors:
- Shows: Connection failed. Check the ComfyUI URL and whether the pod/server is running.

Prompt errors:
- Shows: Generation request failed. The workflow, model, or inputs may not match this ComfyUI environment.

Invalid JSON:
- Shows: ComfyUI returned an unexpected response.

Long raw errors:
- Truncated to avoid flooding the mobile screen.
```

## Safety rules

```text
- Do not auto-retry failed prompts without user action.
- Do not auto-interrupt on timeout.
- Do not mutate workflow.json directly.
- Do not bypass patch_targets.
- Keep /interrupt manual.
- Keep queue/interrupt validation pending until real RunPod + Android testing.
```

## Deferred until runtime validation

```text
- Confirm exact /queue response shape on current ComfyUI version.
- Show queue details beyond count.
- Add clear queue controls.
- Add interrupt confirmation dialog if accidental taps become a problem.
- Map ComfyUI node execution errors to exact UI fields.
```

## Runtime validation checklist

During RunPod + Android validation, confirm:

```text
1. Check queue works against real ComfyUI.
2. Queue running/pending counts are accurate.
3. Interrupt works during a real generation.
4. Interrupt does not crash the app when nothing is running.
5. Friendly connection errors appear for a stopped/invalid URL.
6. Friendly prompt errors appear for missing model/custom node mismatch.
7. History timeout message is understandable.
```
