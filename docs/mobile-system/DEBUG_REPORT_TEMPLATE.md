# Debug Report Template

## Purpose

This file defines a copy-paste debug report format for failures in the Android app, Analyzer, ComfyUI, or RunPod environment.

The goal is to help a non-programmer send enough useful information to ChatGPT, Claude, or a developer without exposing private data unnecessarily.

## Privacy rule

```text
Do not include full private RunPod URLs by default.
Do not include generated images by default.
Do not include API keys, tokens, cookies, or secrets.
Redact anything that looks private.
```

## Short debug report

Use this first.

```text
Project: ComfyUI Mobile System
Where it failed:
- Setup / connection
- Remote profile list
- Profile download
- Local profile open
- Generate screen
- Image upload
- /prompt submit
- /ws progress
- /history result
- /view image display
- RunPod startup
- Analyzer export
- Other:

What I expected:

What happened instead:

Visible error message:

ComfyUI URL type:
- RunPod web/proxy URL
- local URL
- unknown

Can ComfyUI open in browser?
- yes / no / unknown

Profile name/id if known:

Does the profile need an input image?
- yes / no / unknown

Model warning shown?
- yes / no / unknown

Technical detail copied from app or ComfyUI:
```

## Full debug report

Use this when the short report is not enough.

```text
Project: ComfyUI Mobile System
Date/time:
Reporter:

Environment:
- Android device/emulator:
- Android version:
- Flutter app version/commit if known:
- RunPod GPU/pod type if known:
- ComfyUI version/commit if known:
- Analyzer branch/commit if known:

Current branch/PR:
- repo: popchami/comfyui-mobile-system
- branch: docs/mobile-system-spec
- PR: #1

Failure step:
- Setup / connection
- Remote profile list
- Profile download
- Local profile save
- Local profile open
- Generate screen render
- Image picker
- Image upload
- Workflow patch
- /prompt submit
- /ws progress
- /history lookup
- /view image display
- Analyzer node import
- Analyzer profile export
- RunPod startup
- Other:

Expected behavior:

Actual behavior:

User-facing error:

Technical error:

HTTP status code if any:

ComfyUI response body if safe:

Prompt id if available:

Profile information:
- profile name:
- profile id:
- profile version:
- patch_targets count:
- simple fields count:
- compatibility status:

Workflow information:
- text-to-image / image-to-image / inpaint / upscale / unknown
- uses image input: yes / no / unknown
- required model name if known:
- missing model warning: yes / no / unknown
- missing custom node warning: yes / no / unknown

Reproduction steps:
1.
2.
3.
4.

What was already tried:
- re-entered ComfyUI URL: yes / no
- restarted ComfyUI: yes / no
- restarted app: yes / no
- re-downloaded profile: yes / no
- re-selected input image: yes / no
- used a different model/profile: yes / no

Private data redacted:
- full RunPod URL: yes / no
- tokens/secrets: yes / no
- images: yes / no
```

## App-generated debug report target

Later, the Android app can generate a safe report automatically.

Suggested fields:

```json
{
  "project": "ComfyUI Mobile System",
  "app_version": "unknown",
  "profile_id": "",
  "profile_name": "",
  "failed_step": "",
  "friendly_error": "",
  "technical_detail": "",
  "http_status": null,
  "prompt_id": null,
  "requires_image": false,
  "model_warnings": [],
  "custom_node_warnings": [],
  "comfyui_host_redacted": true
}
```

## What not to include

```text
- full RunPod URL unless explicitly needed
- passwords
- API keys
- cookies
- private images
- NSFW images
- full local file paths if they reveal private information
```

## First implementation target later

After MVP validation, the first debug feature should be:

```text
Copy Debug Report button
```

It should copy:

```text
- failed step
- friendly error
- technical details
- profile name/id
- prompt_id if available
- model/custom node warning summary
- redacted ComfyUI host
```

It should not copy images or secrets by default.
