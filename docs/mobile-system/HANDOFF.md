# HANDOFF: ComfyUI Mobile System

## Purpose

This file is the single source of truth for "what is done / in progress / blocked" on this PR. It is fully rewritten at the end of each work session.

Last updated by: ChatGPT, after smartphone-only GitHub documentation, planning, runbook, handoff-prep, final audit, and completion-report cleanup on branch `docs/mobile-system-spec` (PR #1). Termux, RunPod, ComfyUI runtime, and Flutter runtime were not used in this update.

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
Patch workflow using app_profile.json.patch_targets only
  ↓
Submit to ComfyUI official APIs
  ↓
Display generated result
```

Do not discard this system. Use official ComfyUI APIs wherever possible; keep custom code focused on the missing mobile profile layer. Full decision record: `PRE_IMPLEMENTATION_ALIGNMENT_DECISIONS.md`.

## Current PR status

```text
Repository: popchami/comfyui-mobile-system
PR: #1
Branch: docs/mobile-system-spec
State: Draft
Merge: do not merge
Smartphone-only preparation: complete
RunPod GPU validation: not complete
Android real-device/emulator validation: not complete
Implementation: paused except for minimal blocker fixes
```

## Completed: architecture and limited runtime validation

Claude previously completed architecture alignment review and limited CPU-only runtime validation.

Confirmed:

```text
1. ComfyUI starts with ComfyUI-Mobile-Analyzer installed        -> PASS in CPU-only sandbox
2. Mobile Profile Exporter appears via /object_info             -> PASS
3. Mobile Profile Exporter creates a zip                        -> PASS after OUTPUT_NODE fix
4. Zip contains workflow.json and app_profile.json              -> PASS
5. /mobile_analyzer/profiles returns metadata                   -> PASS
6. /mobile_analyzer/profiles/{id}/download downloads zip         -> PASS
7. Flutter MVP passes flutter pub get                           -> PASS
8. Flutter MVP passes flutter analyze                           -> PASS for PR lib/ source
9. Flutter Android app can connect to ComfyUI                    -> PARTIAL / still needs device validation
10. Flutter app can download/save/open/patch/submit/display      -> PARTIAL / still needs device + GPU validation
```

Important caveat:

```text
The validation sandbox had no RunPod GPU, no real checkpoint model, and no Android emulator/device.
```

## Completed: important fixes already on PR branch

### OUTPUT_NODE fix

```text
File: analyzer/ComfyUI-Mobile-Analyzer/nodes.py
Fix: added OUTPUT_NODE = True to MobileProfileExporter.
Reason: without it, ComfyUI rejected exporter-only prompts as prompt_no_outputs.
Status: present on branch docs/mobile-system-spec.
```

### WEB_DIRECTORY cleanup

```text
File: analyzer/ComfyUI-Mobile-Analyzer/__init__.py
Fix: removed unused WEB_DIRECTORY = "web" declaration.
Reason: the custom node does not currently ship frontend web assets, and analyzer/ComfyUI-Mobile-Analyzer/web/ does not exist.
Status: committed on branch docs/mobile-system-spec.
Runtime note: still needs natural confirmation during the next real RunPod ComfyUI startup.
```

## Completed: smartphone-only preparation

Smartphone-only preparation is now complete and recorded in:

```text
docs/mobile-system/SMARTPHONE_ONLY_COMPLETION_REPORT.md
```

The following was completed without RunPod, Termux, Claude Code, ComfyUI runtime, or Flutter runtime:

```text
- Runtime result summary added.
- Blocker list after Claude validation added.
- Next phase plan added.
- Future feature preparation added.
- Additional feature candidates added.
- app_profile.json evolution plan added.
- UX flow preparation added.
- Post-validation issue drafts added.
- Reference study backlog added.
- Reference-to-feature map added.
- Reference study checklist added.
- Validation result templates added.
- Debug report template added.
- Workflow compatibility report template added.
- Decision record template added.
- RunPod validation runbook added.
- Android validation runbook added.
- AI minimal handoff prompts added.
- Next action queue added.
- PR body update draft added.
- Docs audit result added.
- Smartphone-only completion report added.
- README updated as the docs index.
```

## Current source-of-truth docs

Read these first for status:

```text
docs/mobile-system/HANDOFF.md
docs/mobile-system/SMARTPHONE_ONLY_COMPLETION_REPORT.md
docs/mobile-system/RUNTIME_VALIDATION_RESULT.md
docs/mobile-system/BLOCKERS_AFTER_CLAUDE.md
docs/mobile-system/NEXT_PHASE_PLAN.md
docs/mobile-system/NEXT_ACTION_QUEUE.md
docs/mobile-system/DOCS_AUDIT_RESULT.md
```

Use these for the next validation pass:

```text
docs/mobile-system/RUNPOD_VALIDATION_RUNBOOK.md
docs/mobile-system/ANDROID_VALIDATION_RUNBOOK.md
docs/mobile-system/VALIDATION_RESULT_TEMPLATES.md
docs/mobile-system/DEBUG_REPORT_TEMPLATE.md
```

Use this for short AI handoff prompts:

```text
docs/mobile-system/AI_MINIMAL_HANDOFF_PROMPTS.md
```

## Blocked / deferred

```text
1. Real Android build/run (flutter run on emulator or device) — not confirmed yet.
   The real generated Android project must include:
   <uses-permission android:name="android.permission.INTERNET" />

2. Real image generation end-to-end — requires a GPU-backed ComfyUI with an actual checkpoint model.
   Per project rules, no model should be auto-downloaded.
   This must be validated on the user's actual RunPod Pod.

3. WEB_DIRECTORY cleanup still needs real ComfyUI startup confirmation on RunPod.

4. /object_info-based field detection, /models-based existence checks, production storage,
   UI workflow conversion, advanced workflow support, generated history, and prompt presets
   are all deferred until RunPod + Android validation passes.
```

## Do next when RunPod is available

```text
1. Read docs/mobile-system/RUNPOD_VALIDATION_RUNBOOK.md.
2. Start RunPod ComfyUI.
3. Place Analyzer into custom_nodes.
4. Confirm ComfyUI starts and Analyzer loads.
5. Export profile zip.
6. Check Analyzer profile list/download routes.
7. Run real generation with an existing model.
8. Record result using docs/mobile-system/VALIDATION_RESULT_TEMPLATES.md.
9. Update this HANDOFF.md.
```

## Do next when Android validation is available

```text
1. Read docs/mobile-system/ANDROID_VALIDATION_RUNBOOK.md.
2. Create real Flutter Android shell if needed.
3. Copy flutter_mvp lib and pubspec.
4. Add Android INTERNET permission.
5. Run pub get / analyze / run.
6. Connect to ComfyUI.
7. Download/save/open profile.
8. Submit generation.
9. Display generated image.
10. Record result using docs/mobile-system/VALIDATION_RESULT_TEMPLATES.md.
11. Update this HANDOFF.md.
```

## Do next if something fails

```text
1. Fill docs/mobile-system/DEBUG_REPORT_TEMPLATE.md.
2. Identify failing area: RunPod / Android / Analyzer / workflow / model / custom node / ComfyUI API.
3. Fix only the smallest blocker.
4. Re-test the failed path.
5. Update this HANDOFF.md.
6. Keep PR Draft.
```

## Do not do yet

```text
- Do not merge PR #1.
- Do not switch MVP to Serverless.
- Do not auto-download models.
- Do not auto-install custom nodes.
- Do not add Google Drive sync.
- Do not add payment/monetization.
- Do not build a public marketplace.
- Do not turn Android app into a full ComfyUI workflow editor.
- Do not require Playwright/Chromium for MVP.
```

## Merge readiness rule

Do not move toward merge until:

```text
- RunPod ComfyUI validation passes.
- Real checkpoint image generation passes.
- Android device/emulator validation passes.
- HANDOFF.md is updated with final validation results.
- PR body is updated with final validation results.
- User explicitly approves moving forward.
```

## Smartphone-only stop condition

```text
Smartphone-only work is complete.
Do not continue adding documentation unless a new non-runtime planning topic appears.
The next meaningful work is RunPod/Android real validation.
```
