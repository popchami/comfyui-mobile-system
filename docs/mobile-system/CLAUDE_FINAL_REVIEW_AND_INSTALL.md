# Claude Final Review and Install Guide

## Purpose

This file is the handoff point for Claude.

The user cannot use a PC right now. The goal is for Claude to review this PR, first confirm whether the edited pre-implementation decisions are still valid based on official ComfyUI/RunPod capabilities and external references, then confirm whether the current work can be installed/tested.

## Repository and PR

Repository:

```text
popchami/comfyui-mobile-system
```

PR:

```text
#1 Add ComfyUI mobile system architecture and MVP scaffold
```

Branch:

```text
docs/mobile-system-spec
```

## Read first

Claude should read these files first:

```text
docs/mobile-system/PRE_CLAUDE_STATUS.md
docs/mobile-system/PROJECT_DIRECTION_GUARDRAILS.md
docs/mobile-system/PRE_IMPLEMENTATION_ALIGNMENT_DECISIONS.md
docs/mobile-system/SYSTEM_INVENTORY_BEFORE_CLAUDE.md
docs/mobile-system/EXISTING_PLATFORMS_REVIEW.md
docs/mobile-system/COMFY_PORTAL_ENDPOINT_REFERENCE_REVIEW.md
docs/mobile-system/CLAUDE_FINAL_REVIEW_AND_INSTALL.md
docs/mobile-system/STATIC_REVIEW_NOTES.md
```

`PRE_IMPLEMENTATION_ALIGNMENT_DECISIONS.md` is the edited decision layer. Treat it as more actionable than the raw inventory files.

`STATIC_REVIEW_NOTES.md` records what was already checked and fixed before runtime validation.

## What changed before this handoff

The handoff is no longer only runtime validation.

Because this project is still before implementation hardens, Claude should first check whether the edited pre-implementation decisions are still correct.

Main question:

```text
Are we rebuilding something ComfyUI or RunPod already provides?
```

If yes, prefer official platform APIs and keep custom work focused on the mobile profile layer.

## Edited pre-implementation decision

Current decision summary:

```text
- Do not discard the current system.
- Do adjust the implementation strategy.
- Use official ComfyUI APIs wherever possible.
- Keep custom code focused on the missing mobile profile layer.
- Move /object_info and /models earlier than originally planned.
- Keep UI workflow conversion optional for now.
- Keep comfy-portal-endpoint as a reference only.
```

Do not broadly rewrite the code before runtime validation unless Claude identifies a true blocker.

## What was added

This PR adds three main parts:

```text
1. ComfyUI-Mobile-Analyzer scaffold
2. HTML mobile prototype
3. Flutter MVP scaffold
```

## Current priority

Do not add new features first.

Priority is:

```text
1. Review edited pre-implementation decisions
2. Review current files
3. Compare current design with official ComfyUI APIs
4. Compare current design with the external comfy-portal-endpoint reference
5. Confirm /object_info and /models should move earlier, but keep full implementation for after minimum runtime validation unless they are blockers
6. Confirm install/test path
7. Fix blocking errors only
8. Confirm ComfyUI custom node loads
9. Confirm Flutter MVP can reach flutter analyze / flutter run path
10. Only then reprioritize future TODOs
```

## Official ComfyUI APIs to consider source-of-truth

Claude should verify whether the current design should use these existing routes before adding custom replacements:

```text
/prompt
/ws
/history/{prompt_id}
/view
/upload/image
/upload/mask
/system_stats
/object_info
/object_info/{node_class}
/models
/models/{folder}
/workflow_templates
```

Important likely adjustment:

```text
/object_info and /models should become near-term priorities after minimum runtime validation.
```

Reason:

```text
They can reduce manual Analyzer guessing for field types, combo choices, node compatibility, and model existence checks.
```

## External reference stance

`comfy-portal-endpoint` is useful as a reference for UI workflow to API workflow conversion.

Do not:

```text
- copy code
- make Playwright/Chromium required for MVP
- turn this project into a generic workflow portal
- adopt automatic dependency installs
```

Use it only as a reference for a future optional UI converter.

## ComfyUI custom node install target

Analyzer source path in this repo:

```text
analyzer/ComfyUI-Mobile-Analyzer/
```

Expected install location inside ComfyUI:

```text
ComfyUI/custom_nodes/ComfyUI-Mobile-Analyzer/
```

Manual install example:

```bash
cd ComfyUI/custom_nodes
git clone <repo-url> temp-comfyui-mobile-system
cp -r temp-comfyui-mobile-system/analyzer/ComfyUI-Mobile-Analyzer ./ComfyUI-Mobile-Analyzer
```

Then restart ComfyUI.

Expected node:

```text
Mobile Profile Exporter
```

Expected category:

```text
mobile_analyzer
```

## ComfyUI runtime checks

After architecture alignment, restart and check:

```text
1. ComfyUI starts without import errors
2. Mobile Profile Exporter appears in the node menu
3. Paste minimal API workflow JSON into workflow_json_text
4. Queue the exporter node
5. Zip appears under ComfyUI/output/mobile_profiles/
6. Zip contains workflow.json and app_profile.json
7. GET /mobile_analyzer/profiles returns a list
8. GET /mobile_analyzer/profiles/{id}/download downloads the zip
```

Minimal workflow example:

```text
analyzer/ComfyUI-Mobile-Analyzer/examples/minimal_api_workflow.json
```

