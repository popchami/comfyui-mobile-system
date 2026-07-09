# Future Issues and Improvements

## Purpose

This file records known issues, risks, and improvement directions after architecture alignment and the first limited runtime validation pass.

This is not a request to add features before RunPod GPU validation and Android real-device validation.

Current priority remains:

```text
First prove the real RunPod GPU + Android app path works.
```

## Current status

```text
Pre-Claude preparation: complete
Architecture alignment review: complete
Limited CPU-only runtime validation: complete
PR status: Draft
RunPod GPU validation: not completed yet
Android device/emulator validation: not completed yet
Next step: RunPod GPU + Android real-device validation
```

See also:

```text
docs/mobile-system/RUNTIME_VALIDATION_RESULT.md
docs/mobile-system/BLOCKERS_AFTER_CLAUDE.md
docs/mobile-system/NEXT_PHASE_PLAN.md
```

## Main issue groups

```text
1. Remaining real-environment validation gaps
2. Analyzer accuracy limits
3. Flutter app save/load and re-run behavior
4. Workflow compatibility risks
5. Long-term safety and operations risks
```

## 1. Remaining real-environment validation gaps

### Problem

The design and file structure are aligned, and the limited sandbox validation passed for the parts that environment could test. However, the system has not yet been fully tested inside the intended real environment.

Already confirmed:

```text
- ComfyUI can load ComfyUI-Mobile-Analyzer in a CPU-only sandbox.
- Mobile Profile Exporter can appear via /object_info.
- Mobile Profile Exporter can export a profile zip after OUTPUT_NODE fix.
- /mobile_analyzer/profiles works in the sandbox.
- /mobile_analyzer/profiles/{id}/download works in the sandbox.
- Flutter PR source passes pub get and analyze in the sandbox.
```

Still unknown:

```text
- Whether latest branch still loads cleanly on RunPod after WEB_DIRECTORY cleanup.
- Whether real GPU image generation works with an actual checkpoint model.
- Whether Flutter Android runs correctly on a real device or emulator.
- Whether native file_picker behavior works on Android.
- Whether the full Android UI can download, save, open, patch, submit, and display a generated image.
```

### Improvement direction

Do not add features first.

Run the intended real workflow path:

```text
1. Start RunPod ComfyUI.
2. Install/place Analyzer into ComfyUI/custom_nodes.
3. Start ComfyUI and confirm no import errors.
4. Confirm Mobile Profile Exporter appears.
5. Export profile zip.
6. Confirm /mobile_analyzer/profiles returns it.
7. Download the zip in the Flutter Android app.
8. Open GenerateScreen.
9. Submit /prompt to the RunPod ComfyUI URL.
10. Display generated image from /view.
```

## 2. Analyzer accuracy limits

### Problem

The current Analyzer is an MVP scaffold. It detects common simple fields, but it does not yet fully understand complex workflows.

Current limits:

```text
- API workflow is assumed.
- UI workflow import/conversion is not implemented.
- object_info is not inspected.
- Installed custom node existence is not checked.
- Model file existence is not checked.
- ControlNet / IPAdapter / FaceDetailer / Upscale / RemBG handling is not implemented.
```

### Improvement direction

Improve Analyzer in stages after the real RunPod + Android validation path passes:

```text
Phase 1:
Stabilize KSampler / CLIPTextEncode / EmptyLatentImage / LoadImage / model loader handling.

Phase 2:
Use /object_info to read node input types accurately.

Phase 3:
Use /models and /models/{folder} to check model folders and report missing models.

Phase 4:
Classify ControlNet / IPAdapter / FaceDetailer / Upscale / RemBG workflows.

Phase 5:
Support UI workflow to API workflow conversion if needed.
```

Important safety rule:

```text
Do not auto-install custom nodes or auto-download models yet.
Only report what is missing.
```

## 3. Flutter app save/load and re-run behavior

### Problem

Flutter MVP currently uses shared_preferences for local profile storage. This is acceptable for testing, but may not be suitable for large workflow JSON and image-related data.

Known risks:

