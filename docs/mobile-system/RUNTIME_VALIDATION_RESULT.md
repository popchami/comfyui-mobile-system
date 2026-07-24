# Runtime Validation Result

## Purpose

This file records what has already been validated and what remains unverified after the first Claude runtime validation pass.

This file is a status record only. It does not authorize merging the PR.

## Environment used

```text
Environment: throwaway sandbox outside the repository
Device class: aarch64 / CPU-only
GPU: none
Real checkpoint model: none
Android emulator/device: none
RunPod: not used in this pass
```

The validation was useful for finding import/runtime blockers, but it is not a substitute for RunPod GPU validation or real Android validation.

## Architecture review status

```text
Architecture alignment review: PASS
Large rewrite needed: no
Direction change needed: no
```

Confirmed direction:

```text
ComfyUI-side Analyzer
  ↓
mobile_profile_export.zip
  ↓
Smartphone app imports profile
  ↓
Dynamic simple UI
  ↓
Patch workflow using patch_targets only
  ↓
Submit to ComfyUI official APIs
  ↓
Display generated result
```

## Runtime checks already passed

```text
1. ComfyUI starts with ComfyUI-Mobile-Analyzer installed        -> PASS
2. Mobile Profile Exporter appears via /object_info             -> PASS
3. Mobile Profile Exporter creates a zip                        -> PASS after OUTPUT_NODE fix
4. Zip contains workflow.json and app_profile.json              -> PASS
5. /mobile_analyzer/profiles returns metadata                   -> PASS
6. /mobile_analyzer/profiles/{id}/download downloads zip         -> PASS
7. Flutter MVP passes flutter pub get                           -> PASS
8. Flutter MVP passes flutter analyze                           -> PASS for PR lib/ source
```

## Partial checks

```text
9. Flutter Android app can connect to ComfyUI                    -> PARTIAL
10. Flutter app can download/save/open/patch/submit/display      -> PARTIAL
```

Reason:

```text
The Dart service flow was exercised directly, but the full Flutter Android UI was not run on a real device or emulator.
```

The following code-level flow was confirmed:

```text
system_stats                         -> ok
getRemoteProfiles()                  -> ok
downloadProfileZip()                 -> ok
ProfileZipService.parseProfileZip()  -> ok
WorkflowPatcher.patchWorkflow()      -> ok
queuePrompt()                        -> submitted correctly
```

The final /prompt result was expected to fail in the CPU-only sandbox because no checkpoint model existed:

```text
HTTP 400: ckpt_name: 'example.safetensors' not in []
```

This is not a project failure. It confirms that model existence must be validated on a real GPU-backed ComfyUI environment with actual models installed.

## Bug found and fixed

```text
File: analyzer/ComfyUI-Mobile-Analyzer/nodes.py
Fix: added OUTPUT_NODE = True to MobileProfileExporter.
Reason: ComfyUI rejected exporter-only prompts as prompt_no_outputs without this.
Status: fixed and present on branch docs/mobile-system-spec.
```

## Follow-up cleanup performed

```text
File: analyzer/ComfyUI-Mobile-Analyzer/__init__.py
Fix: removed unused WEB_DIRECTORY = "web" declaration.
Reason: no web assets are shipped and analyzer/ComfyUI-Mobile-Analyzer/web/ does not exist.
Status: committed on branch docs/mobile-system-spec.
```

This cleanup still needs to be naturally confirmed during the next ComfyUI startup on RunPod.

## Not validated yet

```text
- RunPod ComfyUI startup with this Analyzer.
- Real GPU image generation with an actual checkpoint.
- Real Android project shell creation.
- Android INTERNET permission in the generated manifest.
- Flutter app running on Android device or emulator.
- Native file_picker behavior on Android.
- End-to-end mobile flow from profile download to generated image display.
```

## Merge status

```text
Do not merge yet.
PR should remain Draft until RunPod GPU validation and Android device validation are complete.
```
