# Static Review Notes

## Purpose

This file records the static review performed before handing the PR to Claude for runtime install checks.

The user cannot use a PC right now, so this review focuses on obvious source-level mismatches that can be fixed without running ComfyUI or Flutter.

## Reviewed areas

```text
analyzer/ComfyUI-Mobile-Analyzer/nodes.py
analyzer/ComfyUI-Mobile-Analyzer/server.py
analyzer/ComfyUI-Mobile-Analyzer/__init__.py
mobile-app/flutter_mvp/lib/main.dart
mobile-app/flutter_mvp/lib/models/local_profile.dart
mobile-app/flutter_mvp/lib/services/comfy_api_client.dart
mobile-app/flutter_mvp/lib/services/comfy_progress_client.dart
mobile-app/flutter_mvp/lib/services/local_profile_store.dart
mobile-app/flutter_mvp/lib/services/profile_zip_service.dart
mobile-app/flutter_mvp/lib/services/workflow_patcher.dart
mobile-app/flutter_mvp/lib/screens/generate_screen.dart
```

## Fixed during static review

### 1. `nodes.py` connection detection

Before:

```python
return isinstance(value, list) and len(value) == 2 and isinstance(value[0], str)
```

Problem:

ComfyUI connection references may use a numeric node id in the first slot depending on source/export style.

Fixed:

```python
if not isinstance(value, list) or len(value) != 2:
    return False
return isinstance(value[0], (str, int)) and isinstance(value[1], int)
```

### 2. Analyzer profile version bump

`nodes.py` now emits:

```json
"profile_version": "0.2.1"
```

This marks the connection-detection fix.

### 3. Flutter app entrypoint

Added:

```text
mobile-app/flutter_mvp/lib/main.dart
```

This starts:

```text
ComfyMobileMvpApp -> SetupScreen
```

### 4. Flutter run checklist updated

Updated:

```text
mobile-app/flutter_mvp/RUN_CHECKLIST.md
```

Added Android Internet permission note and real Flutter project shell caveat.

## Flutter target clarification

The current Flutter MVP is Android-first.

Reason:

```text
GenerateScreen uses file_picker + dart:io File for image upload.
```

Do not treat Web support as required for this MVP. If Claude tests Web and sees `dart:io` issues, that should not block Android MVP validation.

## Local storage clarification

`LocalProfileStore` currently uses `shared_preferences`.

This is acceptable for MVP install validation because it proves save/load behavior. It is not the final production storage plan for large workflows.

Future production storage should probably move to file-based local storage for:

```text
workflow.json
app_profile.json
source_info.json
preview image
history snapshots
```

## Still needs runtime validation by Claude

### ComfyUI side

```text
1. Confirm custom node pack imports without error.
2. Confirm Mobile Profile Exporter appears in ComfyUI.
3. Confirm zip output under ComfyUI/output/mobile_profiles/.
4. Confirm /mobile_analyzer/profiles route registration works.
5. Confirm /mobile_analyzer/profiles/{id}/download returns the zip.
```

### Flutter side

```text
1. flutter pub get
2. flutter analyze
3. flutter run on Android target
4. Android Internet permission in generated platform shell
5. file_picker behavior on Android
6. /ws connection with clientId
7. /prompt submission with same clientId
8. /history polling and /view image display
```

## Known caveats

### Flutter scaffold vs full Flutter project

`mobile-app/flutter_mvp` contains a Flutter scaffold. It may not include full platform folders such as:

```text
android/
ios/
web/
```

If `flutter run` requires a complete shell, Claude should create a real Flutter project and copy over:

```text
lib/
pubspec.yaml
```

### SharedPreferences storage

Current local profile storage uses `shared_preferences`.

This is acceptable for MVP validation, but file-based storage may be needed later for large workflows.

### Analyzer model checks

Analyzer currently reports detected model names as unverified references. It does not yet confirm model files exist.

### object_info checks

Analyzer does not yet inspect ComfyUI `object_info`.

### UI workflow conversion

Analyzer currently expects API-style workflow JSON pasted into `workflow_json_text`. UI workflow to API workflow conversion is not completed.

## Next action for Claude

Claude should start with:

```text
docs/mobile-system/CLAUDE_FINAL_REVIEW_AND_INSTALL.md
```

Then use this file to understand what has already been statically reviewed.
