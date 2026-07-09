# Static Review Notes

## Purpose

This file records static reviews performed before real RunPod and Android runtime validation.

The user cannot use a PC right now, so this review focuses on obvious source-level mismatches that can be fixed without running ComfyUI or Flutter.

## Latest static review follow-up

Date: 2026-07-09

Runtime used:

```text
RunPod: no
Android runtime: no
Flutter runtime: no
Termux: no
```

Result:

```text
Static cross-file review completed.
Low-risk issues were fixed on branch docs/mobile-system-spec.
Legacy HTML behavior was reviewed and useful app-side behavior was reused.
Generated UI collapsible grouping was implemented in Flutter MVP.
Seed reuse was implemented for the current generation screen session.
PR remains Draft.
Runtime validation is still required.
```

Fixed in this pass:

```text
1. mobile-app/flutter_mvp/lib/services/comfy_api_client.dart
   - Fixed URL path joining so path-based ComfyUI URLs are preserved.
   - Example: https://host/proxy/8188 + /system_stats -> https://host/proxy/8188/system_stats

2. mobile-app/flutter_mvp/lib/services/comfy_progress_client.dart
   - Fixed WebSocket URL path joining so path-based ComfyUI URLs are preserved.
   - Example: https://host/proxy/8188 + /ws -> wss://host/proxy/8188/ws

3. mobile-app/prototype/comfy-progress.js
   - Fixed prototype WebSocket URL path joining for path-based proxy URLs.

4. docs/mobile-system/PR_BODY_UPDATE_DRAFT.md
   - Fixed nested Markdown code fences by using a four-backtick outer fence.
   - Added SMARTPHONE_ONLY_COMPLETION_REPORT.md to the suggested PR source-of-truth list.

5. mobile-app/flutter_mvp/lib/screens/generate_screen.dart
   - Reused proven legacy HTML behavior: keep /history polling as the completion fallback after /prompt.
   - Temporary /history errors no longer immediately fail the generation flow.
   - WebSocket executing null now reports that execution is complete and history is loading.

6. mobile-app/flutter_mvp/lib/screens/setup_screen.dart
   - Reused proven legacy HTML behavior: remember and restore the ComfyUI URL.
   - Uses shared_preferences instead of browser localStorage.
   - Saves the normalized URL after connection and before opening remote profiles.

7. mobile-app/flutter_mvp/lib/screens/generate_screen.dart
   - Reused proven legacy HTML behavior: show selected input image preview before generation.
   - Uses Image.file for selected image fields.

8. mobile-app/flutter_mvp/lib/screens/generate_screen.dart
   - Reused proven legacy HTML behavior: add generated images to an in-session history list.
   - Deduplicates generated images by type/subfolder/filename.
   - Displays a horizontal Session history strip.

9. mobile-app/flutter_mvp/lib/screens/generate_screen.dart
   - Reused proven legacy HTML behavior: open generated images in a larger preview.
   - Uses a dialog with InteractiveViewer.

10. mobile-app/flutter_mvp/lib/screens/generate_screen.dart
   - Implements generated field grouping from analyzed profile fields.
   - Core Inputs remain visible.
   - Basic Generation Settings, Size / Output, Advanced Workflow Features, and Expert / Debug are collapsed with ExpansionTile.
   - If no core field is detected, the first editable field is shown as a fallback core field.

11. mobile-app/flutter_mvp/lib/screens/generate_screen.dart
   - Reuses the last submitted seed within the current generation screen session.
   - Detects seed fields from field_id / label / section / type.
   - Captures the current seed before /prompt submission.
   - Shows a Use last seed button for seed fields when a last seed exists.
   - Still patches workflow only through patch_targets.
```

Legacy HTML reference:

```text
docs/mobile-system/LEGACY_HTML_REUSE_NOTES.md
```

Generated UI layout rules:

```text
docs/mobile-system/UI_VISIBILITY_RULES.md
docs/mobile-system/MOBILE_APP_SPEC.md
```

Still not proven by static review:

```text
- RunPod ComfyUI startup with Analyzer.
- Real profile zip export on RunPod.
- Real /prompt -> /ws -> /history -> /view generation path.
- Real Android flutter run.
- Real Android image picker / upload / display path.
- Real Android session history rendering.
- Real Android preview dialog interaction.
- Real Android generated field grouping layout.
- Real Android seed reuse interaction.
```

## Reviewed areas

