# Pre-Claude Status Summary

## Purpose

This file originally summarized the PR state before handing it to Claude.

Claude has now completed the architecture alignment review and a limited CPU-only runtime validation pass. This file is kept for history, but the current source of truth is now:

```text
docs/mobile-system/HANDOFF.md
docs/mobile-system/RUNTIME_VALIDATION_RESULT.md
docs/mobile-system/BLOCKERS_AFTER_CLAUDE.md
docs/mobile-system/NEXT_PHASE_PLAN.md
```

## Current status after Claude validation

```text
Architecture alignment review: complete
Limited CPU-only runtime validation: complete
OUTPUT_NODE blocker: fixed
WEB_DIRECTORY cleanup: committed after GitHub sanity check
RunPod GPU validation: not complete
Android device/emulator validation: not complete
PR state: Draft
Merge status: do not merge
```

## Current edited decision

The inventory has been edited into a decision file:

```text
docs/mobile-system/PRE_IMPLEMENTATION_ALIGNMENT_DECISIONS.md
```

Current decision summary remains valid:

```text
- Do not discard the current system.
- Do adjust the implementation strategy.
- Use official ComfyUI APIs wherever possible.
- Keep custom code focused on the missing mobile profile layer.
- Move /object_info and /models earlier than originally planned.
- Keep UI workflow conversion optional for now.
- Keep comfy-portal-endpoint as a reference only.
```

## PR state

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

Current state:

```text
state: open
draft: true
merged: false
Do not merge yet.
```

## What Claude already did

Claude previously read these files in order:

```text
docs/mobile-system/PRE_CLAUDE_STATUS.md
docs/mobile-system/PROJECT_DIRECTION_GUARDRAILS.md
docs/mobile-system/PRE_IMPLEMENTATION_ALIGNMENT_DECISIONS.md
docs/mobile-system/SYSTEM_INVENTORY_BEFORE_CLAUDE.md
docs/mobile-system/EXISTING_PLATFORMS_REVIEW.md
docs/mobile-system/COMFY_PORTAL_ENDPOINT_REFERENCE_REVIEW.md
docs/mobile-system/PRIORITY_CONFLICT_REVIEW.md
docs/mobile-system/CLAUDE_FINAL_REVIEW_AND_INSTALL.md
docs/mobile-system/STATIC_REVIEW_NOTES.md
```

Claude then performed the first limited runtime validation in a CPU-only aarch64 sandbox.

## Runtime validation result summary

Already passed in the limited validation pass:

```text
1. ComfyUI starts with ComfyUI-Mobile-Analyzer installed.
2. Mobile Profile Exporter appears via /object_info.
3. Mobile Profile Exporter creates a zip after OUTPUT_NODE fix.
4. Zip contains workflow.json and app_profile.json.
5. /mobile_analyzer/profiles returns profile metadata.
6. /mobile_analyzer/profiles/{id}/download downloads the zip.
7. Flutter MVP passes flutter pub get.
8. Flutter MVP passes flutter analyze for PR lib/ source.
```

Partial / still unverified:

```text
9. Flutter Android app can connect to ComfyUI.
10. Flutter Android app can download, save, open, patch, submit, and display at least one generated image.
```

Reason:

```text
The validation sandbox had no RunPod GPU, no real checkpoint model, and no Android emulator/device.
```

## Important fixes already included

```text
analyzer/ComfyUI-Mobile-Analyzer/nodes.py
- Added OUTPUT_NODE = True to MobileProfileExporter.

analyzer/ComfyUI-Mobile-Analyzer/__init__.py
- Removed unused WEB_DIRECTORY = "web" declaration.
```

## Main components in this PR

### 1. Documentation

```text
docs/mobile-system/
```

Important docs:

