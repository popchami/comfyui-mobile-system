# Pre-Claude Status Summary

## Purpose

This file summarizes the current PR state before handing it to Claude.

The handoff goal changed after reviewing existing ComfyUI/RunPod capabilities and the external `comfy-portal-endpoint` reference.

The user cannot use a PC right now, so the current goal is:

```text
Make the PR clear enough that Claude can first review edited pre-implementation decisions,
then perform architecture alignment,
then install it, run checks, fix blockers, and confirm install readiness.
```

## Important handoff change

This is no longer only a runtime validation handoff.

Claude should first review:

```text
- edited pre-implementation alignment decisions
- current system design
- external reference review
- official ComfyUI API overlap
- official RunPod capability overlap
- whether /object_info and /models should move earlier
```

Then Claude should run runtime validation.

## Current edited decision

The inventory has been edited into a decision file:

```text
docs/mobile-system/PRE_IMPLEMENTATION_ALIGNMENT_DECISIONS.md
```

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

Current state observed before this update:

```text
state: open
merged: false
draft: true
changed files: 50+
commits: 130+
reviews: none yet
```

Important:

```text
Do not merge yet.
Claude should run architecture alignment and install/runtime checks first.
The PR is intentionally kept as Draft until runtime validation passes.
```

## Completion marker

Pre-Claude preparation was previously marked complete here:

```text
docs/mobile-system/PRE_CLAUDE_DONE.md
```

After later platform/reference review, the handoff has been expanded, but the PR remains in a pre-Claude handoff state.

## Claude handoff prompt

Copy-paste prompt for Claude:

```text
docs/mobile-system/CLAUDE_COPYPASTE_PROMPT.md
```

## Claude should start here

Read in this order:

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
- Provides planned profile list/download routes
```

Static fixes already made:

```text
- is_connection supports string and numeric node ids
- profile_version bumped to 0.2.1
- server profile list returns id/name/file/status/size_bytes/modified_at/download_url
- download lookup tolerates ids with or without .zip
- output_app_profile_example.json updated to match current output shape
```

### 3. HTML prototype

```text
mobile-app/prototype/
```

Important files:

```text
index.html
profile-storage.js
stored-profile-ui.js
comfy-progress.js
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

Important files:

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

## Known caveats before Claude runtime check

```text
1. mobile-app/flutter_mvp may be a scaffold, not a full generated Flutter project shell.
2. If platform folders are missing, Claude should run flutter create and copy lib/ + pubspec.yaml.
3. Android INTERNET permission must be present in the generated Android manifest.
4. Flutter Web is not required for MVP because GenerateScreen uses dart:io File.
5. shared_preferences is acceptable for MVP, but large workflows may need file storage later.
6. Analyzer does not yet inspect object_info.
7. Analyzer does not yet confirm actual model file existence.
8. UI workflow to API workflow conversion is not done yet.
9. ComfyUI route registration in server.py still needs real runtime validation.
10. Existing ComfyUI official APIs may replace some planned custom logic.
```

## Architecture alignment questions before runtime validation

Claude should answer:

```text
1. Which current custom logic duplicates official ComfyUI APIs?
2. Should /object_info be the first post-validation Analyzer improvement?
3. Should /models be the first post-validation model-check improvement?
4. Which /mobile_analyzer custom routes are still necessary?
5. Should UI workflow conversion remain optional for now?
6. What is the minimum blocker-free path to validate the current MVP?
```

## Runtime pass condition

Claude should consider this install-ready only when:

```text
1. ComfyUI starts with ComfyUI-Mobile-Analyzer installed.
2. Mobile Profile Exporter appears in ComfyUI.
3. Mobile Profile Exporter creates a zip under output/mobile_profiles.
4. Zip contains workflow.json and app_profile.json.
5. /mobile_analyzer/profiles returns profile metadata.
6. /mobile_analyzer/profiles/{id}/download downloads the zip.
7. Flutter MVP passes flutter pub get.
8. Flutter MVP passes flutter analyze or only has documented non-blocking warnings.
9. Flutter Android app can connect to ComfyUI.
10. Flutter Android app can download, save, open, patch, submit, and display at least one generated image.
```

## Do not do yet

```text
- Do not merge to main yet.
- Do not add automatic custom node installation.
- Do not add automatic model downloads.
- Do not turn the app into a full ComfyUI workflow editor.
- Do not add Playwright/Chromium as a required MVP dependency.
- Do not prioritize future TODOs until architecture alignment and runtime path are confirmed.
```

## After Claude confirms install readiness

Then revisit:

```text
docs/mobile-system/OPEN_TODOS.md
docs/mobile-system/FUTURE_ISSUES_AND_IMPROVEMENTS.md
```

and reorder future work by priority.