```text
analyzer/ComfyUI-Mobile-Analyzer/nodes.py
analyzer/ComfyUI-Mobile-Analyzer/server.py
analyzer/ComfyUI-Mobile-Analyzer/__init__.py
analyzer/ComfyUI-Mobile-Analyzer/examples/output_app_profile_example.json
profiles/flux1_dev/normal/comfyui_mobile.html
profiles/flux2_klein/normal/comfyui_mobile.html
profiles/flux_full/comfyui_mobile.html
profiles/flux1_dev/pixelart/comfyui_pixelart.html
profiles/flux1_dev/icon/comfyui_icon_mobile.html
profiles/sdxl/chibi/comfyui_sdxl_chibi.html
profiles/sdxl/pixelart/comfyui_sdxl_pixelart.html
mobile-app/flutter_mvp/lib/main.dart
mobile-app/flutter_mvp/lib/models/local_profile.dart
mobile-app/flutter_mvp/lib/models/remote_profile.dart
mobile-app/flutter_mvp/lib/services/comfy_api_client.dart
mobile-app/flutter_mvp/lib/services/comfy_progress_client.dart
mobile-app/flutter_mvp/lib/services/local_profile_store.dart
mobile-app/flutter_mvp/lib/services/profile_zip_service.dart
mobile-app/flutter_mvp/lib/services/workflow_patcher.dart
mobile-app/flutter_mvp/lib/screens/setup_screen.dart
mobile-app/flutter_mvp/lib/screens/remote_profiles_screen.dart
mobile-app/flutter_mvp/lib/screens/generate_screen.dart
mobile-app/prototype/comfy-progress.js
docs/mobile-system/PR_BODY_UPDATE_DRAFT.md
```

## Legacy HTML behavior reused

The existing normal HTML flow already used the practical pattern:

```text
saved ComfyUI URL restore
/prompt with client_id
/ws for progress when available
/history/{prompt_id} as the reliable completion/result fallback
/view for generated images
/upload/image for input images
local preview for selected input images
session generated image history
larger generated image preview
seed reuse
```

The new Flutter MVP now follows the same safety idea more closely.

Do not copy legacy prompt/profile content directly into the dynamic app. Only reuse behavior patterns.

## Generated UI grouping implemented

The Flutter MVP now applies the current generated UI rule:

```text
Core Inputs: open
Basic Generation Settings: collapsed
Size / Output: collapsed
Advanced Workflow Features: collapsed
Expert / Debug: collapsed
```

Grouping is currently an app-side fallback based on:

```text
field_id
label
type
section
```

When Analyzer later emits explicit section metadata, that metadata should replace or refine the fallback grouping.

## Seed reuse implemented

The Flutter MVP now keeps the last submitted seed for the current generation screen session.

Current scope:

```text
- Session-only.
- Not persisted across app restarts.
- Does not bypass patch_targets.
- Does not assume all workflows have seed.
```

Future improvement:

```text
Persist last seed per profile after Android validation passes.
```

## Previously fixed during static review

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

### 5. Analyzer profile API metadata

Updated:

```text
analyzer/ComfyUI-Mobile-Analyzer/server.py
```

The profile list now includes:

```text
id
name
file
status
size_bytes
modified_at
download_url
```

Download lookup is now more tolerant if a caller accidentally passes an id with `.zip` included.

### 6. Example app_profile updated

Updated:

```text
analyzer/ComfyUI-Mobile-Analyzer/examples/output_app_profile_example.json
```

The example now matches current Analyzer output shape more closely:

```text
profile_version 0.2.1
prompt / negative
width / height / batch
seed / steps / cfg / sampler / scheduler / denoise
current patch_target_id format
unverified model warnings
exists_in_comfyui null
```

### 7. Typed Flutter remote profile handling

Added:

```text
mobile-app/flutter_mvp/lib/models/remote_profile.dart
```

Updated:

```text
mobile-app/flutter_mvp/lib/services/comfy_api_client.dart
mobile-app/flutter_mvp/lib/screens/remote_profiles_screen.dart
```

`getRemoteProfiles()` now returns typed `List<RemoteProfile>` values instead of `List<dynamic>`.

RemoteProfilesScreen now uses:

```text
profile.id
profile.name
profile.file
profile.sizeBytes
profile.modifiedAt
```

This reduces dynamic typing before Claude runs `flutter analyze`.

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

## Still needs runtime validation by Claude or another runtime environment

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
6. saved ComfyUI URL restore
7. selected image preview
8. /ws connection with clientId
9. /prompt submission with same clientId
10. /history polling and /view image display
11. session history strip
12. larger generated image preview dialog
13. generated field grouping layout
14. seed reuse interaction
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

## Next action for runtime validation

Use:

```text
docs/mobile-system/RUNPOD_VALIDATION_RUNBOOK.md
docs/mobile-system/ANDROID_VALIDATION_RUNBOOK.md
```

For short AI handoff, use:

```text
docs/mobile-system/AI_MINIMAL_HANDOFF_PROMPTS.md
```