Expected profile example:

```text
analyzer/ComfyUI-Mobile-Analyzer/examples/output_app_profile_example.json
```

## Flutter MVP target

Flutter scaffold path:

```text
mobile-app/flutter_mvp/
```

Current MVP target:

```text
Android-first.
```

Do not treat Flutter Web support as required for this MVP. `GenerateScreen` uses `file_picker` and `dart:io File` for image upload, so Web may fail unless rewritten later.

Current files include:

```text
pubspec.yaml
RUN_CHECKLIST.md
lib/main.dart
lib/models/app_profile.dart
lib/models/local_profile.dart
lib/models/remote_profile.dart
lib/models/generated_image.dart
lib/services/comfy_api_client.dart
lib/services/profile_zip_service.dart
lib/services/local_profile_store.dart
lib/services/workflow_patcher.dart
lib/services/comfy_progress_client.dart
lib/services/history_image_extractor.dart
lib/screens/setup_screen.dart
lib/screens/remote_profiles_screen.dart
lib/screens/local_profiles_screen.dart
lib/screens/generate_screen.dart
```

Important Flutter note:

```text
ComfyApiClient.getRemoteProfiles() returns List<RemoteProfile>.
RemoteProfilesScreen should not use dynamic profile maps anymore.
```

Run commands from:

```text
mobile-app/flutter_mvp
```

Commands:

```bash
flutter pub get
flutter analyze
flutter run
```

Important note:

This folder may still be a scaffold, not a fully generated Flutter platform project. If Flutter requires platform folders, create a normal Flutter project shell and copy the `lib/` folder and `pubspec.yaml` into it.

Example path:

```bash
flutter create comfy_mobile_mvp
cp -r mobile-app/flutter_mvp/lib comfy_mobile_mvp/lib
cp mobile-app/flutter_mvp/pubspec.yaml comfy_mobile_mvp/pubspec.yaml
```

Android Internet permission must exist in the real Android manifest:

```xml
<uses-permission android:name="android.permission.INTERNET" />
```

## Flutter MVP expected behavior

Expected app flow:

```text
SetupScreen
  ↓ Enter ComfyUI URL
  ↓ Check /system_stats
  ↓ Open Remote Profiles
  ↓ Load typed RemoteProfile values from /mobile_analyzer/profiles
  ↓ Save selected profile zip
  ↓ Open Local Profiles
  ↓ Open saved profile
  ↓ Render app_profile.ui.simple fields
  ↓ Select image if image field exists
  ↓ Upload image to /upload/image
  ↓ Patch workflow using patch_targets only
  ↓ Connect /ws with clientId
  ↓ Submit /prompt with same clientId
  ↓ Poll /history/{prompt_id}
  ↓ Extract images
  ↓ Display /view images
```

## Architecture questions before runtime validation

Claude should answer these before making feature changes:

```text
1. Which current custom logic duplicates official ComfyUI APIs?
2. Should /object_info be the first post-validation Analyzer improvement?
3. Should /models and /models/{folder} be the first post-validation model-check improvement?
4. Which /mobile_analyzer routes remain necessary?
5. Should UI workflow conversion stay optional for now?
6. What is the smallest path to validate the mobile profile concept?
```

## Do not change these rules

```text
- Do not turn the app into a full ComfyUI workflow editor yet.
- Do not patch fields outside app_profile.json.patch_targets.
- Do not remove unknown nodes.
- Do not auto-install custom nodes.
- Do not auto-download models.
- Do not make Playwright/Chromium required for MVP.
- Do not modify the saved original workflow when generating. Patch a copy.
- Prefer official ComfyUI APIs over custom reimplementation when they already solve the same problem.
```

## Known areas likely needing fixes

Claude should specifically check these:

```text
1. Dart type errors in Flutter files
2. Whether file_picker + dart:io works for Android target
3. Whether ComfyApiClient.uploadImage signature matches usage
4. Whether ComfyProgressClient constructor uses baseUrl or baseUri consistently
5. Whether /ws clientId parameter name matches current ComfyUI behavior
6. Whether server.py route registration works in current ComfyUI
7. Whether nodes.py output app_profile shape matches Flutter parser
8. Whether generated app_profile includes image fields for LoadImage
9. Whether shared_preferences is acceptable for current profile size
10. Whether Android Internet permission is present in the generated app shell
11. Whether RemoteProfile parsing matches /mobile_analyzer/profiles runtime output
12. Whether /object_info and /models should become near-term work
```

## Pass condition

This work is install-ready when Claude can confirm:

```text
1. Edited pre-implementation decisions are still valid
2. Architecture alignment review is complete
3. No official ComfyUI API is being unnecessarily reimplemented for MVP
4. ComfyUI loads ComfyUI-Mobile-Analyzer
5. Mobile Profile Exporter creates a valid zip
6. Analyzer profile API returns and downloads profile zips
7. Flutter MVP passes flutter pub get
8. Flutter MVP passes flutter analyze or has only documented non-blocking warnings
9. Flutter app can connect to ComfyUI
10. Flutter app can download, save, open, patch, submit, and display at least one generated image
```

## After pass condition

After the install path is confirmed, then revisit:

```text
docs/mobile-system/OPEN_TODOS.md
docs/mobile-system/FUTURE_ISSUES_AND_IMPROVEMENTS.md
```

and reorder future work by priority.
