# Post-Validation Legacy HTML UI Review

## Purpose

This file records the decision for how to treat the visual UI of the existing legacy HTML profiles.

## Decision

Do not copy the legacy HTML visual design into the Flutter MVP before RunPod and Android validation.

Use the legacy HTML as:

```text
- behavior reference
- mobile UX friction reference
- fallback logic reference
- known-good ComfyUI operation reference
```

Do not use the legacy HTML as:

```text
- final Flutter visual design
- final app architecture
- universal layout source
- source of hardcoded prompt/model/profile assumptions
```

## Why

The old HTML files were built as fixed per-profile mobile pages.

The new app is dynamic:

```text
app_profile.json
+ workflow.json
+ patch_targets
+ Flutter generated UI
```

Because the new app generates UI from profile metadata, copying the old fixed HTML layout directly would make the MVP harder to validate and could reintroduce workflow-specific assumptions.

## What was already reused

The Flutter MVP already reuses proven HTML behavior where it is safe:

```text
- saved ComfyUI URL restore
- /prompt + client_id
- /ws progress
- /history polling fallback
- /view image display
- /upload/image handling
- selected image preview
- session generated image history
- large image preview
- seed reuse
- collapsible sections concept
```

## Post-validation UI improvement issue

After RunPod + Android validation passes, create a UI improvement issue with this scope:

```text
Review legacy HTML visual layout and decide which UI patterns should be brought into the Flutter app.
```

Candidate review points:

```text
- Overall spacing and vertical density on Android.
- Button placement and action hierarchy.
- Generated image area placement.
- Session history visual style.
- Warning/status display style.
- Selected image preview style.
- Seed controls visual layout.
- Advanced setting section labels.
- Whether legacy visual selected-state markers should be added.
```

## Acceptance criteria for that future issue

```text
- Android validation has already passed or produced concrete UI screenshots.
- Legacy HTML screenshots or direct file review are compared against the Flutter screen.
- Improvements are selected based on real Android usability, not visual copying alone.
- No hardcoded workflow/model/prompt assumptions are introduced.
- app_profile.json + patch_targets architecture remains unchanged.
```

## Current stop rule

```text
Do not perform this UI review before RunPod + Android validation.
Do not add more smartphone-only UI changes before real validation.
```
