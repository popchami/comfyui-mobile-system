# Additional Feature Candidates

## Purpose

This file records additional new feature candidates that are not required for MVP validation but may become useful after the RunPod GPU + Android path is proven.

These are idea-level candidates. Do not implement them before validation.

## Timing rule

```text
Do not implement before RunPod GPU + Android real-device validation passes.
```

Allowed now:

```text
- Record feature concept
- Record user value
- Record risk
- Record required dependencies
- Record priority
```

Not allowed now:

```text
- Build features into the app
- Add cloud sync
- Add monetization
- Add auto-downloads
- Add auto-installs
```

## Candidate priority overview

```text
S: useful soon after MVP works
A: useful after basic reliability
B: useful after profile/library structure is stable
C: later or optional
```

## S candidates

### 1. Profile Library with tags

User value:

```text
The user can manage many workflow profiles without losing track of them.
```

Possible tags:

```text
text-to-image
image-to-image
inpaint
upscale
face
anime
realistic
pixel art
icon
fast
high quality
needs model
needs image
```

Required data:

```text
profile id
profile name
tags
last used date
compatibility status
preview image later
```

Risk:

```text
Too many tags can become confusing. Start with automatic basic tags and allow manual tags later.
```

Priority:

```text
S after MVP validation
```

### 2. Profile search and filter

User value:

```text
The user can quickly find a workflow profile by name, type, tag, or warning status.
```

Filters:

```text
all
ready
needs attention
missing model
image required
recent
favorites
```

Required data:

```text
profile name
tags
warnings
compatibility status
last used date
```

Risk:

```text
Search is not useful until there are multiple saved profiles.
```

Priority:

```text
S after Profile Library exists
```

### 3. Favorite profiles

User value:

```text
Frequently used workflows are easy to access from the top of the local profile list.
```

Required data:

```text
favorite: true/false
favorite_order optional
```

Risk:

```text
Small feature, but should not be prioritized before generation reliability.
```

Priority:

```text
S/A
```

### 4. Last-used values per profile

User value:

```text
The app remembers the last prompt, seed, steps, image choice state, and other values for each profile.
```

Required data:

```text
profile_id
field_id
last_value
updated_at
```

Risk:

```text
Do not overwrite the original profile defaults. Store last-used values separately.
```

Priority:

```text
S after saved re-run behavior works
```

## A candidates

### 5. Preflight check before generation

User value:

```text
The app warns before generation if the profile is likely to fail.
```

Checks:

```text
ComfyUI reachable
required model exists
required image selected
workflow JSON valid
patch_targets valid
profile version supported
```

Required dependencies:

```text
/system_stats
/models
app_profile warnings
local selected image state
```

Risk:

```text
Preflight cannot guarantee success. Use likely-to-fail wording, not absolute claims.
```

Priority:

```text
A
```

### 6. One-tap random seed / lock seed

User value:

```text
The user can easily switch between reproducible and random generations.
```

Behavior:

```text
lock seed: reuse current seed
random seed: generate new seed before submit
```

Required data:

```text
seed patch_target
seed mode
last seed
```

Risk:

```text
Only show if Analyzer exposes a seed patch_target.
```

Priority:

```text
A
```

### 7. Prompt presets per profile

User value:

```text
The user can save common prompt fragments or style presets for a profile.
```

Examples:

```text
high quality
product photo
pixel art
icon style
cute style
realistic lighting
```

Required data:

```text
profile_id
preset_name
positive_prompt_addition
negative_prompt_addition
```

Risk:

```text
Preset stacking can confuse users. Start with simple replace/apply behavior.
```

Priority:

```text
A/B
```

### 8. Generation queue view

User value:

```text
The user can see whether generation is waiting, running, completed, or failed.
```

Possible states:

```text
ready
queued
running
completed
failed
cancelled
```

Required dependencies:

```text
/prompt response
/ws messages
/history/{prompt_id}
```

Risk:

```text
Queue behavior can differ by ComfyUI version and multiple users/sessions.
```

Priority:

```text
A/B
```

### 9. Cancel / interrupt generation

User value:

```text
The user can stop a generation if the wrong settings were submitted.
```

Possible API:

```text
/interrupt
```

Risk:

