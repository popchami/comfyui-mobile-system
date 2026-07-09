# UX Flow Preparation

## Purpose

This file prepares future Android app flows without implementing them before validation.

The goal is to make later UI work easier while keeping the current PR focused on validation.

## Timing rule

```text
Do not implement these flows before RunPod GPU + Android real-device validation passes.
```

Allowed now:

```text
- Define screen responsibilities.
- Define empty/loading/error states.
- Define beginner-friendly wording.
- Define acceptance criteria.
```

Not allowed now:

```text
- Add new screens to code.
- Add full workflow editor behavior.
- Add cloud sync.
- Add payment/monetization.
```

## Current MVP flow

```text
SetupScreen
  ↓
RemoteProfilesScreen
  ↓
Save downloaded profile
  ↓
LocalProfilesScreen
  ↓
GenerateScreen
  ↓
Submit generation
  ↓
Display image
```

## Future screen map

### 1. Setup / Connection Screen

Purpose:

```text
Connect the Android app to the current ComfyUI URL.
```

Primary actions:

```text
- Enter ComfyUI URL
- Check connection through /system_stats
- Open remote profiles
- Open local profiles
```

Future improvements:

```text
- Connection history
- Last used RunPod URL
- Clear connection error messages
- URL expiry warning
```

Empty state wording:

```text
Enter your ComfyUI URL to start.
```

Error wording examples:

```text
Could not reach ComfyUI. Check that the RunPod pod is running and the URL is current.
```

Acceptance criteria:

```text
A beginner can tell whether the issue is the URL, RunPod not running, or ComfyUI not responding.
```

### 2. Remote Profiles Screen

Purpose:

```text
Show profile zips available from ComfyUI-Mobile-Analyzer.
```

Primary actions:

```text
- Fetch /mobile_analyzer/profiles
- Download profile zip
- Save as local profile
```

Future improvements:

```text
- Show profile name
- Show modified time
- Show compatibility status
- Show missing model warning before saving
- Show profile version
```

Empty state wording:

```text
No profiles found. Export a profile from ComfyUI first.
```

Error wording examples:

```text
Profile list could not be loaded. Confirm that ComfyUI-Mobile-Analyzer is installed on ComfyUI.
```

Acceptance criteria:

```text
User can understand whether there are no profiles or the Analyzer route is not working.
```

### 3. Local Profiles Screen

Purpose:

```text
Show profiles saved on the phone.
```

Primary actions:

```text
- Open profile
- Delete profile
- Refresh list
```

Future improvements:

```text
- Profile preview image
- Last used date
- Last successful generation date
- Compatibility badge
- Missing model badge
- Search/filter
```

Empty state wording:

```text
No saved profiles yet. Download one from ComfyUI.
```

Acceptance criteria:

```text
User can reopen a saved profile without downloading it every time.
```

### 4. Generate Screen

Purpose:

```text
Show simple controls generated from app_profile.json and submit generation.
```

Primary actions:

```text
- Edit simple fields
- Select input image if needed
- Submit generation
- Watch progress
- Display result
```

Future improvements:

```text
- Better grouped controls
- Show model warnings
- Show custom node warnings
- Show field help text
- Advanced/expert toggle
- Reset to profile defaults
- Reuse last values
```

Error wording examples:

```text
Required model is missing in ComfyUI.
This profile needs an image. Select an image before generating.
Generation failed. Open technical details for ComfyUI error response.
```

Acceptance criteria:

```text
User can generate without seeing raw workflow JSON.
```

### 5. Preflight Check Screen or Section

Purpose:

```text
Check whether the selected profile is likely to run before sending /prompt.
```

Possible checks:

```text
- ComfyUI reachable
- Analyzer profile valid
- required model exists
- required image selected
- patch_targets valid
- workflow JSON valid
```

Result states:

```text
ready
needs_attention
blocked
unknown
```

Acceptance criteria:

```text
The app catches obvious missing model/image/profile problems before generation.
```

### 6. Error Details Screen or Bottom Sheet

Purpose:

```text
Show beginner-friendly error first, then technical details if needed.
```

Structure:

```text
Short message
What it means
What to do next
Technical details
```

Example:

```text
Short message:
Required model is missing.

What it means:
ComfyUI does not have the checkpoint this profile uses.

What to do next:
Use a profile that matches installed models, or add the model manually on RunPod.

Technical details:
ckpt_name: example.safetensors not in []
```

Acceptance criteria:

```text
A non-programmer can report useful details to an AI assistant without reading logs.
```

### 7. Profile Details Screen

Purpose:

```text
Show what a profile contains before generation.
```

Possible fields:

```text
- profile name
- profile version
- workflow hash
- detected model references
- simple controls count
- patch_targets count
- compatibility status
- warnings
```

Acceptance criteria:

```text
User can inspect profile safety and compatibility without opening JSON.
```

### 8. Generation History Screen

Purpose:

```text
Show past generated images and the profile/settings used.
```

Timing:

```text
Later. Not required for MVP validation.
```

Risks:

```text
- storage growth
- NSFW image storage
- backup/sync safety
```

Acceptance criteria:

```text
History helps users find previous outputs without requiring cloud sync.
```

## Beginner-friendly wording rules

Use wording like:

```text
ComfyUI is not reachable.
Profile was downloaded.
This profile needs an image.
Required model is missing.
Generation is running.
Generated image is ready.
```

Avoid wording like:

```text
Null pointer
Unhandled exception
Malformed payload
Bad state
Stack trace first
```

Technical details can still be shown under an expandable section.

## Navigation rule

The app should not expose full workflow editing in MVP.

```text
Profile list -> simple generated controls -> generate -> result
```

Do not add:

```text
- node graph editor
- arbitrary JSON editor
- custom node installer UI
- model downloader UI
```

## First UX improvements after validation

After RunPod + Android validation passes, prioritize:

```text
1. Better connection error states.
2. Better profile download/save feedback.
3. Better missing model/image messages.
4. Profile details summary.
5. Advanced/expert toggle only after simple controls work.
6. Preview/history later.
```
