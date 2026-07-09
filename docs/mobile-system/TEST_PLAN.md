# Test Plan

## Purpose

This document defines the checks needed before merging the mobile system design and skeleton into `main`.

The goal is not full production validation. The goal is to confirm that the architecture can work end-to-end in the intended RunPod + Android path.

## Current validation status

Claude already completed architecture review and a limited CPU-only runtime pass.

See:

```text
docs/mobile-system/RUNTIME_VALIDATION_RESULT.md
docs/mobile-system/BLOCKERS_AFTER_CLAUDE.md
docs/mobile-system/NEXT_PHASE_PLAN.md
```

Already confirmed:

```text
- Architecture alignment review passed.
- ComfyUI can load the Analyzer in a CPU-only sandbox.
- Mobile Profile Exporter appears via /object_info.
- Profile zip export works after OUTPUT_NODE fix.
- /mobile_analyzer/profiles works.
- /mobile_analyzer/profiles/{id}/download works.
- Flutter pub get passed.
- Flutter analyze passed for PR lib/ source.
```

Still required before merge:

```text
- RunPod GPU validation with real checkpoint.
- Android device/emulator validation.
- End-to-end generated image display in the Android app.
```

## Phase 1: Documentation review

Status:

```text
Complete for initial PR direction.
Keep docs updated when real validation results change.
```

Check:

- `app_profile.json` has enough information for the mobile app.
- `patch_targets` are safe and clear.
- UI visibility levels are practical.
- MVP scope is not too large.
- Analyzer and mobile app responsibilities are separated correctly.
- Unknown nodes are preserved.
- Missing requirements are reported, not auto-installed.

Pass condition:

- Reviewer confirms the design is understandable and implementable.
- Any blocking issues are fixed in the PR branch.

## Phase 2: Static code review

Status:

```text
Complete for first pass. Re-check after any new code changes.
```

Check analyzer skeleton files:

- `__init__.py`
- `nodes.py`
- `server.py`
- `mobile-app/prototype/profile-storage.js`
- `mobile-app/prototype/stored-profile-ui.js`
- `mobile-app/prototype/comfy-progress.js`

Check:

- No auto-install behavior.
- No model download behavior.
- No arbitrary shell execution.
- Output path is limited to `output/mobile_profiles/`.
- Zip contains `workflow.json` and `app_profile.json`.
- Unknown nodes are not removed.
- Generated profile uses `schema_version`.
- Positive and negative prompt detection uses KSampler connections.
- Width, height, and batch are detected from EmptyLatentImage.
- LoadImage creates an image field.
- Detected model names are reported as unverified references.
- Local profile storage uses browser localStorage only in the prototype.
- Local profile storage can upsert, delete, and clear profiles.
- Stored profile UI can save, load, delete, and clear profiles.
- WebSocket helper uses a generated client_id.
- `/prompt` payload includes the same client_id used by `/ws`.

Pass condition:

- No obvious unsafe behavior.
- No obvious syntax or import issue.

## Phase 3: ComfyUI runtime smoke test

Status:

```text
Passed in CPU-only sandbox.
Must be repeated on RunPod after latest PR branch changes.
```

Install draft custom node folder into ComfyUI custom_nodes.

Expected location:

```text
ComfyUI/custom_nodes/ComfyUI-Mobile-Analyzer/
```

Check:

- ComfyUI starts.
- No import error after WEB_DIRECTORY cleanup.
- `MobileProfileExporter` appears in node menu or /object_info.
- Node accepts pasted API-format workflow JSON.
- Node creates a zip under `output/mobile_profiles/`.
- Zip can be opened.
- Zip contains `workflow.json`.
- Zip contains `app_profile.json`.
- `app_profile.json.ui.simple` contains prompt.
- `app_profile.json.ui.simple` contains negative when workflow has KSampler negative connection.
- `app_profile.json.ui.simple` contains seed / steps / cfg.
- `app_profile.json.ui.simple` contains width / height / batch when EmptyLatentImage exists.
- `app_profile.json.ui.simple` contains image field when LoadImage exists.

Pass condition:

- One valid zip is created without crashing ComfyUI.
- app_profile.json contains the expected simple fields.

## Phase 4: Analyzer API smoke test

Status:

```text
Passed in CPU-only sandbox.
Must be repeated on RunPod.
```

After a zip exists, check:

```text
GET /mobile_analyzer/profiles
GET /mobile_analyzer/profiles/{id}/download
```

Pass condition:

- Profile list returns at least one profile.
- Download endpoint returns the zip.

## Phase 5: RunPod real model generation test

Status:

```text
Not completed yet.
Required before merge.
```

Check:

- Use a RunPod ComfyUI environment with an existing approved checkpoint model.
- Do not auto-download models.
- Export or load a profile that references an actually installed model.
- Submit a workflow through `/prompt`.
- Monitor `/ws`.
- Read `/history/{prompt_id}`.
- Fetch result image through `/view`.

Pass condition:

```text
At least one image is generated with a real model and can be fetched through /view.
```

## Phase 6: Flutter Android app test

Status:

```text
Not completed yet.
Required before merge.
```

Use `mobile-app/flutter_mvp` as the source scaffold.

Check:

- Create a real Flutter Android project shell if platform folders are missing.
- Copy `lib/` and `pubspec.yaml` from `mobile-app/flutter_mvp`.
- Add Android INTERNET permission.
- Run `flutter pub get`.
- Run `flutter analyze`.
- Run on Android device or emulator.
- Register ComfyUI URL.
- Check `/system_stats`.
- Fetch profile list.
- Download selected remote profile zip.
- Save local profile.
- Reload saved profile from local profile list.
- Render simple fields.
- Render image fields as file pickers.
- Upload selected image to `/upload/image` if the workflow needs it.
- Patch prompt / negative / seed / steps / cfg / width / height / batch.
- Submit patched workflow to `/prompt`.
- Poll `/history/{prompt_id}`.
- Display output image with `/view`.

Required Android permission:

```xml
<uses-permission android:name="android.permission.INTERNET" />
```

Pass condition:

- One profile zip can be downloaded without manual JSON paste.
- One downloaded profile can be saved and reloaded.
- One image can be generated from a profile imported through the new flow.
- Progress messages appear while generation is running.
- If the workflow uses LoadImage, one selected smartphone image can be uploaded and used.

## Phase 7: Local storage helper test

Status:

```text
Prototype helper test still useful, but Android validation is now higher priority.
```

Use the Saved Profiles section in the prototype if browser-based prototype validation is needed.

Check:

- Save current profile.
- Reload the page.
- Stored profile remains visible.
- Load stored profile.
- Delete stored profile.
- Clear all stored profiles.

Pass condition:

- Imported profiles can be saved and loaded from browser localStorage using the prototype UI.

## Merge rule

Do not merge to `main` until:

```text
1. Architecture review remains valid.
2. CPU-only runtime blocker fixes remain in place.
3. RunPod ComfyUI validation passes.
4. Real checkpoint image generation passes.
5. Android device/emulator validation passes.
6. HANDOFF.md is updated with final validation results.
7. PR body is updated with final validation results.
```
