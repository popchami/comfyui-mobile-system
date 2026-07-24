# AI Minimal Handoff Prompts

## Purpose

Use these short prompts when handing the project to Claude, ChatGPT, Codex, or another AI assistant.

The goal is to avoid wasting tokens by pasting the full project history every time.

## Rule

Start with the shortest prompt that fits the task.

If the AI needs more context, point it to the relevant docs instead of pasting everything.

---

# Prompt 1: Current status check

```text
Repository: popchami/comfyui-mobile-system
PR: #1
Branch: docs/mobile-system-spec

Use the PR branch, not main.
The PR is Draft and must not be merged yet.

Read these first:
- docs/mobile-system/HANDOFF.md
- docs/mobile-system/RUNTIME_VALIDATION_RESULT.md
- docs/mobile-system/BLOCKERS_AFTER_CLAUDE.md
- docs/mobile-system/NEXT_PHASE_PLAN.md

Task:
Tell me the current status, what is already done, what is blocked, and the next action.
Do not implement anything yet.
```

---

# Prompt 2: RunPod validation

```text
Repository: popchami/comfyui-mobile-system
PR: #1
Branch: docs/mobile-system-spec

Use the PR branch, not main.
Do not merge.
Do not auto-download models.
Do not auto-install custom nodes.

Read:
- docs/mobile-system/RUNPOD_VALIDATION_RUNBOOK.md
- docs/mobile-system/VALIDATION_RESULT_TEMPLATES.md
- docs/mobile-system/DEBUG_REPORT_TEMPLATE.md

Task:
Follow the RunPod validation runbook.
Validate ComfyUI-Mobile-Analyzer on RunPod, profile zip export, Analyzer routes, and real model generation.
Record PASS / PARTIAL / FAIL and update HANDOFF.md with the result.
```

---

# Prompt 3: Android validation

```text
Repository: popchami/comfyui-mobile-system
PR: #1
Branch: docs/mobile-system-spec

Use the PR branch, not main.
Do not merge.
Do not turn the app into a full workflow editor.
Patch only app_profile.json.patch_targets.

Read:
- docs/mobile-system/ANDROID_VALIDATION_RUNBOOK.md
- mobile-app/flutter_mvp/RUN_CHECKLIST.md
- docs/mobile-system/VALIDATION_RESULT_TEMPLATES.md
- docs/mobile-system/DEBUG_REPORT_TEMPLATE.md

Task:
Validate the Flutter Android MVP against a real ComfyUI URL.
Confirm connection, remote profile download, local save/open, generation submit, /ws, /history, and /view image display.
Record PASS / PARTIAL / FAIL and update HANDOFF.md with the result.
```

---

# Prompt 4: Fix a blocker only

```text
Repository: popchami/comfyui-mobile-system
PR: #1
Branch: docs/mobile-system-spec

Use the PR branch, not main.
Do not merge.
Do not add unrelated features.
Fix only the smallest blocker.

Read:
- docs/mobile-system/HANDOFF.md
- docs/mobile-system/BLOCKERS_AFTER_CLAUDE.md
- docs/mobile-system/DEBUG_REPORT_TEMPLATE.md
- docs/mobile-system/VALIDATION_RESULT_TEMPLATES.md

Problem:
<paste the failure/debug report here>

Task:
Identify the smallest safe fix.
Make only that fix.
Re-test the failing path if possible.
Update HANDOFF.md with what changed and what remains unverified.
```

---

# Prompt 5: Reference study

```text
Repository: popchami/comfyui-mobile-system
PR: #1
Branch: docs/mobile-system-spec

Use the PR branch, not main.
Do not implement anything yet.
Do not copy external code.

Read:
- docs/mobile-system/REFERENCE_STUDY_BACKLOG.md
- docs/mobile-system/REFERENCE_TO_FEATURE_MAP.md
- docs/mobile-system/REFERENCE_STUDY_CHECKLIST.md

Task:
Study the requested reference area and summarize:
- what we learned
- what to adopt
- what not to adopt
- which docs/specs should change
- which future issue should be opened later
```

---

# Prompt 6: Future feature planning

```text
Repository: popchami/comfyui-mobile-system
PR: #1
Branch: docs/mobile-system-spec

Use the PR branch, not main.
Do not implement feature code yet.

Read:
- docs/mobile-system/FUTURE_FEATURE_PREP.md
- docs/mobile-system/ADDITIONAL_FEATURE_CANDIDATES.md
- docs/mobile-system/APP_PROFILE_EVOLUTION_PLAN.md
- docs/mobile-system/UX_FLOW_PREP.md
- docs/mobile-system/POST_VALIDATION_ISSUE_DRAFTS.md

Task:
Take the requested feature idea and turn it into a clear future issue draft with:
- problem
- scope
- required data/API
- acceptance criteria
- out of scope
- risks
```

---

# Prompt 7: Merge readiness check

```text
Repository: popchami/comfyui-mobile-system
PR: #1
Branch: docs/mobile-system-spec

Use the PR branch, not main.
Do not merge automatically.

Read:
- docs/mobile-system/HANDOFF.md
- docs/mobile-system/RUNTIME_VALIDATION_RESULT.md
- docs/mobile-system/VALIDATION_RESULT_TEMPLATES.md
- docs/mobile-system/BLOCKERS_AFTER_CLAUDE.md

Task:
Check whether PR #1 is ready to merge.
Use the merge readiness checklist.
If not ready, list exactly what remains.
```

---

# Prompt 8: Debug report analysis

```text
Repository: popchami/comfyui-mobile-system
PR: #1
Branch: docs/mobile-system-spec

Use the PR branch, not main.
Do not implement until the cause is clear.

Read:
- docs/mobile-system/DEBUG_REPORT_TEMPLATE.md
- docs/mobile-system/VALIDATION_RESULT_TEMPLATES.md
- docs/mobile-system/WORKFLOW_COMPATIBILITY_REPORT_TEMPLATE.md

Debug report:
<paste report here>

Task:
Explain the likely cause, which area failed, what to check next, and whether this is a RunPod, Android, Analyzer, workflow, model, or custom-node issue.
```

---

# Minimal context to always include

```text
Important rules:
- PR #1 is Draft.
- Use branch docs/mobile-system-spec.
- Do not merge yet.
- Do not auto-install custom nodes.
- Do not auto-download models.
- Do not make Android app a full workflow editor.
- Patch only app_profile.json.patch_targets.
- Preserve unknown workflow nodes.
- Use official ComfyUI APIs where possible.
- RunPod Pods first, Serverless later.
```
