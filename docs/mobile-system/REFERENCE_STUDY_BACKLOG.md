# Reference Study Backlog

## Purpose

This file records external and official reference materials that should be studied later.

This is different from feature ideas. These references are inputs for better design decisions after the current MVP validation path is proven.

## Timing rule

```text
Do not integrate, copy, or depend on these references before RunPod GPU + Android validation passes.
```

Allowed now:

```text
- Record what each reference is useful for.
- Record what should be adopted as an idea.
- Record what should not be copied or made mandatory.
- Record when it should be studied.
```

Not allowed now:

```text
- Copy external code.
- Add heavy dependencies.
- Change product identity.
- Turn this project into a full workflow portal.
- Turn this project into ComfyUI Manager.
```

## Reference priority overview

```text
S: Must keep aligned with this project
A: Study soon after validation
B: Study when expanding compatibility
C: Later reference only
```

## S reference 1: Official ComfyUI server/API behavior

### Why it matters

The mobile system should not reimplement ComfyUI features that already exist.

### Study focus

```text
- /prompt
- /ws
- /history/{prompt_id}
- /view
- /upload/image
- /upload/mask
- /system_stats
- /object_info
- /object_info/{node_class}
- /models
- /models/{folder}
- /queue
- /interrupt
```

### Adopt as design principle

```text
Use official ComfyUI APIs as source-of-truth wherever possible.
The custom Analyzer should focus on translating workflow/API/runtime information into a mobile-safe profile.
```

### Do not do

```text
Do not build duplicate custom endpoints for things official ComfyUI already provides.
Do not make the mobile app depend on ComfyUI internal frontend details unless necessary.
```

### When to revisit

```text
Immediately after RunPod validation, before implementing /object_info or /models support.
```

## S reference 2: Official ComfyUI API workflow examples

### Why it matters

The mobile app submits API-format workflows, not full UI graph editor data.

### Study focus

```text
- API workflow JSON shape
- client_id usage
- /prompt payload shape
- WebSocket progress monitoring
- /history output image lookup
- /view image fetch parameters
```

### Adopt as design principle

```text
Use the same client_id for /prompt and /ws.
Submit a generation copy of workflow JSON.
Read images from /history and fetch through /view.
```

### Do not do

```text
Do not require the user to manually paste JSON into the Android app.
Do not patch arbitrary workflow fields outside patch_targets.
```

### When to revisit

```text
During RunPod GPU image-generation validation.
```

## A reference 3: comfy-portal-endpoint

### Why it matters

This project previously identified comfy-portal-endpoint as useful reference for UI workflow to API workflow conversion and endpoint design.

### Study focus

```text
- UI workflow to API workflow conversion concept
- Use of ComfyUI frontend graphToPrompt concept
- Separate health/readiness endpoint idea
- Separate convert endpoint idea
- Cold start/readiness handling
- Workflow list/get/save/convert separation
```

### Adopt as ideas only

```text
- A converter should be optional.
- Conversion should be separated from normal generation.
- Health/readiness state is useful.
- Cold start state should be explicit.
```

### Do not do

```text
Do not copy code.
Do not make Playwright/Chromium required for MVP.
Do not shift this project into a generic ComfyUI workflow portal.
Do not make this project depend on comfy-portal-endpoint identity.
```

### When to revisit

```text
After API-format workflow validation passes and if UI-format workflow import becomes a real blocker.
```

## A reference 4: RunPod Pods behavior

### Why it matters

The current product direction is RunPod ComfyUI + Android app. RunPod behavior affects URL handling, storage, startup, and cost.

### Study focus

```text
- Pod lifecycle
- Web/proxy URL behavior
- SSH/Jupyter access if needed
- Template/container behavior
- Storage behavior with terminate operation
- Network Volume 0GB implications
- GPU selection
- Startup time and cold start behavior
```

### Adopt as design principle

```text
Treat RunPod URL as session-dependent.
Do not assume uploaded images or temporary files persist forever.
Warn the user to stop the pod manually when finished if no RunPod API integration exists.
```

### Do not do

```text
Do not claim the app can start/stop RunPod unless explicitly implemented later.
Do not auto-download models to reduce setup friction.
Do not store NSFW outputs in cloud by default.
```

### When to revisit

```text
During the next RunPod validation pass.
```

## B reference 5: RunPod Serverless

