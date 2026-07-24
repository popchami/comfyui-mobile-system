# Post-Validation Issue Drafts

## Purpose

This file contains issue-ready drafts for work that should happen after RunPod GPU + Android validation passes.

Do not open or implement these as active tasks until the real validation path is complete.

## Rule before converting to Issues

```text
Only convert these drafts into real GitHub Issues after:
1. RunPod ComfyUI validation passes.
2. Real checkpoint image generation passes.
3. Flutter Android device/emulator validation passes.
4. HANDOFF.md is updated with final validation results.
```

## Issue 1: Improve user-facing error messages

Title:

```text
Improve user-facing error messages for connection, profile, model, and generation failures
```

Problem:

```text
The current MVP may expose raw HTTP/ComfyUI errors. A beginner needs clear guidance without reading logs.
```

Scope:

```text
- Map common failures to friendly messages.
- Keep technical details available in an expandable section.
- Add step context: connection, profile download, zip parse, image upload, prompt submit, ws progress, history, view image.
```

Acceptance criteria:

```text
- Missing model shows a clear model-missing message.
- Unreachable ComfyUI URL shows a connection message.
- Invalid profile zip shows a profile import message.
- Failed image upload shows an image upload message.
- Raw technical details are still available for AI/debugging.
```

Out of scope:

```text
- Auto-fixing errors.
- Auto-downloading models.
- Auto-installing custom nodes.
```

## Issue 2: Confirm saved profile re-run reliability

Title:

```text
Validate and harden saved profile re-run behavior
```

Problem:

```text
A saved profile must be usable again after reopening the app, but RunPod URLs, uploaded images, and model availability can change.
```

Scope:

```text
- Reopen saved profile.
- Re-enter/update ComfyUI URL if needed.
- Patch only patch_targets.
- Submit generation from saved profile.
- Confirm original workflow is not mutated.
```

Acceptance criteria:

```text
- Saved text-to-image profile can generate again after app restart.
- Saved image-to-image profile asks for image re-selection or re-upload when needed.
- Original saved workflow stays unchanged.
```

Out of scope:

```text
- Cloud sync.
- Generation history.
- Full workflow editor.
```

## Issue 3: Handle image input re-upload for LoadImage workflows

Title:

```text
Add reliable image re-upload flow for LoadImage workflows
```

Problem:

```text
ComfyUI uploaded filenames may not persist across RunPod sessions. Android may provide content URIs instead of normal file paths.
```

Scope:

```text
- Detect profiles that require image input.
- Require user selection before generation.
- Upload selected image to /upload/image.
- Patch LoadImage.image with the uploaded filename.
- Show clear error if image is missing.
```

Acceptance criteria:

```text
- A LoadImage workflow can run from Android after selecting an image.
- Re-opening a saved profile does not silently reuse a missing old upload filename.
- User sees a clear message when image re-selection is required.
```

Out of scope:

```text
- Image editing.
- Mask editing.
- Automatic cloud backup of input images.
```

## Issue 4: Decide production profile storage strategy

Title:

```text
Decide and implement production-safe local profile storage
```

Problem:

```text
shared_preferences is acceptable for MVP proof, but large workflows and future preview/history data may require file-based storage.
```

Scope:

```text
- Measure typical profile size.
- Decide shared_preferences vs app-local files.
- Define profile directory structure if file-based storage is needed.
- Preserve existing saved profiles or provide migration.
```

Acceptance criteria:

```text
- Large workflow profiles can be saved and reopened reliably.
- App does not corrupt local profile data.
- Storage behavior is Android-safe.
```

Out of scope:

```text
- Google Drive sync.
- Public sharing.
- Payment features.
```

## Issue 5: Add /object_info-based field metadata

Title:

```text
Use /object_info to improve Analyzer field metadata
```

Problem:

```text
Analyzer currently relies on class_type guesses for common fields. /object_info can provide field types, required/optional state, and combo choices from the running ComfyUI environment.
```

Scope:

```text
- Query /object_info or /object_info/{node_class} where useful.
- Add optional input_metadata to app_profile.json.
- Use metadata for safer app controls.
- Preserve current app_profile compatibility.
```

