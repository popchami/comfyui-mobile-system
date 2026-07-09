# Future Feature Preparation

## Purpose

This file prepares future features without implementing them before RunPod GPU + Android validation.

The goal is to prevent future ideas from being lost while keeping PR #1 focused and safe.

## Timing rule

```text
Do not implement these features before RunPod GPU + Android real-device validation passes.
```

Allowed now:

```text
- Record feature intent.
- Record risks.
- Record required data/API dependencies.
- Record acceptance criteria.
- Record what must not be done.
```

Not allowed now:

```text
- Large code implementation.
- Automatic model downloads.
- Automatic custom node installation.
- Full workflow editor behavior.
- Playwright/Chromium as required MVP dependency.
- Google Drive sync.
- Payment/monetization.
```

## Feature priority buckets

### S: Core reliability after validation

These features improve the MVP path directly after the real RunPod + Android flow works.

```text
1. Better error messages
2. Saved profile re-run reliability
3. Image input re-upload behavior
4. Production-safe profile storage
```

### A: Analyzer accuracy

These features make profile generation more accurate without changing the product direction.

```text
1. /object_info-based field metadata
2. /models-based model existence check
3. custom node existence reporting
4. needs_attention warnings
```

### B: Workflow compatibility

These expand which workflows can be used.

```text
1. UI workflow import/conversion
2. ControlNet support
3. IPAdapter support
4. FaceDetailer support
5. Upscale workflow support
6. RemBG/background removal workflow support
```

### C: Advanced workflow safety and usability

These are important but should wait until the basic app is proven.

```text
1. bypass handling
2. subgraph handling
3. node color matching
4. generated history
5. profile preview image
6. profile update/migration
```

## Feature prep cards

### 1. Better error messages

Intent:

```text
When generation fails, show a clear user-facing reason instead of raw API errors.
```

Examples:

```text
- Model not found
- Custom node missing
- ComfyUI URL unreachable
- WebSocket disconnected
- Prompt rejected
- Image upload failed
- Profile zip invalid
```

Required data:

```text
- HTTP status code
- ComfyUI error JSON
- current profile id/name
- failed step name
```

Acceptance criteria:

```text
A beginner can understand what to fix without reading ComfyUI logs.
```

Do not:

```text
Do not hide the raw technical detail completely. Keep a technical details section for debugging.
```

### 2. Saved profile re-run reliability

Intent:

```text
A saved profile can be reopened later and used to generate again.
```

Risks:

```text
- RunPod URL changes between sessions.
- Uploaded image names may no longer exist in ComfyUI input folder.
- Model availability may change.
- Profile version may become old.
```

Required behavior:

```text
- Re-enter or update ComfyUI URL.
- Re-upload input images if needed.
- Patch only patch_targets.
- Keep original saved workflow unchanged.
```

Acceptance criteria:

```text
A saved profile can generate again after reopening the app, as long as the required model exists.
```

### 3. Image input re-upload behavior

Intent:

```text
When a workflow uses LoadImage, the Android app should re-upload the selected image when generating.
```

Risks:

```text
- ComfyUI uploaded filenames may not persist after restart.
- RunPod temporary storage may reset.
- Android file picker may return content URIs instead of normal paths.
```

Required behavior:

```text
- Store enough local info to ask user to re-select image if needed.
- Upload image through /upload/image before /prompt.
- Patch LoadImage.image with returned/uploaded filename.
```

Acceptance criteria:

```text
Image-to-image workflows can run from the Android app without manually copying image files into ComfyUI.
```

### 4. Production-safe profile storage

Intent:

```text
Move from shared_preferences to file-based app-local storage if profile JSON becomes too large.
```

Possible structure:

```text
profiles/
  profile_id/
    app_profile.json
    workflow.json
    source_info.json
    preview.png
    history/
```

Risks:

```text
- Android storage permissions
- backup/restore behavior
- profile migration
- large JSON performance
```

Acceptance criteria:

```text
Large workflows can be saved and reopened reliably without corrupting local app data.
```

### 5. /object_info-based field metadata

Intent:

```text
Use ComfyUI's /object_info API as the source of truth for node input metadata.
```

