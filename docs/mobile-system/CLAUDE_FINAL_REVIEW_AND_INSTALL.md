# Claude Final Review and Install Guide

## Purpose

This file is the handoff point for Claude.

The user cannot use a PC right now. The goal is for Claude to review this PR and confirm whether the current work can be installed/tested, then continue to the minimum fixes required for installation.

## Repository and PR

Repository:

```text
popchami/comfyui-mobile-system
```

PR:

```text
#1 Add ComfyUI mobile system architecture specs
```

Branch:

```text
docs/mobile-system-spec
```

## Read first

Claude should read these two files first:

```text
docs/mobile-system/CLAUDE_FINAL_REVIEW_AND_INSTALL.md
docs/mobile-system/STATIC_REVIEW_NOTES.md
```

`STATIC_REVIEW_NOTES.md` records what was already checked and fixed before runtime validation.

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
1. Review current files
2. Confirm install/test path
3. Fix blocking errors
4. Confirm ComfyUI custom node loads
5. Confirm Flutter MVP can reach flutter analyze / flutter run path
6. Only then reprioritize future TODOs
```

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

After restart, check:

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
  ↓ Load /mobile_analyzer/profiles
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

## Do not change these rules

```text
- Do not turn the app into a full ComfyUI workflow editor yet.
- Do not patch fields outside app_profile.json.patch_targets.
- Do not remove unknown nodes.
- Do not auto-install custom nodes.
- Do not auto-download models.
- Do not modify the saved original workflow when generating. Patch a copy.
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
```

## Pass condition

This work is install-ready when Claude can confirm:

```text
1. ComfyUI loads ComfyUI-Mobile-Analyzer
2. Mobile Profile Exporter creates a valid zip
3. Analyzer profile API returns and downloads profile zips
4. Flutter MVP passes flutter pub get
5. Flutter MVP passes flutter analyze or has only documented non-blocking warnings
6. Flutter app can connect to ComfyUI
7. Flutter app can download, save, open, patch, submit, and display at least one generated image
```

## After pass condition

After the install path is confirmed, then revisit:

```text
docs/mobile-system/OPEN_TODOS.md
```

and reorder future work by priority.
