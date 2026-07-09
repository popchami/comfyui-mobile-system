# HANDOFF: ComfyUI Mobile System

## Purpose

This file is the single source of truth for "what is done / in progress / blocked" on this PR.

Last updated by: ChatGPT, after correcting the project concept to user-provided workflow import on branch `docs/mobile-system-spec` (PR #1). Termux, RunPod, ComfyUI runtime, Flutter runtime, and Android runtime were not used in this update.

## Current decision

```text
User prepares any ComfyUI workflow
  ↓
ComfyUI-Mobile-Analyzer reads/analyzes the user workflow
  ↓
Analyzer exports workflow.json + app_profile.json as mobile_profile_export.zip
  ↓
Smartphone app imports profile zip
  ↓
Smartphone app renders dynamic simple UI from app_profile.json
  ↓
Smartphone app patches only app_profile.json.patch_targets
  ↓
Smartphone app submits the workflow to ComfyUI official APIs
  ↓
Smartphone app displays generated result
```

Do not discard this system. Use official ComfyUI APIs wherever possible; keep custom code focused on the missing mobile profile layer.

Important clarification:

```text
The product must not be narrowed into a fixed set of app-owned dedicated workflows.
The user should only need to prepare a ComfyUI workflow.
The dedicated custom node/analyzer converts that user-provided workflow into an app-readable profile.
```

Concept detail:

```text
docs/mobile-system/USER_PROVIDED_WORKFLOW_CONCEPT.md
```

## Final smartphone-only status

```text
Repository: popchami/comfyui-mobile-system
PR: #1
Branch: docs/mobile-system-spec
State: Draft
Merge: DO NOT MERGE
Smartphone-only preparation: COMPLETE
Smartphone-only implementation: COMPLETE
Smartphone-only documentation: COMPLETE
Smartphone-only handoff preparation: COMPLETE
RunPod GPU validation: NOT COMPLETE
Android real-device/emulator validation: NOT COMPLETE
Next meaningful work: REAL VALIDATION ONLY
```

## Smartphone-side app behavior now prepared

```text
- ComfyUI URL save/restore.
- /system_stats connection check.
- /object_info capability check.
- /models/{folder} read-only helpers.
- /queue helper and Check queue button.
- /interrupt helper and Interrupt button.
- Friendly mobile-facing error messages.
- app_profile warning parsing.
- missing model warning display.
- missing custom node warning display.
- Analyzer warning display.
- Read-only Check environment button.
- ModelFolderResolver for checkpoints, loras, vae, clip, controlnet, upscale_models, diffusion_models, and embeddings.
- EnvironmentModelChecker integrated into GenerateScreen.
- profile-specific previous input restore.
- profile-specific input save before /prompt.
- Reset to profile defaults.
- Random seed button.
- Use last seed button.
- selected image preview.
- /prompt submission with client_id.
- /ws progress listener.
- /history polling fallback.
- /view generated image display.
- Session history strip.
- Generated image large preview.
- Generated image metadata: prompt_id, profile name, seed, created_at.
- Session history thumbnail metadata display.
- Collapsible generated UI sections.
```

## Current generated UI decision

```text
Do not collapse every usable field.
Keep core creative inputs visible by default.
Collapse detailed settings by default.
```

Default generation screen layout:

```text
1. Core Inputs                       open
   - prompt
   - negative prompt
   - required image input

2. Basic Generation Settings         collapsed
   - seed
   - steps
   - cfg
   - sampler
   - scheduler
   - denoise

3. Size / Output                     collapsed
   - width
   - height
   - batch

4. Advanced Workflow Features        collapsed
   - LoRA
   - ControlNet
   - IPAdapter
   - FaceDetailer
   - Upscale
   - RemBG
   - Inpaint
   - Mask

5. Expert / Debug                    collapsed
   - unknown editable inputs
   - custom node warnings
   - raw workflow/debug info
```

## Current app-side reused behaviors from legacy HTML

```text
- Saved ComfyUI URL restore.
- /prompt + /ws + /history + /view flow.
- /history fallback when /ws is unavailable or unstable.
- Selected image preview.
- Session generated image history.
- Larger generated image preview.
- Current-session seed reuse.
```

Existing HTML profiles under `profiles/` were reviewed as proven behavior references. Details are recorded in:

```text
docs/mobile-system/LEGACY_HTML_REUSE_NOTES.md
```

## Legacy HTML visual UI decision

```text
Legacy HTML visual layout was not copied into the Flutter MVP.
Legacy HTML UI/UX behavior was used as a reference.
A dedicated visual UI review is deferred until after RunPod + Android validation.
```

Post-validation review note:

```text
docs/mobile-system/POST_VALIDATION_LEGACY_HTML_UI_REVIEW.md
```

Reason:

```text
The old HTML files are fixed per-profile pages.
The new Flutter app generates UI dynamically from app_profile.json + patch_targets.
Copying the old visual layout before validation could reintroduce workflow-specific assumptions.
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

```text
- MobileProfileExporter has OUTPUT_NODE = True.
- Analyzer __init__.py no longer declares unused WEB_DIRECTORY.
- HTTP API URL builder preserves path-based proxy base paths.
- WebSocket URL builder preserves path-based proxy base paths.
- Prototype WebSocket URL builder preserves path-based proxy base paths.
- PR_BODY_UPDATE_DRAFT.md uses safe nested Markdown fences.
```

## Current source-of-truth docs

Read these first for status:

```text
docs/mobile-system/HANDOFF.md
docs/mobile-system/SMARTPHONE_ONLY_COMPLETION_REPORT.md
docs/mobile-system/USER_PROVIDED_WORKFLOW_CONCEPT.md
docs/mobile-system/RUNTIME_VALIDATION_RESULT.md
docs/mobile-system/BLOCKERS_AFTER_CLAUDE.md
docs/mobile-system/NEXT_PHASE_PLAN.md
docs/mobile-system/NEXT_ACTION_QUEUE.md
docs/mobile-system/DOCS_AUDIT_RESULT.md
docs/mobile-system/STATIC_REVIEW_NOTES.md
docs/mobile-system/LEGACY_HTML_REUSE_NOTES.md
docs/mobile-system/UI_VISIBILITY_RULES.md
docs/mobile-system/MOBILE_APP_SPEC.md
docs/mobile-system/APP_INPUT_STATE_CONTROLS.md
docs/mobile-system/APP_QUEUE_AND_ERROR_CONTROLS.md
docs/mobile-system/APP_CAPABILITY_CHECKS.md
docs/mobile-system/APP_PROFILE_WARNING_DISPLAY.md
docs/mobile-system/APP_MODEL_FOLDER_RESOLVER.md
docs/mobile-system/APP_ENVIRONMENT_MODEL_CHECKER.md
docs/mobile-system/APP_GENERATED_IMAGE_METADATA.md
docs/mobile-system/POST_VALIDATION_LEGACY_HTML_UI_REVIEW.md
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

4. /queue, /interrupt, /object_info, /models/{folder}, Check environment,
   generated image metadata, session history display, seed reuse, Random seed,
   Reset to defaults, and generated UI grouping all need Android/RunPod validation.

5. Legacy HTML visual UI review is deferred until after RunPod + Android validation.

6. User-provided workflow import must be validated with at least one real user workflow.
```

## Do next when RunPod is available

```text
1. Read docs/mobile-system/RUNPOD_VALIDATION_RUNBOOK.md.
2. Start RunPod ComfyUI.
3. Place Analyzer into custom_nodes.
4. Confirm ComfyUI starts and Analyzer loads.
5. Use or prepare a real user-provided ComfyUI workflow.
6. Export profile zip from that workflow.
7. Check Analyzer profile list/download routes.
8. Run real generation with an existing model.
9. Validate /prompt -> /ws -> /history -> /view.
10. Validate /queue and /interrupt.
11. Validate /object_info and /models/{folder} behavior.
12. Record result using docs/mobile-system/VALIDATION_RESULT_TEMPLATES.md.
13. Compare with existing HTML behavior where useful.
14. Update this HANDOFF.md.
```

## Do next when Android validation is available

```text
1. Read docs/mobile-system/ANDROID_VALIDATION_RUNBOOK.md.
2. Create real Flutter Android shell if needed.
3. Copy flutter_mvp lib and pubspec.
4. Add Android INTERNET permission.
5. Run pub get / analyze / run.
6. Connect to ComfyUI.
7. Download/save/open a profile generated from a user-provided workflow.
8. Confirm generated UI layout: core inputs open, detailed settings collapsed.
9. Confirm profile-specific previous input restore.
10. Confirm Reset to profile defaults.
11. Confirm Random seed.
12. Confirm Use last seed.
13. Confirm Profile warnings card.
14. Confirm Check environment.
15. Confirm Check queue.
16. Confirm Interrupt.
17. Submit generation.
18. Display generated image.
19. Confirm session history metadata and large preview metadata.
20. Record result using docs/mobile-system/VALIDATION_RESULT_TEMPLATES.md.
21. Compare /prompt -> /ws -> /history -> /view behavior against existing HTML.
22. Update this HANDOFF.md.
```

## Do next if something fails

```text
1. Fill docs/mobile-system/DEBUG_REPORT_TEMPLATE.md.
2. Identify failing area: RunPod / Android / Analyzer / workflow / model / custom node / ComfyUI API.
3. Check whether existing HTML already has proven behavior for the failing area.
4. Fix only the smallest blocker.
5. Re-test the failed path.
6. Update this HANDOFF.md.
7. Keep PR Draft.
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
- Do not copy legacy HTML prompt/content lists into the new dynamic app.
- Do not collapse every usable generated UI field.
- Do not add more smartphone-only features before real validation.
- Do not copy legacy HTML visual layout before Android validation.
- Do not narrow the product into a fixed set of app-owned workflows.
```

## Merge readiness rule

Do not move toward merge until:

```text
- RunPod ComfyUI validation passes.
- Real checkpoint image generation passes.
- Android device/emulator validation passes.
- A real user-provided workflow import/export path is validated.
- Generated UI layout is validated on Android.
- Seed reuse interaction is validated on Android.
- Check environment is validated against real ComfyUI.
- Generated image metadata display is validated on Android.
- HANDOFF.md is updated with final validation results.
- PR body is updated with final validation results.
- User explicitly approves moving forward.
```

## Final smartphone-only stop condition

```text
Smartphone-only work is complete.
Do not continue adding smartphone-only features.
The next meaningful work is RunPod/Android real validation unless a new source-level blocker is discovered.
Legacy HTML visual UI review is a post-validation issue, not a pre-validation change.
User-provided workflow import is the correct product concept.
```
