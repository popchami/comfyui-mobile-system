# PR Body Update Draft

## Purpose

Use this text to update PR #1 body when PR-body editing is available.

Current PR:

```text
Repository: popchami/comfyui-mobile-system
PR: #1
Branch: docs/mobile-system-spec
State: Draft
Do not merge yet.
```

## Suggested PR body addition

Add this near the top of the PR body, under the current status section.

````markdown
## Final smartphone-only status

```text
Smartphone-only preparation: COMPLETE
Smartphone-only implementation: COMPLETE
Smartphone-only documentation: COMPLETE
Smartphone-only handoff preparation: COMPLETE
RunPod GPU validation: NOT COMPLETE
Android real-device/emulator validation: NOT COMPLETE
Merge: DO NOT MERGE
Next meaningful work: REAL VALIDATION ONLY
```

## Current source of truth

Read these first:

```text
docs/mobile-system/HANDOFF.md
docs/mobile-system/SMARTPHONE_ONLY_COMPLETION_REPORT.md
docs/mobile-system/RUNTIME_VALIDATION_RESULT.md
docs/mobile-system/BLOCKERS_AFTER_CLAUDE.md
docs/mobile-system/NEXT_PHASE_PLAN.md
docs/mobile-system/NEXT_ACTION_QUEUE.md
docs/mobile-system/DOCS_AUDIT_RESULT.md
docs/mobile-system/STATIC_REVIEW_NOTES.md
```

## Validation runbooks

```text
docs/mobile-system/RUNPOD_VALIDATION_RUNBOOK.md
docs/mobile-system/ANDROID_VALIDATION_RUNBOOK.md
docs/mobile-system/VALIDATION_RESULT_TEMPLATES.md
docs/mobile-system/DEBUG_REPORT_TEMPLATE.md
```

## Smartphone-side app features prepared

```text
- ComfyUI URL save/restore
- /system_stats connection check
- /object_info capability check
- /models/{folder} read-only helpers
- /queue helper + Check queue
- /interrupt helper + Interrupt
- friendly error messages
- profile warning display
- missing model / missing custom node warning
- Check environment
- ModelFolderResolver
- EnvironmentModelChecker
- profile-specific previous input save/restore
- Reset to profile defaults
- Random seed
- Use last seed
- selected image preview
- /prompt + client_id
- /ws progress
- /history fallback
- /view generated image display
- session history
- generated image large preview
- generated image metadata
- collapsible generated UI sections
```

## Feature detail docs added

```text
docs/mobile-system/APP_INPUT_STATE_CONTROLS.md
docs/mobile-system/APP_QUEUE_AND_ERROR_CONTROLS.md
docs/mobile-system/APP_CAPABILITY_CHECKS.md
docs/mobile-system/APP_PROFILE_WARNING_DISPLAY.md
docs/mobile-system/APP_MODEL_FOLDER_RESOLVER.md
docs/mobile-system/APP_ENVIRONMENT_MODEL_CHECKER.md
docs/mobile-system/APP_GENERATED_IMAGE_METADATA.md
```

## Still blocked before merge

```text
- RunPod ComfyUI validation.
- Real checkpoint image generation.
- Android device/emulator validation.
- Flutter app end-to-end generated image display.
- Android validation of generated UI grouping, seed controls, environment checks, queue/interrupt, and generated image metadata.
```

## Stop condition

```text
Do not add more smartphone-only features before real validation.
Do not mark PR ready for review or merge until RunPod + Android validation pass and HANDOFF.md is updated with final results.
```
````

## Reminder

```text
PR #1 must remain Draft and unmerged until RunPod + Android validation pass.
```