### Why it matters

Serverless may become useful later, but it is not the current validation target.

### Study focus

```text
- /run
- /runsync
- /status
- /stream
- /health
- worker cold start behavior
- request/response payload constraints
- persistent storage limitations
```

### Possible future use

```text
Serverless could be useful after the profile format and generation flow are stable.
It may support a more app-like production backend later.
```

### Do not do now

```text
Do not switch the current MVP to Serverless.
Do not design the Android app around Serverless first.
Do not hide ComfyUI while the workflow/profile system is still being validated.
```

### When to revisit

```text
After the Pod-based MVP works and cost/operation requirements are clearer.
```

## B reference 6: ComfyUI Manager / custom node management patterns

### Why it matters

Users may have missing custom nodes. The app should report missing requirements clearly.

### Study focus

```text
- how custom nodes are identified
- how missing nodes usually appear in workflows
- how users currently install/repair missing nodes
- how dependency warnings are represented
```

### Adopt as idea only

```text
Report missing custom nodes and provide guidance.
```

### Do not do

```text
Do not become a ComfyUI Manager replacement.
Do not auto-install custom nodes.
Do not run arbitrary shell commands from the Android app.
```

### When to revisit

```text
After /object_info-based node metadata work starts.
```

## B reference 7: Civitai workflow/model sharing behavior

### Why it matters

The long-term goal mentions Civitai/GitHub/local workflows. Civitai workflows may require specific models, LoRAs, VAEs, and custom nodes.

### Study focus

```text
- how workflows are shared
- whether metadata includes model references
- how users discover required models
- licensing/safety concerns
- NSFW content concerns
```

### Adopt as idea only

```text
Use metadata to warn about missing requirements.
Support manual import first.
```

### Do not do

```text
Do not auto-download Civitai models.
Do not create a public marketplace in the MVP.
Do not sync NSFW generated images to cloud by default.
```

### When to revisit

```text
After local/GitHub workflow import is stable.
```

## B reference 8: GitHub workflow/profile storage patterns

### Why it matters

GitHub may be a source for shared workflow files or app/profile specs.

### Study focus

```text
- raw workflow file import
- repository file organization
- versioned profile examples
- issue templates for workflow compatibility bugs
```

### Adopt as idea only

```text
Use GitHub as a manual source of workflow/profile files where appropriate.
Keep workflow/profile examples versioned.
```

### Do not do

```text
Do not make GitHub required for normal app usage.
Do not fetch arbitrary URLs automatically.
```

### When to revisit

```text
After profile import/export and local library are stable.
```

## C reference 9: Mobile app local storage and backup patterns

### Why it matters

Profiles, previews, and histories may grow beyond shared_preferences.

### Study focus

```text
- app-local files
- backup/export zip format
- Android scoped storage
- user-controlled delete/export
- privacy defaults
```

### Adopt as design principle

```text
Keep generated images local by default.
Make export explicit.
Make deletion easy.
```

### Do not do

```text
Do not enable automatic cloud sync by default.
Do not store unlimited history without user control.
```

### When to revisit

```text
After saved profile re-run behavior is proven.
```

## C reference 10: Prompt preset / style preset patterns

### Why it matters

The app may later help non-expert users generate prompts without editing raw JSON or complex nodes.

### Study focus

```text
- prompt fragment presets
- positive/negative prompt pairing
- profile-specific presets
- last-used values
```

### Adopt as idea only

```text
Keep prompt presets optional and profile-specific.
```

### Do not do

```text
Do not turn the app into a generic prompt marketplace.
Do not overwrite original profile defaults.
```

### When to revisit

```text
After prompt patching and saved profile re-run are stable.
```

## Reference study order after validation

```text
1. Official ComfyUI server/API behavior
2. Official ComfyUI API workflow examples
3. RunPod Pods behavior
4. /object_info and /models usage details
5. ComfyUI Manager / missing custom node patterns
6. comfy-portal-endpoint UI-to-API conversion reference
7. Civitai workflow/model sharing behavior
8. GitHub workflow/profile storage patterns
9. Android local storage and backup patterns
10. Prompt/style preset patterns
11. RunPod Serverless later
```

## Key rule

References should improve this project, not redefine it.

```text
This project remains:
RunPod ComfyUI + ComfyUI-Mobile-Analyzer + Android app using safe mobile profiles.
```
