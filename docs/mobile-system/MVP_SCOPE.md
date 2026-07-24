# MVP Scope

## Goal

The first version should prove the full path:

```text
Analyze workflow in ComfyUI
  ↓
Export mobile_profile_export.zip
  ↓
Smartphone app downloads it
  ↓
Smartphone app shows simple UI
  ↓
User edits key parameters
  ↓
App patches workflow.json
  ↓
App submits to ComfyUI
  ↓
App displays generated image
```

Do not try to support every ComfyUI custom node in MVP.

## ComfyUI-Mobile-Analyzer MVP

Required:

- Load `workflow.json`
- Detect workflow format at a basic level
- Classify core nodes
- Build `app_profile.json`
- Build `mobile_profile_export.zip`
- Save zip to `ComfyUI/output/mobile_profiles/`
- Provide profile list API
- Provide profile download API

## MVP known nodes

- KSampler
- CLIPTextEncode
- LoadImage
- SaveImage
- PreviewImage
- EmptyLatentImage
- CheckpointLoaderSimple
- UNETLoader
- DualCLIPLoader
- VAELoader
- VAEEncode
- VAEDecode
- LoraLoader

## MVP simple UI fields

Expose only when present in workflow:

- prompt
- negative
- seed
- steps
- cfg
- sampler
- scheduler
- denoise
- width
- height
- batch
- input image

## Smartphone App MVP

Required:

- Register ComfyUI URL
- Check connection with `/system_stats`
- Fetch profile list from `/mobile_analyzer/profiles`
- Download zip from `/mobile_analyzer/profiles/{id}/download`
- Extract zip locally
- Validate `app_profile.json`
- Load `workflow.json`
- Render `simple` UI
- Edit prompt / seed / steps / cfg
- Patch workflow using `patch_targets`
- Send patched workflow to `/prompt`
- Read result from `/history/{prompt_id}`
- Display image via `/view`

## Out of scope for MVP

- Full ControlNet UI
- Full IPAdapter UI
- FaceDetailer UI
- Upscale UI
- Wildcard UI
- Ollama / LLM UI
- Automatic custom node installation
- Automatic model download
- ComfyUI Manager integration beyond later documentation
- Google Drive auto-save
- Cloud sync
- Multiple users
- Payments
- Batch export
- Debug export UI

## MVP principle

MVP is not a full ComfyUI replacement.

MVP is a workflow execution app that can:

```text
read analyzed profile
show simple controls
patch safe values
submit workflow
show result
```
