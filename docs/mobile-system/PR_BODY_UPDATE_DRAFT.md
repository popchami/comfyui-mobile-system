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

Add this under the current source-of-truth / validation docs section.

````markdown
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
```

## Validation runbooks

```text
docs/mobile-system/RUNPOD_VALIDATION_RUNBOOK.md
docs/mobile-system/ANDROID_VALIDATION_RUNBOOK.md
```

## Minimal AI handoff

```text
docs/mobile-system/AI_MINIMAL_HANDOFF_PROMPTS.md
```

## Added smartphone-only planning docs

```text
docs/mobile-system/FUTURE_FEATURE_PREP.md
docs/mobile-system/ADDITIONAL_FEATURE_CANDIDATES.md
docs/mobile-system/APP_PROFILE_EVOLUTION_PLAN.md
docs/mobile-system/UX_FLOW_PREP.md
docs/mobile-system/POST_VALIDATION_ISSUE_DRAFTS.md
docs/mobile-system/REFERENCE_STUDY_BACKLOG.md
docs/mobile-system/REFERENCE_TO_FEATURE_MAP.md
docs/mobile-system/REFERENCE_STUDY_CHECKLIST.md
docs/mobile-system/VALIDATION_RESULT_TEMPLATES.md
docs/mobile-system/DEBUG_REPORT_TEMPLATE.md
docs/mobile-system/WORKFLOW_COMPATIBILITY_REPORT_TEMPLATE.md
docs/mobile-system/DECISION_RECORD_TEMPLATE.md
```

## Latest smartphone-only preparation status

```text
- No runtime validation was performed in this prep pass.
- No Termux work was performed.
- No RunPod work was performed.
- No Flutter runtime work was performed.
- Documentation, planning, validation runbooks, reporting templates, and AI handoff prompts were updated.
- HANDOFF.md and README.md are the current main entrypoints.
```

## Still blocked before merge

```text
- RunPod ComfyUI validation.
- Real checkpoint image generation.
- Android device/emulator validation.
- Flutter app end-to-end generated image display.
```
````

## Reminder

```text
Do not mark PR ready for review or merge until RunPod + Android validation pass and HANDOFF.md is updated with final results.
```
