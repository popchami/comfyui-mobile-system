# Android Validation Runbook

## Purpose

This is the step-by-step runbook for validating the Flutter Android MVP app against a real ComfyUI URL.

Use this after RunPod validation passes or when a real ComfyUI URL is available.

## Current rule

```text
Do not merge PR #1 until Android validation and RunPod validation both pass.
```

## What this runbook proves

```text
The Android app can connect to ComfyUI,
download a profile zip,
save it locally,
open it,
render simple controls,
patch only patch_targets,
submit generation,
and display at least one generated image.
```

## Before starting

Confirm:

```text
- Repository: popchami/comfyui-mobile-system
- Branch: docs/mobile-system-spec
- PR: #1
- PR is still Draft
- A real ComfyUI URL is available
- RunPod validation passed or ComfyUI is known working
- At least one remote profile zip exists
```

Rules:

```text
- Do not merge PR.
- Do not turn app into workflow editor.
- Do not add auto-downloads.
- Do not add auto-installs.
- Validate current MVP path only.
```

## Step 1: Create real Flutter Android project shell

`mobile-app/flutter_mvp` is a scaffold. If Android platform folders are missing, create a real Flutter shell and copy in the MVP source.

Record:

```text
Flutter version:
Android device/emulator:
Android version:
```

Check:

```text
Real Flutter project shell exists: PASS / FAIL
mobile-app/flutter_mvp/lib copied: PASS / FAIL
pubspec.yaml copied: PASS / FAIL
```

## Step 2: Add Android INTERNET permission

Required permission:

```xml
<uses-permission android:name="android.permission.INTERNET" />
```

Expected location:

```text
android/app/src/main/AndroidManifest.xml
```

Place it under the root `<manifest>` element, outside `<application>`.

Check:

```text
INTERNET permission added: PASS / FAIL
```

## Step 3: Flutter checks

Run:

```text
flutter pub get
flutter analyze
flutter run
```

Check:

```text
flutter pub get: PASS / FAIL
flutter analyze: PASS / FAIL
flutter run: PASS / FAIL
App opens on Android: PASS / FAIL
```

## Step 4: Setup connection

In the app:

```text
Open SetupScreen
Enter current ComfyUI URL
Run connection check
```

Check:

```text
SetupScreen opens: PASS / FAIL
/system_stats connection works: PASS / FAIL
Friendly error if connection fails: PASS / FAIL / not checked
```

## Step 5: Remote profiles

In the app:

```text
Open Remote Profiles
Load profiles from /mobile_analyzer/profiles
Select a profile
Download profile zip
Save locally
```

Check:

```text
Remote profile list loads: PASS / FAIL
Profile zip downloads: PASS / FAIL
Profile saves locally: PASS / FAIL
```

## Step 6: Local profiles

In the app:

```text
Open Local Profiles
Open saved profile
```

Check:

```text
Local profile list shows saved profile: PASS / FAIL
Saved profile opens: PASS / FAIL
app_profile parses: PASS / FAIL
workflow parses: PASS / FAIL
```

## Step 7: Generate screen

Check:

```text
GenerateScreen renders simple fields: PASS / FAIL
Prompt field appears if detected: PASS / FAIL / not applicable
Negative field appears if detected: PASS / FAIL / not applicable
Seed field appears if detected: PASS / FAIL / not applicable
Steps field appears if detected: PASS / FAIL / not applicable
CFG field appears if detected: PASS / FAIL / not applicable
Width/height fields appear if detected: PASS / FAIL / not applicable
Image picker appears if LoadImage detected: PASS / FAIL / not applicable
```

## Step 8: Submit generation

If image input is required:

```text
Select image from Android file picker
Upload image through /upload/image
```

Then:

```text
Edit one simple field
Submit generation
```

Check:

```text
Image picker works: PASS / FAIL / not applicable
Image upload works: PASS / FAIL / not applicable
Workflow patches only patch_targets: PASS / FAIL / not directly verified
/prompt submit works: PASS / FAIL
/ws progress received: PASS / FAIL
/history result available: PASS / FAIL
/view image displays: PASS / FAIL
```

## Step 9: Record result

Use:

```text
docs/mobile-system/VALIDATION_RESULT_TEMPLATES.md
Template 2: Android Flutter validation result
```

Update:

```text
docs/mobile-system/HANDOFF.md
```

If Android validation changes merge readiness, update PR body too.

## Pass condition

Android validation is PASS only if:

```text
- App runs on Android.
- ComfyUI connection works.
- Remote profile zip downloads.
- Profile saves locally.
- Saved profile opens.
- GenerateScreen renders controls.
- /prompt submit works.
- /ws and /history work.
- /view image displays in app.
```

## Partial condition

Android validation is PARTIAL if:

```text
- App runs and profiles load,
  but generation or image display does not complete.
```

## Fail condition

Android validation is FAIL if:

```text
- App cannot run.
- App cannot connect to ComfyUI.
- Remote profile zip cannot be downloaded or opened.
```

## Common failures to capture

```text
- INTERNET permission missing
- RunPod URL expired
- CORS/proxy/URL issue
- file_picker issue
- image upload failed
- /prompt rejected
- WebSocket failed
- /view image not loading
```

## Next action after PASS

```text
If RunPod validation also passed, review merge readiness with VALIDATION_RESULT_TEMPLATES.md Template 5.
```

## Next action after PARTIAL or FAIL

```text
1. Fill DEBUG_REPORT_TEMPLATE.md.
2. Fill VALIDATION_RESULT_TEMPLATES.md.
3. Fix only the smallest blocker.
4. Update HANDOFF.md.
5. Keep PR Draft.
```
