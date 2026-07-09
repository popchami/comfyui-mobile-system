# HANDOFF: ComfyUI Mobile System

## Purpose

This file is the single source of truth for "what is done / in progress / blocked" on this PR.

Last updated by: Claude, work session paused by user request on branch `docs/mobile-system-spec` (PR #1), 2026-07-09 13:22 JST (commit `f824389`). Then updated by: ChatGPT, after recording full HTML and official ComfyUI API conflict notes on the same branch, through 2026-07-09 21:30 JST (multiple commits, tip `cee7b9b` at merge time). Termux, RunPod, ComfyUI runtime, Flutter runtime, and Android runtime were not used in ChatGPT's update.

**要確認(rebase統合時のメモ)**: 本ファイルは2つの独立した更新系列を統合したものです。時系列としてはClaudeによる「Session paused — quick resume summary」(13:22)が先、ChatGPTによる大幅な拡張(同日21:30まで、複数コミット)が後です。両者はそれぞれ別のブランチ状態からの記述であり、このrebase統合コミットで初めて突き合わされました。内容に新旧の食い違いがある場合、基本的にはこの後に続く各セクション(ChatGPT側、時系列で後)がより新しい状態を反映しています。Claudeの記録は「その時点のスナップショット」として保持しています。

## Session paused — quick resume summary (Claude、2026-07-09 13:22 JST 時点)

```text
Where we stopped:
  Architecture review + runtime validation is fully DONE and PUSHED.
  Nothing is mid-flight. Working tree is clean (git status: nothing to commit).

What was planned next (not started):
  1. Validate Flutter Android pass conditions 9-10 for real, on the user's
     actual RunPod Pod with GPU + a real checkpoint model (not on this
     local sandbox, which has no GPU).
  2. Add INTERNET permission to the real generated Android manifest when a
     real Flutter project shell is created for real device testing.
  3. Only after 1-2 pass, revisit OPEN_TODOS.md / FUTURE_ISSUES_AND_IMPROVEMENTS.md
     and reprioritize.

Sandbox environment kept installed for reuse (do not re-download):
  /tmp/claude-0/-root-comfyui-mobile-system/f3061f5e-90f9-482b-b8ab-f51e1fa15f7d/scratchpad/
    ComfyUI/            official ComfyUI clone + venv with torch(cpu)/aiohttp/etc installed,
                         custom_nodes/ComfyUI-Mobile-Analyzer/ already copied in (with the fix)
    flutter_git/         flutter/flutter stable clone with bootstrapped flutter tool (already
                         built the flutter_tools snapshot once — this is the slow part)
    dart_sdk/             standalone arm64 Dart SDK zip extracted
    comfy_mobile_mvp/     flutter create --platforms=android shell with lib/+pubspec.yaml
                         copied in from the real repo, pub get already done
  This is a session-scratchpad path (not guaranteed permanent across all
  environments) — if a future session finds it gone, it must be recreated;
  see "Runtime validation" below for the exact steps that worked.
  No processes are currently running (ComfyUI server was stopped after
  validation); only the installed files remain.
```

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

Conclusion (Claudeの記録, 2026-07-09 13:22時点): direction and decisions in `PRE_IMPLEMENTATION_ALIGNMENT_DECISIONS.md` are still valid. No large rewrite needed.

Concept detail:

```text
docs/mobile-system/USER_PROVIDED_WORKFLOW_CONCEPT.md
```

### Runtime validation (executed on-device, not just documented)

ComfyUI + the custom node + Flutter tooling were actually installed in the throwaway sandbox directory listed above (outside the repo, CPU-only, aarch64, no GPU), and the real flow was run end-to-end. Results against the 10-item pass condition in `CLAUDE_FINAL_REVIEW_AND_INSTALL.md` (see the numbered list under "## Completed: architecture and limited runtime validation" below):

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

This confirms the client-side data flow (download -> parse -> patch -> submit) is correct end-to-end at the code level. What is NOT confirmed: actual Flutter widget rendering, `file_picker` native Android plugin behavior, and real image generation/display (needs a real GPU + real checkpoint, which this sandbox intentionally does not have).

### Bug fixed (blocker) — pushed

```text
File: analyzer/ComfyUI-Mobile-Analyzer/nodes.py
Fix: added `OUTPUT_NODE = True` to MobileProfileExporter.
Reason: without it, ComfyUI rejects any /prompt containing only this node with
  400 "prompt_no_outputs", because the node has no dependents and wasn't marked
  as an output node itself. Reproduced live, fixed, re-verified live (queue ->
  execute -> zip written -> downloadable).
Commit: 6ab9ef7. Pushed to origin/docs/mobile-system-spec.
```

This was the only code change made. No other files were touched.

### HANDOFF.md rewrite — pushed

```text
Commit: 0f942ab. Pushed to origin/docs/mobile-system-spec.
```

## In progress / not yet done (Claudeの記録, 2026-07-09 13:22時点)

```text
- Nothing is mid-flight. Session was paused cleanly by user request.
- git status is clean; both commits above are pushed; no local-only changes exist.
```

**要確認**: 上記はClaudeが2026-07-09 13:22時点で記録した内容です。その後ChatGPTが同日21:30頃までに本ファイル全体を大幅に拡張しており(下記「## Blocked / deferred」「## Do next when RunPod is available」等、より詳細な項目群が追加されています)。「Nothing is mid-flight」という記述は統合後のドキュメント全体としては古い可能性があります。最新の未完了事項は下部の該当セクションを参照してください。

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
- i2i ON/OFF behavior reference.
- i2i / inpaint mode switch behavior reference.
- image picker + selected image preview behavior reference.
- mask canvas, paint, erase, clear, and brush size behavior reference.
```

(Claudeの記録, 2026-07-09 13:22時点の補足: Still Draft. Do not merge. Both commits (OUTPUT_NODE fix + this HANDOFF.md) are pushed to origin/docs/mobile-system-spec. Architecture direction confirmed valid; no large rewrite triggered.)

Existing HTML profiles under `profiles/` were reviewed as proven behavior references. Details are recorded in:

```text
docs/mobile-system/LEGACY_HTML_REUSE_NOTES.md
docs/mobile-system/I2I_MASK_INPAINT_REUSE_AND_API_PLAN.md
docs/mobile-system/HTML_AND_OFFICIAL_API_CONFLICT_NOTES.md
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
docs/mobile-system/I2I_MASK_INPAINT_REUSE_AND_API_PLAN.md
docs/mobile-system/HTML_AND_OFFICIAL_API_CONFLICT_NOTES.md
docs/mobile-system/SUBGRAPH_AND_BYPASS_ANALYSIS.md
docs/mobile-system/LLM_ASSISTED_WORKFLOW_ANALYSIS.md
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

7. Image input / mask / img2img / inpaint support must be validated against real workflows and ComfyUI upload endpoints.

8. Full HTML, smartphone app, and Analyzer routes must be validated to coexist without official API route conflicts.
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
12. Validate image input / mask / img2img / inpaint workflows when available.
13. Confirm full HTML and smartphone app only call official APIs and do not replace them.
14. Record result using docs/mobile-system/VALIDATION_RESULT_TEMPLATES.md.
15. Compare with existing HTML behavior where useful.
16. Update this HANDOFF.md.
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
20. Confirm image picker/upload behavior when profile contains image inputs.
21. Confirm mask editor/upload behavior when profile contains mask inputs.
22. Confirm img2img/inpaint patch_targets are respected.
23. Record result using docs/mobile-system/VALIDATION_RESULT_TEMPLATES.md.
24. Compare /prompt -> /ws -> /history -> /view and i2i/mask behavior against existing HTML.
25. Update this HANDOFF.md.
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
- Do not create custom routes that collide with official ComfyUI routes.
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
- Image input / mask / img2img / inpaint behavior is validated where profiles require it.
- Full HTML / smartphone app / Analyzer route coexistence is validated.
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
Image input / mask / img2img / inpaint must be workflow-driven, not fixed-HTML-workflow-driven.
Full HTML is a behavior reference and client, not a competing API layer.
```

(Claudeの記録, 2026-07-09 13:22時点の「次にやること」は、冒頭の「Session paused — quick resume summary」に記載済みの内容と重複するため、ここでは繰り返さず参照のみとします。)
