# Smartphone App Spec

## Role

The smartphone app reads exported mobile profiles, builds a simple UI, patches safe workflow values, submits to ComfyUI, and displays results.

The app is a safe control surface for completed user-owned workflows.

It should not pretend that every imported workflow is fully supported.

## Initial setup

The app should support:

- ComfyUI URL input
- `/system_stats` connection check
- Analyzer availability check
- profile list check
- local storage initialization

## Required APIs

- `GET /system_stats`
- `GET /mobile_analyzer/profiles`
- `GET /mobile_analyzer/profiles/{id}/download`
- `POST /prompt`
- `GET /history/{prompt_id}`
- `GET /view`
- WebSocket progress

## Profile import flow

```text
1. Fetch profile list from ComfyUI
2. User selects profile
3. Download profile zip
4. Extract zip
5. Validate app_profile.json
6. Validate workflow.json
7. Read compatibility level
8. Save to app local storage if valid
9. Register as local profile
```

## Local storage

```text
app_data/
  profiles/
    profile_id/
      workflow.json
      app_profile.json
      preview.png
      source_info.json
```

## Validation

Before registering a profile, check:

- zip opens correctly
- `workflow.json` exists
- `app_profile.json` exists
- `schema_version` is supported
- `profile_id` exists
- `workflow_id` exists
- compatibility status is valid
- missing nodes and models are shown to user

## Compatibility handling

The app must respect Analyzer compatibility levels.

```text
supported
- Show normal generation UI.
- Allow editing of validated controls.
- Allow generation if environment checks pass.

partial
- Show usable safe controls.
- Show warnings prominently.
- Hide or disable risky controls.
- Allow generation only if safe_to_generate is true.

unsupported
- Preserve/display profile metadata.
- Do not expose unsafe editing.
- Do not generate unless a later validation explicitly marks it safe.
- Explain why unsupported.
```

Potential app behavior:

```text
Supported profile
  -> normal Generate screen

Partial profile
  -> Generate screen with warning card and disabled risky sections

Unsupported profile
  -> Profile details / analysis report only
```

## Screens

Initial screens:

- Setup screen
- Connection status screen
- Remote profile list screen
- Local profile list screen
- Generation screen
- History screen
- Settings screen

Additional/detail screens may exist:

- Profile analysis report screen
- Graph / node detail screen
- Subgraph detail screen
- Compatibility warning screen

## Generation screen layout

The generation screen should be generated from `app_profile.json`, but the app should control the screen structure.

Default layout:

```text
1. Status / connection / current profile
2. Compatibility / warning card
3. Core Inputs                       open
4. Basic Generation Settings         collapsed
5. Size / Output                     collapsed
6. Advanced Workflow Features        collapsed
7. Expert / Debug                    collapsed
8. Generate action
9. Session history / generated outputs
```

Core Inputs should remain visible by default:

```text
- prompt
- negative prompt
- required image input
- mask / paint controls when required
- wildcard controls when profile exposes them as primary controls
```

Detailed settings should be collapsible by default:

```text
- seed
- steps
- cfg
- sampler
- scheduler
- denoise
- width
- height
- batch
- LoRA
- ControlNet
- IPAdapter
- FaceDetailer
- Upscale
- RemBG
- Inpaint
- Mask
- wildcard controls when optional/large
- unknown editable inputs
- debug/raw workflow information
```

Important:

```text
Do not collapse every usable field.
The user should immediately see where to enter the main creative input.
A control being on another page does not mean it is disconnected from the workflow graph.
```

If Analyzer provides explicit section metadata, use it.
If not, use app-side fallback grouping based on `field_id`, `label`, `type`, and `section`.

## Generation flow

```text
1. User opens local profile
2. App reads compatibility level
3. App renders only safe UI from app_profile.json
4. User edits supported fields
5. App patches workflow.json using patch_targets only
6. App submits patched workflow to /prompt only when safe_to_generate is true
7. App tracks progress
8. App reads result from /history
9. App displays output according to output type
10. App saves generation history
```

## Generation history

Save:

- output reference or local thumbnail when available
- output type
- profile_id
- prompt
- seed
- created_at
- ComfyUI URL
- patched workflow snapshot

MVP may keep only session history in the generation screen until persistent storage is finalized.

## Profile update rule

- Same `profile_id` plus newer `profile_version` means update
- Different `profile_id` means new profile

## Delete rule

Deleting a profile on smartphone deletes only the local app profile.

It should not delete the zip from ComfyUI.

## Connection types

Support these types:

- RunPod
- Local PC
- Other URL

Save:

- ComfyUI URL
- optional Jupyter URL
- memo
- last connected at

## MVP principle

The smartphone app is not a complete ComfyUI replacement.

MVP is a workflow execution app:

```text
read profile
show simple controls
patch safe values
submit workflow
show result
```

## Product guardrail

```text
The app UI may be simple, but it must respect Analyzer compatibility.
Supported means safe controls and generation.
Partial means warning-first and only safe controls.
Unsupported means preserve and explain, not unsafe generation.
```