Acceptance criteria:

```text
- KSampler choices and numeric fields can be described from runtime metadata.
- Unknown/custom nodes can provide better needs_attention information.
- Existing profiles without input_metadata still work.
```

Out of scope:

```text
- Full workflow editor.
- Arbitrary custom node UI.
```

## Issue 6: Add /models-based model existence checks

Title:

```text
Use /models to report missing checkpoint, LoRA, VAE, and other model references
```

Problem:

```text
Analyzer can detect model names but currently marks them unverified. The app should warn when required models are missing.
```

Scope:

```text
- Query /models and /models/{folder}.
- Compare detected model references against available models.
- Add model_checks to app_profile.json.
- Show missing model warning before generation.
```

Acceptance criteria:

```text
- Existing model references show exists.
- Missing model references show missing.
- The app blocks or warns clearly before generation when required model is missing.
```

Out of scope:

```text
- Auto-download models.
- Model search marketplace.
- ComfyUI Manager replacement.
```

## Issue 7: Research optional UI workflow import/conversion

Title:

```text
Research optional UI workflow to API workflow conversion path
```

Problem:

```text
Many workflows are shared in ComfyUI UI format. MVP assumes API workflow format.
```

Scope:

```text
- Compare UI workflow vs API workflow structure.
- Study comfy-portal-endpoint as reference only.
- Identify whether conversion should be Analyzer-side, optional tool-side, or user-assisted.
- Avoid Playwright/Chromium as required MVP dependency.
```

Acceptance criteria:

```text
- Clear decision recorded: implement optional converter, defer, or require API export.
- Risks and dependencies are documented.
```

Out of scope:

```text
- Copying comfy-portal-endpoint code.
- Required Playwright/Chromium dependency.
- Full workflow management portal.
```

## Issue 8: Add advanced workflow detection plan

Title:

```text
Plan support for ControlNet, IPAdapter, FaceDetailer, Upscale, and RemBG workflows
```

Problem:

```text
Advanced workflows need careful detection so the app can expose useful controls without breaking workflow structure.
```

Scope:

```text
- Detect common advanced node roles.
- Mark unsupported or partially supported workflows as needs_attention.
- Decide which fields can become patch_targets.
- Keep unknown nodes preserved.
```

Acceptance criteria:

```text
- Analyzer can identify major advanced workflow types.
- App shows clear support status.
- No advanced node is edited unless it is listed as a safe patch_target.
```

Out of scope:

```text
- Rebuilding workflow graphs.
- Full node editor.
- Auto-installing missing custom nodes.
```

## Issue 9: Add profile details screen

Title:

```text
Add profile details summary screen
```

Problem:

```text
Users need a readable summary of what a profile contains before generating.
```

Scope:

```text
- Show profile name/version.
- Show simple controls count.
- Show patch_targets count.
- Show detected model references.
- Show warnings/compatibility status.
```

Acceptance criteria:

```text
User can inspect a profile without opening JSON.
```

Out of scope:

```text
- Editing raw workflow JSON.
- Node graph visualization.
```

## Issue 10: Add generated preview/history after MVP is stable

Title:

```text
Add optional profile preview and generated history
```

Problem:

```text
Saved profiles are hard to recognize without a preview or history.
```

Scope:

```text
- Save optional preview image.
- Save limited local history.
- Allow history deletion.
- Avoid automatic cloud sync.
```

Acceptance criteria:

```text
User can visually identify a saved profile and clear local history.
```

Out of scope:

```text
- Google Drive sync.
- Public sharing.
- Unlimited storage.
```

## Suggested issue order after validation

```text
1. Improve user-facing error messages
2. Confirm saved profile re-run reliability
3. Handle image input re-upload for LoadImage workflows
4. Decide production profile storage strategy
5. Add /object_info-based field metadata
6. Add /models-based model existence checks
7. Add profile details screen
8. Research optional UI workflow import/conversion
9. Add advanced workflow detection plan
10. Add generated preview/history after MVP is stable
```