```text
README.md
ARCHITECTURE.md
APP_PROFILE_SCHEMA.md
WORKFLOW_PATCH_RULES.md
UI_VISIBILITY_RULES.md
MVP_SCOPE.md
ANALYZER_SPEC.md
MOBILE_APP_SPEC.md
PROJECT_DIRECTION_GUARDRAILS.md
PRE_IMPLEMENTATION_ALIGNMENT_DECISIONS.md
SYSTEM_INVENTORY_BEFORE_CLAUDE.md
EXISTING_PLATFORMS_REVIEW.md
COMFY_PORTAL_ENDPOINT_REFERENCE_REVIEW.md
PRE_CLAUDE_DONE.md
PRE_CLAUDE_STATUS.md
PRIORITY_CONFLICT_REVIEW.md
CLAUDE_COPYPASTE_PROMPT.md
CLAUDE_FINAL_REVIEW_AND_INSTALL.md
STATIC_REVIEW_NOTES.md
OPEN_TODOS.md
FUTURE_ISSUES_AND_IMPROVEMENTS.md
EXTERNAL_REFERENCES.md
RUNTIME_VALIDATION_RESULT.md
BLOCKERS_AFTER_CLAUDE.md
NEXT_PHASE_PLAN.md
```

### 2. ComfyUI-Mobile-Analyzer scaffold

```text
analyzer/ComfyUI-Mobile-Analyzer/
```

Important files:

```text
__init__.py
nodes.py
server.py
examples/minimal_api_workflow.json
examples/output_app_profile_example.json
```

Current Analyzer behavior:

```text
- Adds Mobile Profile Exporter node
- Accepts pasted API workflow JSON text
- Exports workflow.json + app_profile.json into a zip
- Saves zip under output/mobile_profiles
- Detects prompt / negative / width / height / batch / seed / steps / cfg / sampler / scheduler / denoise
- Detects basic model references as unverified
- Preserves unknown workflow nodes
- Provides profile list/download routes
```

### 3. HTML prototype

```text
mobile-app/prototype/
```

Current prototype behavior:

```text
- Set ComfyUI URL
- Check /system_stats
- Fetch /mobile_analyzer/profiles
- Download remote profile zip
- Import local profile zip
- Extract app_profile.json and workflow.json
- Render simple UI
- Save/load/delete local browser profiles
- Upload image to /upload/image
- Patch workflow using patch_targets
- Submit /prompt with client_id
- Listen to /ws progress
- Poll /history
- Display /view images
```

### 4. Flutter MVP scaffold

```text
mobile-app/flutter_mvp/
```

Current Flutter MVP behavior:

```text
- Android-first target
- SetupScreen accepts ComfyUI URL
- /system_stats connection check
- RemoteProfilesScreen loads typed List<RemoteProfile>
- Saves downloaded profile zip as LocalProfile
- LocalProfilesScreen opens saved profiles
- GenerateScreen renders app_profile.ui.simple fields
- Image fields use file_picker + dart:io File
- Uploads selected image files to /upload/image
- Patches workflow using patch_targets only
- Submits /prompt with same clientId used by /ws
- Polls /history/{prompt_id}
- Extracts and displays /view images
```

## Remaining caveats

```text
1. mobile-app/flutter_mvp is still a scaffold, not a full generated Flutter project shell.
2. If platform folders are missing, create a real Flutter shell and copy lib/ + pubspec.yaml.
3. Android INTERNET permission must be present in the generated Android manifest.
4. Flutter Web is not required for MVP because GenerateScreen uses dart:io File.
5. shared_preferences is acceptable for MVP, but large workflows may need file storage later.
6. Analyzer does not yet inspect /object_info for field metadata.
7. Analyzer does not yet confirm actual model file existence through /models.
8. UI workflow to API workflow conversion is not done yet.
9. Real RunPod GPU validation still needs to happen.
10. Real Android app runtime validation still needs to happen.
```

## Next reviewer should start here

```text
docs/mobile-system/HANDOFF.md
docs/mobile-system/RUNTIME_VALIDATION_RESULT.md
docs/mobile-system/BLOCKERS_AFTER_CLAUDE.md
docs/mobile-system/NEXT_PHASE_PLAN.md
```

## Do not do yet

```text
- Do not merge to main yet.
- Do not add automatic custom node installation.
- Do not add automatic model downloads.
- Do not turn the app into a full ComfyUI workflow editor.
- Do not add Playwright/Chromium as a required MVP dependency.
- Do not add Google Drive/cloud sync.
- Do not add payment/monetization.
```
