# Smartphone App Spec

## Role

The smartphone app reads exported mobile profiles, builds a simple UI, patches safe workflow values, submits to ComfyUI, and displays results.

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
7. Save to app local storage
8. Register as local profile
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

## Screens

Initial screens:

- Setup screen
- Connection status screen
- Remote profile list screen
- Local profile list screen
- Generation screen
- History screen
- Settings screen

## Generation flow

```text
1. User opens local profile
2. App renders simple UI from app_profile.json
3. User edits supported fields
4. App patches workflow.json using patch_targets
5. App submits patched workflow to /prompt
6. App tracks progress
7. App reads result from /history
8. App displays images via /view
9. App saves generation history
```

## Generation history

Save:

- image reference or local thumbnail
- profile_id
- prompt
- seed
- created_at
- ComfyUI URL
- patched workflow snapshot

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
