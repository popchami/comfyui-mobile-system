# Mobile App Prototype

This folder is a placeholder for the smartphone app side of ComfyUI Mobile System.

## Role

The app should:

1. Register a ComfyUI URL
2. Check `/system_stats`
3. Fetch `/mobile_analyzer/profiles`
4. Download `/mobile_analyzer/profiles/{id}/download`
5. Extract `mobile_profile_export.zip`
6. Read `app_profile.json`
7. Render simple UI
8. Patch `workflow.json`
9. Submit to `/prompt`
10. Display images from `/history` and `/view`

## Current prototype

```text
mobile-app/prototype/index.html
mobile-app/prototype/profile-storage.js
```

This is a temporary HTML/PWA-style prototype for validating the app flow before building Flutter.

It can currently:

- Save a ComfyUI URL in the input field
- Check `/system_stats`
- Fetch `/mobile_analyzer/profiles`
- Show remote profile names
- Download selected remote profile zip
- Import local profile zip
- Extract `app_profile.json` and `workflow.json` from zip using JSZip
- Accept pasted `app_profile.json`
- Accept pasted `workflow.json`
- Validate minimal profile shape
- Render `ui.simple` fields
- Render image fields as file pickers
- Upload selected images to `/upload/image`
- Patch `LoadImage.image` with the uploaded image name
- Patch `workflow.json` using `patch_targets`
- Submit patched workflow to `/prompt`
- Poll `/history/{prompt_id}`
- Build `/view` URLs
- Display generated images
- Show patched workflow and history JSON for debugging

## Storage helper

`profile-storage.js` adds localStorage helper functions for browser-side profile persistence.

Supported helper actions:

- load stored profiles
- save stored profiles
- upsert profile by `profile_id`
- delete profile
- clear profiles

This helper is prepared for the next prototype step where imported zip profiles are saved and reopened without importing again.

## Not implemented in prototype yet

- Full UI wiring for stored profile list
- WebSocket progress
- Flutter UI

## MVP simple fields

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

## Development direction

Validation may start as a simple HTML/PWA prototype.

Final app direction is Flutter because it can handle:

- local profile storage
- zip extraction
- image caching
- Android app packaging
- future gallery save

## Important rule

The mobile app must not become a full workflow editor in MVP.

It should only patch fields listed in `app_profile.json.patch_targets`.