Expected benefit:

```text
- Better field types
- Better combo choices
- Better required/optional handling
- Better custom node compatibility
```

Risks:

```text
- object_info may vary across ComfyUI versions/custom nodes.
- Offline profile export may not have access to a running server if design changes later.
```

Acceptance criteria:

```text
Analyzer field metadata is based on the running ComfyUI environment instead of only hardcoded class_type guesses.
```

### 6. /models-based model existence checks

Intent:

```text
Use /models and /models/{folder} to verify whether referenced models exist.
```

Expected output:

```text
- model exists
- model missing
- model folder unknown
- model reference unverified
```

Do not:

```text
Do not auto-download missing models.
Only report missing models and show user-readable guidance.
```

Acceptance criteria:

```text
Before generation, the app can warn that a required checkpoint/LoRA/VAE is missing.
```

### 7. UI workflow import/conversion

Intent:

```text
Allow workflows copied from ComfyUI UI format to be converted or analyzed safely.
```

Reference:

```text
comfy-portal-endpoint is reference-only for the conversion concept.
Do not copy code.
Do not make Playwright/Chromium required for MVP.
```

Risks:

```text
- UI workflow and API workflow have different shapes.
- Conversion may require ComfyUI frontend logic.
- Heavy dependencies can hurt RunPod terminate/0GB-style operation.
```

Acceptance criteria:

```text
User can import a common ComfyUI workflow format without manually converting it first, if the optional converter is available.
```

### 8. ControlNet / IPAdapter / FaceDetailer / Upscale support

Intent:

```text
Expose common advanced workflow controls safely in the Android app.
```

Approach:

```text
Start with detection and needs_attention warnings.
Only expose fields as simple if Analyzer can prove they are safe patch_targets.
```

Do not:

```text
Do not expose every advanced node field by default.
Do not rewrite workflow structure.
```

Acceptance criteria:

```text
Advanced workflow support adds useful mobile controls without turning the app into a full ComfyUI editor.
```

### 9. Bypass handling

Intent:

```text
Support optional workflow branches without permanently changing the saved workflow.
```

Rule:

```text
Patch a generation copy only.
Never mutate the saved original workflow directly.
```

Acceptance criteria:

```text
Optional branches can be used safely and the saved profile remains unchanged.
```

### 10. Subgraph handling

Intent:

```text
Preserve workflows that use ComfyUI subgraphs.
```

Initial direction:

```text
Do not flatten or edit subgraphs in MVP.
Only expose safe patch_targets generated by Analyzer.
Subgraph internals should default to expert or hidden unless proven safe.
```

Acceptance criteria:

```text
A workflow containing subgraphs is preserved and not broken by profile export/import.
```

### 11. Node color matching

Intent:

```text
Use ComfyUI node color metadata to make app-side controls feel connected to the original workflow.
```

Timing:

```text
Later usability improvement. Not a functional blocker.
```

Acceptance criteria:

```text
If color metadata is available, the app can use it as a visual hint without changing workflow behavior.
```

### 12. Generated history and preview image

Intent:

```text
Let users recognize profiles and past generations more easily.
```

Possible data:

```text
- preview image
- last generated image
- last prompt
- generation timestamp
- used profile version
```

Risks:

```text
- storage growth
- NSFW image storage concerns
- Google Drive sync concerns
```

Acceptance criteria:

```text
User can identify a saved profile visually without forcing cloud sync.
```

## Do not implement list

Do not implement these until explicitly revisited after validation:

```text
- auto model download
- auto custom node install
- Google Drive image sync
- paid plan / monetization
- public sharing
- full workflow editor
- ComfyUI Manager replacement
- required Playwright/Chromium conversion pipeline
```

## Next action after validation

After RunPod GPU + Android validation passes, convert this document into real GitHub issues or implementation tickets in this order:

```text
1. Better error messages
2. Saved profile re-run reliability
3. Image input re-upload behavior
4. Production-safe profile storage decision
5. /object_info-based field metadata
6. /models-based model existence checks
7. UI workflow import/conversion research
8. Advanced workflow support
```
