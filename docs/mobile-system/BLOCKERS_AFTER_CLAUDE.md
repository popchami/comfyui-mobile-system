# Blockers After Claude Validation

## Purpose

This file records what still blocks merging PR #1 after the architecture review and limited runtime validation pass.

## Current blocker summary

```text
The mobile system is not blocked by known architecture issues anymore.
It is blocked by missing real validation environments.
```

## Blocker 1: RunPod GPU validation not complete

### Status

```text
Blocked until RunPod is available.
```

### Why this matters

The CPU-only sandbox confirmed that the Analyzer can load, export a profile zip, and expose profile download routes. It could not confirm real image generation because no GPU or real checkpoint model was available.

### Required validation

```text
1. Start a RunPod Pod with ComfyUI.
2. Install/place ComfyUI-Mobile-Analyzer under ComfyUI/custom_nodes/.
3. Start ComfyUI.
4. Confirm Mobile Profile Exporter appears.
5. Export a profile zip.
6. Confirm /mobile_analyzer/profiles works.
7. Confirm /mobile_analyzer/profiles/{id}/download works.
8. Run a real workflow with an actual checkpoint.
9. Confirm /prompt -> /ws -> /history -> /view completes with a generated image.
```

### Rules

```text
- Do not auto-download models.
- Do not auto-install custom nodes.
- Use already-approved test models/workflows only.
```

## Blocker 2: Android device or emulator validation not complete

### Status

```text
Blocked until Android runtime validation is available.
```

### Why this matters

Flutter `pub get` and `analyze` passed for the PR source, but the actual app has not been run on a real Android device or emulator.

### Required validation

```text
1. Create a real Flutter Android project shell.
2. Copy mobile-app/flutter_mvp/lib/ and pubspec.yaml into it.
3. Add Android INTERNET permission.
4. Run flutter pub get.
5. Run flutter analyze.
6. Run on Android device or emulator.
7. Connect to ComfyUI URL.
8. Download a profile zip.
9. Save/open the profile locally.
10. Patch only patch_targets.
11. Submit generation.
12. Display at least one generated image.
```

### Required Android permission

```xml
<uses-permission android:name="android.permission.INTERNET" />
```

## Blocker 3: WEB_DIRECTORY cleanup needs natural runtime confirmation

### Status

```text
Cleanup committed, but not yet revalidated in live RunPod ComfyUI.
```

### Why this matters

The unused declaration was removed because no `web/` directory or ComfyUI frontend assets are shipped. This is the safer state for the current custom node, but the next ComfyUI startup should still confirm no import regression.

### Required validation

```text
Start ComfyUI with the latest PR branch Analyzer and confirm no import error.
```

## Not blockers right now

The following are important, but must not block the next validation step:

```text
- /object_info-based field metadata support
- /models-based model existence checks
- UI workflow to API workflow conversion
- file-based production profile storage
- bypass handling
- subgraph handling
- node color matching
- ControlNet / IPAdapter / FaceDetailer / Upscale support
```

## Merge rule

```text
Do not merge PR #1 until Blocker 1 and Blocker 2 are complete.
Blocker 3 should be checked as part of Blocker 1.
```