```text
Interrupt may affect the whole ComfyUI queue, not only this app's generation. Must be tested carefully.
```

Priority:

```text
B after queue behavior is understood
```

## B candidates

### 10. Profile import/export backup

User value:

```text
The user can move profiles between devices or restore profiles without cloud sync.
```

Format:

```text
profile zip
or app backup zip containing multiple profiles
```

Risk:

```text
Backups may contain prompts, workflow details, and preview images. Treat as private data.
```

Priority:

```text
B
```

### 11. QR code / local sharing of ComfyUI URL or profile metadata

User value:

```text
The user can move the current ComfyUI URL or a profile reference between devices more easily.
```

Possible uses:

```text
share ComfyUI URL
share local profile metadata
share import instructions
```

Risk:

```text
Do not expose private RunPod URLs publicly by accident.
```

Priority:

```text
B/C
```

### 12. RunPod session notes

User value:

```text
The app can help the user remember which RunPod URL/session/model state was used.
```

Possible fields:

```text
last_runpod_url
last_connected_at
notes
model availability snapshot
```

Risk:

```text
Do not imply the app can start/stop RunPod unless that is explicitly implemented later.
```

Priority:

```text
B
```

### 13. Cost awareness notes

User value:

```text
The user can avoid forgetting that a GPU pod is running.
```

Possible UX:

```text
manual reminder text
connected since timestamp
warning when generation completes: remember to stop RunPod if finished
```

Risk:

```text
Do not claim actual billing or pod state unless integrated with RunPod API later.
```

Priority:

```text
B
```

### 14. Debug report export

User value:

```text
When something fails, the user can copy a useful report to ChatGPT/Claude.
```

Report contents:

```text
app version
profile id/name
ComfyUI URL host only or redacted URL
failed step
friendly error
technical detail
prompt_id if available
model warning summary
```

Privacy rule:

```text
Redact full URLs and avoid including images by default.
```

Priority:

```text
A/B
```

## C candidates

### 15. Profile marketplace / template gallery

User value:

```text
The user can choose prepared workflow profiles instead of building everything manually.
```

Risk:

```text
High risk: licensing, NSFW content, model requirements, maintenance, security.
```

Initial safe version:

```text
Local built-in example profiles only, no public marketplace.
```

Priority:

```text
C / much later
```

### 16. In-app workflow recommendation

User value:

```text
The app can suggest which profile fits text-to-image, image-to-image, icon, upscale, etc.
```

Risk:

```text
Recommendation is only useful after tags and compatibility checks exist.
```

Priority:

```text
C
```

### 17. Multi-profile batch generation

User value:

```text
Generate the same prompt across multiple workflows or settings.
```

Risk:

```text
Can waste GPU time and cost quickly. Needs cost warning and queue safety.
```

Priority:

```text
C
```

### 18. A/B compare results

User value:

```text
Compare two settings, seeds, or profiles side by side.
```

Risk:

```text
Requires history/preview storage and can increase GPU usage.
```

Priority:

```text
C
```

### 19. Lightweight prompt builder

User value:

```text
Help non-experts create prompts from simple options.
```

Possible sections:

```text
subject
style
lighting
camera
quality
negative prompt
```

Risk:

```text
Can become a separate product. Keep optional and profile-specific.
```

Priority:

```text
C
```

### 20. Local-only safety mode

User value:

```text
The user can keep profiles and outputs local, without cloud sync or sharing.
```

Behavior:

```text
no auto cloud sync
no public sharing
manual delete history
manual export only
```

Priority:

```text
B/C depending on storage/history features
```

## Suggested next feature decision order

After MVP validation, evaluate in this order:

```text
1. Better error messages
2. Debug report export
3. Saved profile re-run reliability
4. Image re-upload behavior
5. Profile library with tags
6. Profile search/filter/favorites
7. Last-used values
8. Preflight check
9. /object_info and /models integration
10. Prompt presets
11. Queue view
12. RunPod session/cost notes
13. Import/export backup
14. Preview/history
15. Advanced workflow support
```

## Features to avoid until much later

```text
- public marketplace
- automatic model downloads
- automatic custom node installs
- cloud sync by default
- multi-profile batch generation without cost warnings
- full workflow editor
```
