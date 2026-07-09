# Next Action Queue

## Purpose

This file keeps the next actions in one place so future work does not drift.

## Current status

```text
PR: #1
Branch: docs/mobile-system-spec
State: Draft
Merge: do not merge
RunPod GPU validation: not complete
Android validation: not complete
Implementation: paused except for minimal blocker fixes
```

## Done

```text
- Architecture direction documented.
- Official ComfyUI API-first direction documented.
- Analyzer + Flutter MVP scaffold created.
- Claude limited CPU-only runtime validation completed.
- OUTPUT_NODE blocker fixed.
- WEB_DIRECTORY cleanup committed.
- HANDOFF updated.
- Runtime result, blockers, next phase docs added.
- Future features prepared.
- Reference study backlog/checklist prepared.
- Validation/debug/workflow/decision templates prepared.
- RunPod and Android validation runbooks prepared.
- Minimal AI handoff prompts prepared.
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
8. Record result in VALIDATION_RESULT_TEMPLATES.md format.
9. Update HANDOFF.md.
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
10. Record result and update HANDOFF.md.
```

## Do next if something fails

```text
1. Fill docs/mobile-system/DEBUG_REPORT_TEMPLATE.md.
2. Identify failing area:
   - RunPod
   - Android
   - Analyzer
   - workflow
   - model
   - custom node
   - ComfyUI API
3. Fix only the smallest blocker.
4. Re-test the failed path.
5. Update HANDOFF.md.
6. Keep PR Draft.
```

## Do next after both validations pass

```text
1. Run merge readiness check.
2. Update HANDOFF.md with final validation results.
3. Update PR body with final validation results.
4. Decide whether PR can move from Draft to Ready for review.
5. Do not merge automatically without explicit user instruction.
```

## First post-validation feature planning order

```text
1. Better error messages
2. Debug report export
3. Saved profile re-run reliability
4. Image input re-upload behavior
5. Production-safe profile storage decision
6. /object_info-based field metadata
7. /models-based model existence checks
8. Profile details screen
9. Optional UI workflow conversion research
10. Advanced workflow support planning
```

## Reference study order after validation

```text
1. Official ComfyUI server/API behavior
2. Official ComfyUI API workflow examples
3. RunPod Pods behavior
4. /object_info and /models usage details
5. ComfyUI Manager missing-node patterns
6. comfy-portal-endpoint conversion design
7. Civitai workflow/model sharing behavior
8. GitHub profile/workflow storage patterns
9. Android local storage and backup patterns
10. Prompt/style preset patterns
11. RunPod Serverless later
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

## Current safest next action

```text
Wait for RunPod availability, then run RUNPOD_VALIDATION_RUNBOOK.md.
```

If RunPod is still unavailable but Android tooling becomes available first:

```text
Run Android validation only up to connection/profile loading if a reachable ComfyUI URL exists.
Do not mark full Android validation PASS until real generation and image display work.
```
