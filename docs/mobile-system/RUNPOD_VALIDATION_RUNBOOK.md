# RunPod Validation Runbook

## Purpose

This is the step-by-step runbook for validating the ComfyUI Mobile System on RunPod.

Use this when RunPod becomes available again.

## Current rule

```text
Do not merge PR #1 until this RunPod validation and Android validation both pass.
```

## What this runbook proves

```text
RunPod ComfyUI can load ComfyUI-Mobile-Analyzer,
export a profile zip,
serve it through Analyzer routes,
run a real model generation,
and expose generated images through official ComfyUI APIs.
```

## Before starting

Confirm:

```text
- Repository: popchami/comfyui-mobile-system
- Branch: docs/mobile-system-spec
- PR: #1
- PR is still Draft
- RunPod is available
- A GPU Pod can be started
- A ComfyUI environment is available
- At least one approved checkpoint/model is already available or manually prepared
```

Rules:

```text
- Do not auto-download models.
- Do not auto-install custom nodes.
- Do not merge PR.
- Do not test Serverless yet.
```

## Validation steps

### Step 1: Start RunPod ComfyUI

Record:

```text
RunPod Pod type:
GPU:
ComfyUI template/image:
ComfyUI URL:
Started at:
```

Check:

```text
ComfyUI opens in browser: PASS / FAIL
/system_stats responds: PASS / FAIL
```

### Step 2: Place Analyzer

Expected path:

```text
ComfyUI/custom_nodes/ComfyUI-Mobile-Analyzer/
```

Use the Analyzer from the PR branch:

```text
analyzer/ComfyUI-Mobile-Analyzer/
```

Check:

```text
__init__.py exists: PASS / FAIL
nodes.py exists: PASS / FAIL
server.py exists: PASS / FAIL
No WEB_DIRECTORY="web" declaration: PASS / FAIL
```

### Step 3: Restart ComfyUI

Check:

```text
ComfyUI starts: PASS / FAIL
Analyzer imports without error: PASS / FAIL
Mobile Profile Exporter appears: PASS / FAIL
```

If import fails, use:

```text
docs/mobile-system/DEBUG_REPORT_TEMPLATE.md
docs/mobile-system/VALIDATION_RESULT_TEMPLATES.md
```

### Step 4: Export profile zip

Use a minimal API workflow first.

Record:

```text
Workflow name:
Workflow format: API workflow
Model referenced:
```

Check:

```text
Mobile Profile Exporter runs: PASS / FAIL
Zip created under output/mobile_profiles: PASS / FAIL
workflow.json included: PASS / FAIL
app_profile.json included: PASS / FAIL
app_profile parses: PASS / FAIL
patch_targets present: PASS / FAIL
```

### Step 5: Check Analyzer routes

Check:

```text
GET /mobile_analyzer/profiles: PASS / FAIL
GET /mobile_analyzer/profiles/{id}/download: PASS / FAIL
Downloaded zip opens: PASS / FAIL
```

Record:

```text
Profile id:
Profile name:
Downloaded zip size:
```

### Step 6: Real generation with actual model

Use an already available model.

Record:

```text
Checkpoint/model used:
Model was already present: yes / no
No auto-download performed: yes / no
```

Check:

```text
/prompt accepted: PASS / FAIL
/ws progress received: PASS / FAIL
/history/{prompt_id} returns output: PASS / FAIL
/view fetches image: PASS / FAIL
Generated image exists: PASS / FAIL
```

### Step 7: Record result

Use:

```text
docs/mobile-system/VALIDATION_RESULT_TEMPLATES.md
Template 1: RunPod ComfyUI validation result
```

Update:

```text
docs/mobile-system/HANDOFF.md
```

If RunPod validation changes merge readiness, update PR body too.

## Pass condition

RunPod validation is PASS only if:

```text
- ComfyUI starts with Analyzer.
- Mobile Profile Exporter appears.
- Profile zip exports.
- Analyzer profile list/download routes work.
- Real model generation works.
- /prompt -> /ws -> /history -> /view path works.
```

## Partial condition

RunPod validation is PARTIAL if:

```text
- Analyzer loads and profile export works,
  but real model generation cannot be completed.
```

## Fail condition

RunPod validation is FAIL if:

```text
- ComfyUI cannot start with Analyzer.
- Mobile Profile Exporter cannot be loaded.
- Profile zip cannot be generated.
- Analyzer routes do not work.
```

## Common failures to capture

```text
- Analyzer import error
- missing model
- /prompt rejected
- /ws connection failed
- /history empty
- /view image not found
- RunPod URL expired/changed
- uploaded input image missing
```

## Next action after PASS

```text
Proceed to Android validation using docs/mobile-system/ANDROID_VALIDATION_RUNBOOK.md
```

## Next action after PARTIAL or FAIL

```text
1. Fill DEBUG_REPORT_TEMPLATE.md.
2. Fill VALIDATION_RESULT_TEMPLATES.md.
3. Fix only the smallest blocker.
4. Update HANDOFF.md.
5. Keep PR Draft.
```
