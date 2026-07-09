# Future Issues and Improvements

## Purpose

This file records known issues, risks, and improvement directions after the pre-Claude handoff preparation.

This is not a request to add features before runtime validation.

Current priority remains:

```text
First prove the minimum runtime path works.
```

## Current status

```text
Pre-Claude preparation: complete
PR status: Draft
Runtime validation: not completed yet
Next step: Claude runtime validation
```

## Main issue groups

```text
1. Runtime uncertainty before validation
2. Analyzer accuracy limits
3. Flutter app save/load and re-run behavior
4. Workflow compatibility risks
5. Long-term safety and operations risks
```

## 1. Runtime uncertainty before validation

### Problem

The design and file structure are aligned, but the system has not yet been tested inside a real ComfyUI and Flutter Android runtime.

Unknowns:

```text
- Whether ComfyUI loads ComfyUI-Mobile-Analyzer correctly.
- Whether Mobile Profile Exporter appears in ComfyUI.
- Whether /mobile_analyzer/profiles is registered correctly.
- Whether output/mobile_profiles resolves to the intended ComfyUI output folder.
- Whether Flutter Android can complete /ws, /prompt, /history, and /view flow.
```

### Improvement direction

Do not add features first.

Run the minimum workflow path:

```text
1. Install Analyzer into ComfyUI/custom_nodes.
2. Start ComfyUI.
3. Confirm Mobile Profile Exporter appears.
4. Paste minimal_api_workflow.json.
5. Export profile zip.
6. Confirm /mobile_analyzer/profiles returns it.
7. Download the zip in Flutter.
8. Open GenerateScreen.
9. Submit /prompt.
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

Improve Analyzer in stages:

```text
Phase 1:
Stabilize KSampler / CLIPTextEncode / EmptyLatentImage / LoadImage / model loader handling.

Phase 2:
Use object_info to read node input types accurately.

Phase 3:
Check model folders and report missing models.

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
- Image input re-upload behavior needs runtime validation.
- Saved workflow re-run behavior needs runtime validation.
- Generated history storage is still weak.
- Error messages are still basic.
```

### Improvement direction

After runtime validation, move toward file-based profile storage.

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
Move large profile data to app-local files.

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
2. Use object_info for accurate input metadata.
3. Report missing models and nodes.
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
Claude runtime validation.

Step 2:
Fix only blockers found by Claude.

Step 3:
Pass the minimum profile zip to Flutter generation path.

Step 4:
Confirm saved profile re-run behavior.

Step 5:
Improve error display.

Step 6:
Add object_info support.

Step 7:
Add model/node missing checks.

Step 8:
Add UI workflow import/conversion if needed.

Step 9:
Add ControlNet / IPAdapter / FaceDetailer / Upscale support.

Step 10:
Add bypass / subgraph / node color handling.
```

## Priority ranking

### S rank: prove the core path

```text
- ComfyUI custom node loads.
- Profile zip is exported.
- Flutter reads the zip.
- /prompt generation works.
- /view image display works.
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
- object_info support.
- model existence checks.
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
A ComfyUI workflow can be analyzed by ComfyUI,
loaded by a smartphone app,
patched only through allowed fields,
submitted back to ComfyUI,
and displayed as a generated image.
```

If this works once, the core concept is validated.

## Recommended files after Claude validation

After Claude completes runtime validation, add:

```text
1. RUNTIME_VALIDATION_RESULT.md
2. BLOCKERS_AFTER_CLAUDE.md
3. NEXT_PHASE_PLAN.md
```

These should record:

```text
- What passed.
- What failed.
- What was fixed.
- What remains unverified.
- What should be done next.
```
