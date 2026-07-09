# Flutter MVP Run Checklist

## Purpose

This checklist is for the first real Flutter validation of `mobile-app/flutter_mvp`.

The goal is not a polished app. The goal is to confirm that the current MVP flow can run.

## Before running

Confirm these files exist:

```text
pubspec.yaml
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

## Commands

Run from:

```text
mobile-app/flutter_mvp
```

Then run:

```bash
flutter pub get
flutter analyze
flutter run
```

## Expected first app flow

```text
SetupScreen
  ↓ enter ComfyUI URL
  ↓ Check connection
  ↓ Remote profiles
  ↓ Load remote profiles
  ↓ Save selected profile
  ↓ Back to SetupScreen
  ↓ Local profiles
  ↓ Open saved profile
  ↓ Edit simple fields
  ↓ Choose image if image field exists
  ↓ Submit /prompt
  ↓ Watch progress
  ↓ See generated image
```

## Known issues to check

- `main.dart` may need to be re-added if it was blocked by safety checks during earlier scaffold creation.
- Android Internet permission may be required in the real app shell.
- `file_picker` may need Android/iOS platform setup depending on final Flutter project generation.
- `Image.network` may fail if RunPod/ComfyUI URL requires a session, has CORS/proxy issues, or expires.
- `ComfyProgressClient` uses `/ws?clientId=...`; confirm ComfyUI version accepts this parameter name.
- `LocalProfileStore` currently uses shared_preferences and stores JSON directly. This is acceptable for MVP, but large workflows may need file storage later.

## Pass condition

MVP pass means:

```text
A profile zip can be downloaded, saved locally, opened, patched, submitted to /prompt, and at least one generated image can be displayed.
```

## Safety rule

Do not turn this into a full workflow editor yet.

```text
Only patch fields listed in app_profile.json.patch_targets.
```
