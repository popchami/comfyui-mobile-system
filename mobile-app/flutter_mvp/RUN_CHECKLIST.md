# Flutter MVP Run Checklist

## Purpose

This checklist is for the first real Android validation of `mobile-app/flutter_mvp`.

The goal is not a polished app. The goal is to confirm that the current MVP flow can run on Android against a real ComfyUI URL.

## Current validation status

Already confirmed in Claude's limited CPU-only validation:

```text
flutter pub get       -> PASS
flutter analyze       -> PASS for PR lib/ source
Dart service flow     -> partially exercised against live ComfyUI sandbox
```

Still not confirmed:

```text
Android device/emulator run
Native file_picker behavior
Android UI navigation/rendering
End-to-end display of a real generated image
```

## Before running

Confirm these files exist:

```text
pubspec.yaml
lib/main.dart
lib/models/app_profile.dart
lib/models/local_profile.dart
lib/models/generated_image.dart
lib/models/remote_profile.dart
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

## Important: this folder is a scaffold

`mobile-app/flutter_mvp` may not contain a full generated Flutter platform shell.

If Android platform folders are missing, create a real Flutter project shell first, then copy this scaffold into it.

Example flow:

```bash
flutter create comfy_mobile_mvp
cd comfy_mobile_mvp
rm -rf lib
cp -r /path/to/comfyui-mobile-system/mobile-app/flutter_mvp/lib ./lib
cp /path/to/comfyui-mobile-system/mobile-app/flutter_mvp/pubspec.yaml ./pubspec.yaml
```

## Android permission note

A real generated Flutter Android project must include Internet permission.

Expected Android manifest permission:

```xml
<uses-permission android:name="android.permission.INTERNET" />
```

Add it to:

```text
android/app/src/main/AndroidManifest.xml
```

Place it under the root `<manifest>` element, outside `<application>`.

## Commands

Run from the real generated Flutter project shell:

```bash
flutter pub get
flutter analyze
flutter run
```

## Expected first app flow

```text
SetupScreen
  ↓ enter ComfyUI URL
  ↓ Check connection via /system_stats
  ↓ Remote profiles
  ↓ Load remote profiles from /mobile_analyzer/profiles
  ↓ Save selected profile zip
  ↓ Back to SetupScreen
  ↓ Local profiles
  ↓ Open saved profile
  ↓ Edit simple fields
  ↓ Choose image if image field exists
  ↓ Submit /prompt
  ↓ Watch /ws progress
  ↓ Read /history/{prompt_id}
  ↓ See generated image through /view
```

## Known issues to check

- `file_picker` may need Android/iOS platform setup depending on final Flutter project generation.
- `Image.network` may fail if RunPod/ComfyUI URL requires a session, has proxy issues, or expires.
- `ComfyProgressClient` uses `/ws?clientId=...`; confirm the target ComfyUI version accepts this parameter name.
- `LocalProfileStore` currently uses shared_preferences and stores JSON directly. This is acceptable for MVP, but large workflows may need file storage later.
- RunPod public/proxy URLs may change between pod sessions. Re-enter the current ComfyUI URL before testing.

## Pass condition

MVP Android pass means:

```text
A profile zip can be downloaded from RunPod ComfyUI, saved locally, opened, patched, submitted to /prompt, and at least one generated image can be displayed on Android.
```

## Safety rule

Do not turn this into a full workflow editor yet.

```text
Only patch fields listed in app_profile.json.patch_targets.
```
