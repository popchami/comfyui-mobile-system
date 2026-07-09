# Decision Record Template

## Purpose

Use this template when the project makes a decision that future AI assistants must not accidentally reverse.

This keeps the project stable across ChatGPT, Claude, Codex, and manual GitHub work.

## When to create a decision record

Create or update a decision record when deciding:

```text
- architecture direction
- API dependency direction
- workflow compatibility rules
- storage strategy
- RunPod operation model
- Android app behavior
- security/safety boundaries
- what not to implement
```

## Template

# Decision: <short decision title>

## Status

```text
proposed / accepted / superseded / rejected
```

## Date

```text
YYYY-MM-DD
```

## Context

```text
What problem or conflict caused this decision?
What options existed?
Why does this matter?
```

## Decision

```text
What did we decide?
```

## Reason

```text
Why is this the right decision now?
```

## Consequences

### Positive

```text
- Positive consequence 1
- Positive consequence 2
```

### Negative / tradeoff

```text
- Tradeoff 1
- Tradeoff 2
```

## What this allows

```text
- Allowed action 1
- Allowed action 2
```

## What this forbids

```text
- Forbidden action 1
- Forbidden action 2
```

## Revisit condition

```text
When should this decision be revisited?
What evidence would justify changing it?
```

## Related docs

```text
- docs/mobile-system/...
```

## Related PRs/issues

```text
- PR #
- Issue #
```

---

# Current high-value decisions to preserve

These are not full records here, but should remain visible.

## Keep current system, adjust implementation strategy

```text
Do not discard the current system.
Use the current Analyzer + Android app direction, but align implementation with official APIs.
```

## Official ComfyUI APIs first

```text
Use official ComfyUI APIs wherever possible.
Do not duplicate official ComfyUI behavior through custom endpoints.
```

## Custom code only for mobile profile layer

```text
Custom Analyzer code should focus on exporting mobile-safe profile zips.
```

## No auto-install / no auto-download

```text
Do not auto-install custom nodes.
Do not auto-download models.
Only report missing requirements.
```

## No full workflow editor

```text
The Android app is not a full ComfyUI workflow editor.
It patches only app_profile.json.patch_targets.
```

## RunPod Pods first, Serverless later

```text
Validate with RunPod Pods first.
Do not switch MVP to RunPod Serverless before the Pod-based path works.
```

## UI workflow conversion optional

```text
UI workflow to API workflow conversion is useful later, but optional after MVP validation.
Do not make Playwright/Chromium mandatory for MVP.
```

## Generated images local by default

```text
Do not enable automatic cloud sync for generated images by default.
Be careful with NSFW outputs and user privacy.
```
