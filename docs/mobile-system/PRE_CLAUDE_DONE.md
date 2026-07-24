# Pre-Claude Work Complete

## Status

Pre-Claude preparation work is complete.

This PR is now ready to hand to Claude for runtime validation.

## Current PR state

```text
PR: #1 Add ComfyUI mobile system architecture and MVP scaffold
Branch: docs/mobile-system-spec
State: open
Draft: true
Merged: false
Label: runtime-validation-pending
Changed files: 49
Commits: 114+
```

## What is complete

```text
- PR is Draft to prevent accidental merge.
- PR has runtime-validation-pending label.
- PR body explains current scope and pass conditions.
- Claude copy-paste prompt exists.
- Claude read order is documented.
- Pre-Claude status summary exists.
- Priority/conflict review exists.
- Static review notes exist.
- Open TODOs are marked as post-install-validation work.
- Unsafe/future work is explicitly out of scope before runtime validation.
```

## Claude entrypoint

Use this file first when handing off to Claude:

```text
docs/mobile-system/CLAUDE_COPYPASTE_PROMPT.md
```

Then Claude should read:

```text
docs/mobile-system/PRE_CLAUDE_STATUS.md
docs/mobile-system/PRIORITY_CONFLICT_REVIEW.md
docs/mobile-system/CLAUDE_FINAL_REVIEW_AND_INSTALL.md
docs/mobile-system/STATIC_REVIEW_NOTES.md
```

## Do not continue feature work before Claude

No more feature work should be added before runtime validation.

Allowed before Claude only if absolutely necessary:

```text
- typo fixes
- broken link fixes
- documentation wording fixes
```

Not allowed before Claude:

```text
- new ComfyUI Analyzer features
- new Flutter features
- storage migration
- object_info implementation
- model existence checks
- UI workflow conversion
- bypass handling
- subgraph handling
- node color handling
- automatic installs
- automatic downloads
```

## Runtime validation target

Claude should confirm:

```text
1. ComfyUI loads ComfyUI-Mobile-Analyzer.
2. Mobile Profile Exporter appears in ComfyUI.
3. Mobile Profile Exporter creates a zip under output/mobile_profiles.
4. Zip contains workflow.json and app_profile.json.
5. /mobile_analyzer/profiles returns profile metadata.
6. /mobile_analyzer/profiles/{id}/download downloads the zip.
7. Flutter MVP passes flutter pub get.
8. Flutter MVP passes flutter analyze or only has documented non-blocking warnings.
9. Flutter Android app can connect to ComfyUI.
10. Flutter Android app can download, save, open, patch, submit, and display at least one generated image.
```

## After Claude passes runtime validation

Then this PR can move from Draft to Ready for Review or be prepared for merge.

After that, revisit:

```text
docs/mobile-system/OPEN_TODOS.md
```
