# HANDOFF: ComfyUI Mobile System

## Purpose

This file is the single source of truth for "what is done / in progress / blocked" on this PR. It is fully rewritten (not diff-appended) at the end of each work session.

Last updated by: ChatGPT, after GitHub PR branch sanity check on branch `docs/mobile-system-spec` (PR #1). Termux, RunPod, ComfyUI runtime, and Flutter runtime were not used in this update.

## Current decision (unchanged)

```text
ComfyUI-side Analyzer
  ↓
mobile_profile_export.zip
  ↓
Smartphone app imports profile
  ↓
Dynamic simple UI
  ↓
Patch workflow
  ↓
Submit to ComfyUI
```

Do not discard this system. Use official ComfyUI APIs wherever possible; keep custom code focused on the missing mobile profile layer. Full decision record: `PRE_IMPLEMENTATION_ALIGNMENT_DECISIONS.md`.

## Completed

### Architecture alignment review (docs + code)

Claude previously read all 9 handoff docs in order, then cross-checked the documented decisions against the actual code in `analyzer/ComfyUI-Mobile-Analyzer/` and `mobile-app/flutter_mvp/`. Findings:

```text
1. No official-API route duplication. Flutter client calls /prompt, /ws, /history,
   /view, /upload/image, /system_stats directly — no custom reimplementation.
   The only functional "duplication" is nodes.py's classify_node()/build_app_profile(),
   which hardcodes ~7 class_types instead of querying /object_info.
2. /object_info should be the first post-validation Analyzer improvement. Confirmed:
   not a blocker for current MVP (minimal_api_workflow.json works without it).
3. /models should be the first post-validation model-check improvement. Confirmed:
   detect_model_refs() only extracts names today, marked "unverified" honestly.
4. Only 2 custom routes exist: /mobile_analyzer/profiles and
   /mobile_analyzer/profiles/{id}/download. Both are load-bearing for Flutter
   (RemoteProfilesScreen). Neither duplicates an official route. Nothing to trim.
5. UI workflow -> API workflow conversion: confirmed still unimplemented and
   optional. requirements.txt has zero heavy deps (no Playwright/Chromium).
6. comfy-portal-endpoint: confirmed zero code/dependency footprint in this repo.
   Reference-only status holds.
7. Minimum blocker-free validation path executed successfully where the sandbox allowed it.
```

Conclusion: direction and decisions in `PRE_IMPLEMENTATION_ALIGNMENT_DECISIONS.md` are still valid. No large rewrite needed.

### Runtime validation already performed by Claude

Claude previously installed ComfyUI + the custom node + Flutter tooling in a throwaway sandbox directory (outside the repo, CPU-only, aarch64, no GPU) and ran the real flow end-to-end as far as that environment allowed. Results against the 10-item pass condition in `CLAUDE_FINAL_REVIEW_AND_INSTALL.md`:

```text
1. ComfyUI starts with ComfyUI-Mobile-Analyzer installed        -> PASS
2. Mobile Profile Exporter appears (verified via /object_info)  -> PASS
3. Mobile Profile Exporter creates a zip under output/mobile_profiles -> PASS (after OUTPUT_NODE fix)
4. Zip contains workflow.json and app_profile.json               -> PASS
5. /mobile_analyzer/profiles returns profile metadata             -> PASS
6. /mobile_analyzer/profiles/{id}/download downloads the zip      -> PASS
7. Flutter MVP passes flutter pub get                              -> PASS
8. Flutter MVP passes flutter analyze                              -> PASS (0 errors in lib/;
   2 info-level const-constructor suggestions; 1 unrelated error in the
   flutter-create-generated default test/widget_test.dart, which is not
   part of this PR's source and references the scaffold's placeholder MyApp)
9. Flutter Android app can connect to ComfyUI                      -> PARTIAL (see Blocked)
10. Flutter Android app can download/save/open/patch/submit/display -> PARTIAL (see Blocked)
```

For items 9-10, a full Android build/run was not possible in the sandbox (no Android emulator, no GPU/models). As a substitute, the actual Dart service classes (`ComfyApiClient`, `ProfileZipService`, `WorkflowPatcher`, `HistoryImageExtractor` — unmodified, straight from `mobile-app/flutter_mvp/lib/`) were exercised directly via `dart run` against the live ComfyUI instance:

```text
system_stats                    -> ok
getRemoteProfiles()             -> ok, found the exported profile
downloadProfileZip()            -> ok, 2280 bytes
ProfileZipService.parseProfileZip() -> ok, 11 fields / 11 patch_targets parsed
WorkflowPatcher.patchWorkflow() -> ok, prompt/seed/etc. patched correctly
queuePrompt() -> submitted correctly; ComfyUI correctly rejected it with
  HTTP 400 "ckpt_name: 'example.safetensors' not in []" because no real
  checkpoint model exists in the sandbox (expected — no models were
  downloaded, per the no-auto-download rule)
```

This confirms the client-side data flow (download -> parse -> patch -> submit) is correct end-to-end at the code level. What is NOT confirmed: actual Flutter widget rendering, `file_picker` native Android plugin behavior, and real image generation/display (needs a real GPU + real checkpoint).

### Bug fixed and now present on PR branch

```text
File: analyzer/ComfyUI-Mobile-Analyzer/nodes.py
Fix: added `OUTPUT_NODE = True` to MobileProfileExporter.
Reason: without it, ComfyUI rejects any /prompt containing only this node with
  400 "prompt_no_outputs", because the node has no dependents and wasn't marked
  as an output node itself. Reproduced live, fixed, re-verified live (queue ->
  execute -> zip written -> downloadable).
Original fix commit reported by Claude: 6ab9ef7.
GitHub PR branch sanity check: confirmed `OUTPUT_NODE = True` is now present on
  branch `docs/mobile-system-spec`.
```

### WEB_DIRECTORY cleanup

```text
File: analyzer/ComfyUI-Mobile-Analyzer/__init__.py
Fix: removed unused `WEB_DIRECTORY = "web"` declaration.
Reason: the custom node does not currently ship ComfyUI frontend web assets, and
  `analyzer/ComfyUI-Mobile-Analyzer/web/` does not exist in the PR branch.
  Removing the declaration avoids pointing ComfyUI at a non-existent web folder.
Commit: 9c1f9e0.
Runtime note: this cleanup was not revalidated in a live ComfyUI environment in
  this ChatGPT-only update. It should be naturally covered by the next RunPod
  ComfyUI startup check.
```

## In progress / not yet done

```text
- Nothing is actively in progress.
- Current state is ready for the next RunPod/GPU and Android-device validation pass when those environments are available.
```

## Blocked / deferred

```text
1. Real Android build/run (flutter run on emulator or device) — not confirmed yet.
   The generated test project's AndroidManifest.xml was missing
   <uses-permission android:name="android.permission.INTERNET" /> by default.
   This was added only in Claude's throwaway scratch project for testing, not in
   the repo, because mobile-app/flutter_mvp has no android/ folder committed by design.
   Whoever runs `flutter create` for real should add this permission.
2. Real image generation end-to-end — requires a GPU-backed ComfyUI with an
   actual checkpoint model. Per project rules, no model should be auto-downloaded.
   This must be validated on the user's actual RunPod Pod.
3. /object_info-based field detection, /models-based existence checks, file-based
   local storage, UI workflow conversion — all correctly deferred per
   PRIORITY_CONFLICT_REVIEW.md, not started.
```

## PR status

```text
Still Draft. Do not merge.
PR branch: docs/mobile-system-spec.
Latest known PR branch includes the OUTPUT_NODE fix and the WEB_DIRECTORY cleanup.
Architecture direction confirmed valid; no large rewrite triggered.
```

## Recommended next steps (in priority order)

```text
1. When RunPod is available, start ComfyUI with this PR branch's Analyzer and confirm
   the custom node still imports cleanly after the WEB_DIRECTORY cleanup.
2. Validate real image generation on a RunPod Pod with GPU + a real checkpoint.
3. Create the real Flutter Android project shell, add INTERNET permission, then run
   on an Android device or emulator.
4. After 1-3 pass, revisit docs/mobile-system/OPEN_TODOS.md and
   FUTURE_ISSUES_AND_IMPROVEMENTS.md and reprioritize.
```
