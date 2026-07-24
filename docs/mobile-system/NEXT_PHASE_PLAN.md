# Next Phase Plan

## Purpose

This file defines the next work phase after the smartphone-only GitHub cleanup is complete.

## Current state

```text
Smartphone-only GitHub cleanup: complete
Architecture alignment review: complete
Limited CPU-only runtime validation: complete
PR status: Draft
Merge status: do not merge
```

## Next phase name

```text
RunPod GPU + Android real-device validation
```

## Phase goal

Confirm the real MVP path:

```text
RunPod ComfyUI
  ↓
ComfyUI-Mobile-Analyzer exports profile zip
  ↓
Android Flutter app downloads profile zip
  ↓
Android Flutter app opens profile
  ↓
Android Flutter app patches patch_targets only
  ↓
Android Flutter app submits workflow to ComfyUI
  ↓
ComfyUI generates an image with a real model
  ↓
Android Flutter app displays the result
```

## Step 1: RunPod ComfyUI validation

Do this when RunPod is available.

```text
1. Start RunPod Pod with ComfyUI.
2. Put the latest PR branch Analyzer into:
   ComfyUI/custom_nodes/ComfyUI-Mobile-Analyzer/
3. Start or restart ComfyUI.
4. Confirm no import errors.
5. Confirm Mobile Profile Exporter appears.
6. Export a profile zip from a minimal API workflow.
7. Confirm zip exists under output/mobile_profiles/.
8. Confirm zip includes workflow.json and app_profile.json.
9. Confirm GET /mobile_analyzer/profiles returns the profile.
10. Confirm GET /mobile_analyzer/profiles/{id}/download downloads the zip.
```

## Step 2: Real model generation validation

```text
1. Use an already-approved checkpoint/model already available in the RunPod environment.
2. Do not auto-download models.
3. Use a minimal workflow that references that existing model.
4. Submit /prompt with a generated or downloaded profile.
5. Monitor /ws.
6. Read /history/{prompt_id}.
7. Fetch output through /view.
8. Confirm at least one image is generated.
```

## Step 3: Android Flutter validation

```text
1. Create a real Flutter Android project shell.
2. Copy mobile-app/flutter_mvp/lib/ into the real project.
3. Copy mobile-app/flutter_mvp/pubspec.yaml into the real project.
4. Add Android INTERNET permission.
5. Run flutter pub get.
6. Run flutter analyze.
7. Run on Android device or emulator.
8. Enter RunPod ComfyUI URL.
9. Confirm /system_stats connection.
10. Download profile zip.
11. Save it locally.
12. Open it from Local Profiles.
13. Edit simple fields.
14. Submit generation.
15. Display generated image.
```

Required Android permission:

```xml
<uses-permission android:name="android.permission.INTERNET" />
```

## Step 4: Decide merge readiness

Only consider making PR #1 ready for review or merging after:

```text
- RunPod ComfyUI validation passes.
- Real checkpoint image generation passes.
- Android Flutter app run passes.
- HANDOFF.md is updated with the real validation result.
- PR body is updated with the real validation result.
```

## Step 5: Post-validation priorities

After the real RunPod + Android path passes, revisit future work in this order:

```text
1. Confirm saved profile re-run behavior and image re-upload behavior.
2. Improve error messages.
3. Decide production storage: shared_preferences vs file-based profile storage.
4. Add /object_info-based field metadata support.
5. Add /models-based missing model checks.
6. Add UI workflow import/conversion if needed.
7. Add advanced workflow support such as ControlNet, IPAdapter, FaceDetailer, Upscale.
8. Add bypass, subgraph, and node color support later.
```

## Do not do in the next phase

```text
- Do not merge automatically.
- Do not add automatic custom node installation.
- Do not add automatic model downloads.
- Do not turn the app into a full workflow editor.
- Do not add Playwright/Chromium as required MVP dependency.
- Do not add Google Drive sync.
- Do not add payment/monetization.
```