```text
- Large workflow JSON may be too heavy for shared_preferences.
- Image input re-upload behavior needs Android runtime validation.
- Saved workflow re-run behavior needs RunPod + Android validation.
- Generated history storage is still weak.
- Error messages are still basic.
```

### Improvement direction

After real validation, move toward file-based profile storage if shared_preferences is too weak.

Possible production structure:

```text
profiles/
  profile_id/
    app_profile.json
    workflow.json
    source_info.json
    preview.png
    history/
      2026-07-09_001.json
      2026-07-09_001.png
```

Suggested progression:

```text
MVP:
Use shared_preferences to prove the flow.

Next:
Move large profile data to app-local files if needed.

Later:
Add preview image, generated history, last-used values, and profile update handling.
```

## 4. Workflow compatibility risks

### Problem

ComfyUI workflows are flexible. Compatibility can break if the app tries to support too much too early.

Known risks:

```text
- Bypassed nodes are not handled.
- Subgraphs are not handled.
- UI workflow and API workflow contain different kinds of metadata.
- Node color may be lost in API workflow format.
- Custom nodes may use different input names and behaviors.
```

### Improvement direction

Compatibility should expand in this order:

```text
1. Stabilize flat API workflows.
2. Use /object_info for accurate input metadata.
3. Use /models to report missing models and nodes.
4. Add UI workflow import/conversion if needed.
5. Add bypass handling.
6. Add subgraph handling.
7. Add node color handling.
```

Important workflow safety rule:

```text
Never mutate the saved original workflow directly.
Patch only a generation copy.
Discard the generation copy after submission.
```

## 5. Long-term safety and operations risks

### Problem

The system can become risky if it automatically installs code, downloads models, or syncs generated images without clear user control.

Risks:

```text
- Automatic custom node install can run unsafe code.
- Automatic model download can create capacity, copyright, or NSFW storage problems.
- External URL fetching can reduce safety.
- Google Drive sync may be unsafe for NSFW images.
- RunPod paths and storage behavior can differ by environment.
```

### Improvement direction

Keep a conservative safety model.

Allowed:

```text
- Analyze workflow JSON.
- Show missing nodes.
- Show missing models.
- Show suggested install/download information.
- Save/load profiles under explicit user control.
```

Not allowed yet:

```text
- Automatic pip install.
- Automatic git clone.
- Automatic model download.
- Automatic external URL fetching.
- Automatic Google Drive sync.
```

## Recommended improvement roadmap

```text
Step 1:
RunPod GPU validation.

Step 2:
Android real-device or emulator validation.

Step 3:
Fix only blockers found during real validation.

Step 4:
Confirm saved profile re-run behavior and image re-upload behavior.

Step 5:
Improve error display.

Step 6:
Decide whether shared_preferences is enough or file-based profile storage is needed.

Step 7:
Add /object_info support.

Step 8:
Add /models and /models/{folder} model/node missing checks.

Step 9:
Add UI workflow import/conversion if needed.

Step 10:
Add ControlNet / IPAdapter / FaceDetailer / Upscale support.

Step 11:
Add bypass / subgraph / node color handling.
```

## Priority ranking

### S rank: prove the real core path

```text
- RunPod ComfyUI custom node loads.
- Profile zip is exported on RunPod.
- Flutter Android reads the zip.
- /prompt generation works with a real model.
- /view image display works in the Android app.
```

### A rank: make MVP usable

```text
- Saved profile re-run.
- Image input re-upload.
- Clear error messages.
- Better profile list display.
```

### B rank: improve compatibility

```text
- /object_info support.
- /models existence checks.
- custom node existence checks.
- UI workflow import.
```

### C rank: later usability and advanced workflow support

```text
- node color matching.
- bypass handling.
- subgraph handling.
- Google Drive support.
- payment/monetization.
- ComfyUI Manager registration.
```

## Key project principle

The next proof target is:

```text
A ComfyUI workflow can be analyzed by RunPod ComfyUI,
loaded by a smartphone app,
patched only through allowed fields,
submitted back to RunPod ComfyUI,
and displayed on Android as a generated image.
```

If this works once, the core concept is validated.
