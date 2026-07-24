# Priority and Conflict Review

## Purpose

This file reviews the remaining work before Claude runtime validation.

The goal is to decide:

```text
1. What must be done before install validation.
2. What should wait until after install validation.
3. What should not be done now because it could conflict with MVP install readiness.
```

## Current principle

The current PR is not trying to finish the whole product.

The current target is:

```text
ComfyUI Analyzer can be installed.
Profile zip can be exported.
Flutter Android MVP can download, save, open, patch, submit, and display one generated image.
```

Everything that does not directly support that target should wait.

## Category A: should be done before install validation

These items reduce Claude/runtime confusion and are worth doing before install validation.

### A1. Keep Analyzer output and Flutter parser aligned

Reason:

```text
If app_profile output and Flutter parser disagree, install validation fails even if ComfyUI works.
```

Current status:

```text
Mostly done.
```

Already improved:

```text
- output_app_profile_example.json updated
- RemoteProfile model added
- getRemoteProfiles() now returns List<RemoteProfile>
- RemoteProfilesScreen no longer uses dynamic profile maps
```

Remaining before install:

```text
- Claude should still verify actual generated app_profile.json against Flutter parser.
```

### A2. Confirm minimum Flutter project shell path

Reason:

```text
mobile-app/flutter_mvp may not include android/ ios/ web/ platform folders.
```

This is not a blocker if documented.

Current status:

```text
Documented in RUN_CHECKLIST.md, CLAUDE_FINAL_REVIEW_AND_INSTALL.md, and PRE_CLAUDE_STATUS.md.
```

Do not spend time generating a full Flutter shell inside this PR until Claude runs it.

### A3. Keep Android-first target explicit

Reason:

```text
GenerateScreen uses file_picker + dart:io File.
Flutter Web is not required for MVP.
```

Current status:

```text
Done.
```

### A4. Keep API routes simple and testable

Reason:

```text
The app depends on /mobile_analyzer/profiles and /mobile_analyzer/profiles/{id}/download.
```

Current status:

```text
server.py returns profile metadata and download_url.
Download lookup tolerates ids with or without .zip.
```

Remaining before install:

```text
- Claude must verify route registration in real ComfyUI runtime.
```

### A5. Preserve safety rules

Reason:

```text
The app must not become a workflow editor before basic install works.
```

Current status:

```text
Documented repeatedly.
```

Rules:

```text
- patch only patch_targets
- do not delete unknown nodes
- do not auto-install nodes
- do not auto-download models
- patch a generation copy, not the saved original workflow
```

## Category B: should wait until after install validation

These are important, but doing them now can delay or destabilize the install test.

### B1. UI workflow to API workflow conversion

Importance:

```text
High later.
```

Why wait:

```text
It touches Analyzer parsing deeply and may break the current API-workflow MVP.
```

Use after install:

```text
Once pasted API workflow export works, add UI workflow import/conversion as a separate step.
```

### B2. object_info checks

Importance:

```text
High later.
```

Why wait:

```text
Requires real ComfyUI runtime behavior and may be better implemented after Claude confirms the plugin loads.
```

Use after install:

```text
Use object_info to verify node classes, input types, combo options, and allowed values.
```

### B3. Model file existence checks

Importance:

```text
High later.
```

Why wait:

```text
Model folder layouts vary by ComfyUI setup. Adding this before runtime validation can create false blockers.
```

Current safe behavior:

```text
Detected model names are listed as unverified references.
```

### B4. File-based local storage

Importance:

```text
Medium-high later.
```

Why wait:

```text
shared_preferences is enough to prove MVP save/load. File storage is better later for large workflows but not needed before first install validation.
```

### B5. Advanced node support

Includes:

```text
ControlNet
Upscale
IPAdapter
FaceDetailer
LoRA advanced controls
RemBG
Inpaint
Wildcard
Ollama/LLM
```

Why wait:

```text
These expand scope and make install validation harder.
```

Use after install:

```text
Add one advanced feature at a time after base generation works.
```

### B6. Node color matching

Importance:

```text
Usability improvement.
```

Why wait:

```text
It depends on UI workflow metadata and does not affect install readiness.
```

### B7. Bypass handling

Importance:

```text
High for advanced workflow correctness.
```

Why wait:

```text
It requires careful distinction between saved workflow state and per-generation patched copy. Doing it before base install may introduce workflow mutation bugs.
```

### B8. Subgraph handling

Importance:

```text
High later.
```

Why wait:

```text
Subgraph structure may change how nodes and patch_targets are addressed. It should wait until normal flat workflow import works.
```

## Category C: do not do now

These are likely to conflict with install readiness.

### C1. Automatic custom node install

Do not do now.

Reason:

```text
It creates security and environment risks. MVP should report missing nodes, not install them.
```

### C2. Automatic model download

Do not do now.

Reason:

```text
Large files, licensing, storage, NSFW/model-source concerns, and RunPod cost risk.
```

### C3. Full ComfyUI workflow editor

Do not do now.

Reason:

```text
It conflicts with the MVP rule: patch only patch_targets.
```

### C4. Google Drive / cloud sync

Do not do now.

Reason:

```text
Storage and NSFW safety concerns should be designed separately after local generation works.
```

### C5. Payment / monetization

Do not do now.

Reason:

```text
No value until install and generation path is proven.
```

### C6. ComfyUI Manager registration

Do not do now.

Reason:

```text
The custom node must be runtime-tested first.
```

## Potential conflicts

### Conflict 1: UI workflow conversion vs current API workflow MVP

Risk:

```text
Adding conversion now may break the minimal API workflow test.
```

Decision:

```text
Wait until API workflow export/import works.
```

### Conflict 2: object_info validation vs incomplete runtime access

Risk:

```text
Strict checks may mark valid workflows as invalid before runtime behavior is understood.
```

Decision:

```text
Keep current partial/unverified status until runtime confirmed.
```

### Conflict 3: file storage migration vs current save/load proof

Risk:

```text
Switching storage now could introduce Android permissions/path bugs before MVP is proven.
```

Decision:

```text
Keep shared_preferences for first validation.
```

### Conflict 4: bypass handling vs saved workflow safety

Risk:

```text
Bypass toggles could accidentally mutate the saved workflow.
```

Decision:

```text
Do not implement until generation uses explicit copied workflow snapshots and tests exist.
```

### Conflict 5: node color matching vs UI/API workflow metadata

Risk:

```text
API workflows may not contain node colors. Implementing this now could create fake metadata or confusion.
```

Decision:

```text
Wait until UI workflow metadata import exists.
```

## Before install: final allowed work

The only work that should still be allowed before Claude install validation:

```text
1. Documentation cleanup that helps Claude run the install.
2. Obvious static type fixes.
3. Analyzer/Flutter shape alignment fixes.
4. Small fixes that reduce install ambiguity.
```

Do not add new feature categories before install validation.

## Recommendation

Proceed to Claude runtime validation after one final check of:

```text
- PR file list
- README links to PRE_CLAUDE_STATUS / CLAUDE_FINAL_REVIEW_AND_INSTALL / STATIC_REVIEW_NOTES
- no known dynamic typing mismatch in RemoteProfilesScreen
- no known app_profile example mismatch
```

After Claude confirms install readiness, reprioritize OPEN_TODOS.
