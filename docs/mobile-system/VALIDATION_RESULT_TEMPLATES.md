# Validation Result Templates

## Purpose

Use these templates to record future RunPod, Android, reference-study, and blocker-fix results consistently.

These templates are documentation only. They do not change implementation.

## Rule

After any real validation pass, update:

```text
docs/mobile-system/HANDOFF.md
PR body if merge readiness changed
```

If the validation creates new decisions or blockers, also update the relevant planning document.

---

# Template 1: RunPod ComfyUI validation result

## Summary

```text
Date:
Reviewer:
Environment:
RunPod Pod type/GPU:
ComfyUI version/commit if known:
Analyzer branch/commit:
Result: PASS / PARTIAL / FAIL
```

## Startup

```text
ComfyUI starts: PASS / FAIL
Analyzer imports: PASS / FAIL
Mobile Profile Exporter appears: PASS / FAIL
No import error after WEB_DIRECTORY cleanup: PASS / FAIL
```

## Profile export

```text
Minimal API workflow used: yes / no
Profile zip generated: PASS / FAIL
Zip path:
Zip contains workflow.json: PASS / FAIL
Zip contains app_profile.json: PASS / FAIL
app_profile parses: PASS / FAIL
patch_targets present: PASS / FAIL
```

## Analyzer routes

```text
GET /mobile_analyzer/profiles: PASS / FAIL
GET /mobile_analyzer/profiles/{id}/download: PASS / FAIL
Downloaded zip opens: PASS / FAIL
```

## Real generation

```text
Checkpoint/model used:
Model already installed: yes / no
No auto-download performed: yes / no
/prompt accepted: PASS / FAIL
/ws progress received: PASS / FAIL
/history result available: PASS / FAIL
/view image fetched: PASS / FAIL
Generated image displayed somewhere: PASS / FAIL
```

## Problems found

```text
- Problem 1:
- Problem 2:
```

## Decision

```text
Can continue to Android validation: yes / no
Need code fix first: yes / no
Need doc update: yes / no
```

---

# Template 2: Android Flutter validation result

## Summary

```text
Date:
Reviewer:
Device/emulator:
Android version:
Flutter version:
ComfyUI URL type:
Analyzer branch/commit:
Result: PASS / PARTIAL / FAIL
```

## Project shell

```text
Real Flutter Android project shell created: PASS / FAIL
mobile-app/flutter_mvp/lib copied: PASS / FAIL
pubspec.yaml copied: PASS / FAIL
Android INTERNET permission added: PASS / FAIL
flutter pub get: PASS / FAIL
flutter analyze: PASS / FAIL
flutter run: PASS / FAIL
```

Required permission:

```xml
<uses-permission android:name="android.permission.INTERNET" />
```

## App flow

```text
SetupScreen opens: PASS / FAIL
/system_stats connection check: PASS / FAIL
Remote profiles list loads: PASS / FAIL
Profile zip downloads: PASS / FAIL
Local profile saves: PASS / FAIL
Local profile opens: PASS / FAIL
GenerateScreen renders fields: PASS / FAIL
Image picker works if needed: PASS / FAIL
Image upload works if needed: PASS / FAIL
Workflow patches only patch_targets: PASS / FAIL
/prompt submit works: PASS / FAIL
/ws progress works: PASS / FAIL
/history result works: PASS / FAIL
/view image displays: PASS / FAIL
```

## Problems found

```text
- Problem 1:
- Problem 2:
```

## Decision

```text
MVP Android path proven: yes / no
Need code fix first: yes / no
Need doc update: yes / no
```

---

# Template 3: Reference study result

## Summary

```text
Date:
Reviewer:
Reference area:
Result: adopted / partially adopted / deferred / rejected
```

## What was studied

```text
- Source/topic 1:
- Source/topic 2:
```

## What we learned

```text
- Finding 1:
- Finding 2:
```

## What to adopt

```text
- Adopt 1:
- Adopt 2:
```

## What not to adopt

```text
- Do not adopt 1:
- Do not adopt 2:
```

## Impacted docs/specs

```text
- Doc 1:
- Doc 2:
```

## Follow-up issues

```text
- Issue draft/title 1:
- Issue draft/title 2:
```

---

# Template 4: Blocker fix result

## Summary

```text
Date:
Reviewer:
Blocker:
Fix branch/commit:
Result: fixed / partial / failed
```

## Original problem

```text
What failed:
Where it failed:
Why it mattered:
```

## Fix applied

```text
Files changed:
What changed:
Why this is minimal:
```

## Re-test result

```text
Original failure reproduced before fix: yes / no
Fix tested after change: yes / no
Test environment:
Result:
```

## Remaining risk

```text
- Risk 1:
- Risk 2:
```

## Docs updated

```text
- HANDOFF.md: yes / no
- PR body: yes / no
- Test plan: yes / no
- Other:
```

---

# Template 5: Merge readiness check

## Required before merge

```text
PR is not Draft anymore: yes / no
RunPod ComfyUI validation passed: yes / no
Real checkpoint generation passed: yes / no
Android device/emulator validation passed: yes / no
HANDOFF.md updated with final results: yes / no
PR body updated with final results: yes / no
No unresolved blocking issues: yes / no
```

## Decision

```text
Ready to merge: yes / no
Reason:
```
