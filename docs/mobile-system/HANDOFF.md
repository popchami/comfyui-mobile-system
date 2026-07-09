# HANDOFF: ComfyUI Mobile System

## Purpose

This file is the single source of truth for "what is done / in progress / blocked" on this PR. It is fully rewritten (not diff-appended) at the end of each work session.

Last updated by: Claude, during architecture review + runtime validation pass on branch `docs/mobile-system-spec` (PR #1).

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

Read all 9 handoff docs in order, then cross-checked the documented decisions against the actual code in `analyzer/ComfyUI-Mobile-Analyzer/` and `mobile-app/flutter_mvp/`. Findings:

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
7. Minimum blocker-free validation path executed successfully (see below).
```

Conclusion: direction and decisions in `PRE_IMPLEMENTATION_ALIGNMENT_DECISIONS.md` are still valid. No large rewrite needed.

### Runtime validation (executed on-device, not just documented)

This session actually installed ComfyUI + the custom node + Flutter tooling in a throwaway sandbox directory (outside the repo, CPU-only, aarch64, no GPU) and ran the real flow end-to-end. Results against the 10-item pass condition in `CLAUDE_FINAL_REVIEW_AND_INSTALL.md`:

```text
1. ComfyUI starts with ComfyUI-Mobile-Analyzer installed        -> PASS
2. Mobile Profile Exporter appears (verified via /object_info)  -> PASS
3. Mobile Profile Exporter creates a zip under output/mobile_profiles -> PASS (after fix, see below)
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

For items 9-10, a full Android build/run was not possible in this sandbox (no Android emulator, no GPU/models). As a substitute, the actual Dart service classes (`ComfyApiClient`, `ProfileZipService`, `WorkflowPatcher`, `HistoryImageExtractor` — unmodified, straight from `mobile-app/flutter_mvp/lib/`) were exercised directly via `dart run` against the live ComfyUI instance:

```text
system_stats                    -> ok
getRemoteProfiles()             -> ok, found the exported profile
downloadProfileZip()            -> ok, 2280 bytes
ProfileZipService.parseProfileZip() -> ok, 11 fields / 11 patch_targets parsed
WorkflowPatcher.patchWorkflow() -> ok, prompt/seed/etc. patched correctly
queuePrompt() -> submitted correctly; ComfyUI correctly rejected it with
  HTTP 400 "ckpt_name: 'example.safetensors' not in []" because no real
  checkpoint model exists in this sandbox (expected — no models were
  downloaded here, per the no-auto-download rule)
```

This confirms the client-side data flow (download -> parse -> patch -> submit) is correct end-to-end at the code level. What is NOT confirmed: actual Flutter widget rendering, `file_picker` native Android plugin behavior, and real image generation/display (needs a real GPU + real checkpoint, which this sandbox intentionally does not have).

### Bug fixed (blocker)

```text
File: analyzer/ComfyUI-Mobile-Analyzer/nodes.py
Fix: added `OUTPUT_NODE = True` to MobileProfileExporter.
Reason: without it, ComfyUI rejects any /prompt containing only this node with
  400 "prompt_no_outputs", because the node has no dependents and wasn't marked
  as an output node itself. Reproduced live, fixed, re-verified live (queue ->
  execute -> zip written -> downloadable).
Commit: 6ab9ef7 (not pushed — push requires separate user approval per policy).
```

This was the only code change made. No other files were touched.

## In progress / not yet done

```text
- Nothing is actively in progress. The review + validation pass described above
  is complete for what this sandbox can test.
```

## Blocked / deferred (needs environment Claude does not have here)

```text
1. Real Android build/run (flutter run on emulator or device) — no Android
   SDK/emulator in this sandbox. The generated test project's AndroidManifest.xml
   was missing <uses-permission android:name="android.permission.INTERNET" />
   by default (as RUN_CHECKLIST.md already warned); this was added only in the
   throwaway scratch project for testing, not in the repo (mobile-app/flutter_mvp
   has no android/ folder committed — that's expected/by design, see
   PRE_CLAUDE_STATUS.md caveat #2). Whoever runs `flutter create` for real
   should remember to add this permission.
2. Real image generation end-to-end — requires a GPU-backed ComfyUI with an
   actual checkpoint model. Per project rules, no model was auto-downloaded
   here. This must be validated on the user's actual RunPod Pod, not in a
   throwaway sandbox.
3. /object_info-based field detection, /models-based existence checks, file-based
   local storage, UI workflow conversion — all correctly deferred per
   PRIORITY_CONFLICT_REVIEW.md, not started.
```

## PR status

```text
Still Draft. Do not merge.
The OUTPUT_NODE fix is committed locally on docs/mobile-system-spec but not pushed.
Architecture direction confirmed valid; no large rewrite triggered.
```

## Recommended next steps (in priority order)

```text
1. User approves push of commit 6ab9ef7 (the OUTPUT_NODE fix).
2. Validate items 9-10 for real on an actual RunPod Pod with GPU + a real
   checkpoint (do not attempt on this local sandbox).
3. Add INTERNET permission to the real generated Android manifest when the
   actual Flutter project shell is created for real device testing.
4. Only after 2-3 pass, revisit docs/mobile-system/OPEN_TODOS.md and
   FUTURE_ISSUES_AND_IMPROVEMENTS.md and reprioritize.
```
