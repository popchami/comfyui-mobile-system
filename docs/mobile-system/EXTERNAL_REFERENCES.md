# External References

## Purpose

This file records external projects that may be useful as references.

The goal is to learn from good ideas, architecture, API design, and workflow, while keeping this project's implementation original.

## Policy

```text
Reference ideas, not copy code.
```

Allowed:

```text
- Study architecture.
- Study endpoint design.
- Study UX flow.
- Study problem-solving approach.
- Re-implement our own version from our own requirements.
- Record license requirements if later integration is considered.
```

Not allowed:

```text
- Copy code and pretend it is original.
- Remove copyright or license notices.
- Bundle external code without preserving its license.
- Add heavy optional dependencies before runtime validation.
```

## Reference: comfy-portal-endpoint

Repository:

```text
https://github.com/ShunL12324/comfy-portal-endpoint
```

License:

```text
MIT License
Copyright: Shun.L
```

Why it matters:

```text
comfy-portal-endpoint solves a related problem:
UI workflow to API workflow conversion for ComfyUI.
```

Important observed behavior:

```text
- Provides REST endpoints under ComfyUI.
- Handles workflow list/get/save.
- Converts UI workflow format to API workflow format.
- Uses the real ComfyUI frontend through headless Chromium / Playwright.
- Uses graphToPrompt through the frontend, which may improve compatibility with custom nodes.
```

Relevant endpoints to study:

```text
/cpe/health
/cpe/workflow/list
/cpe/workflow/get
/cpe/workflow/save
/cpe/workflow/convert
/cpe/workflow/get-and-convert
```

How it may influence this project:

```text
UI workflow
  ↓
conversion to API workflow
  ↓
ComfyUI-Mobile-Analyzer
  ↓
app_profile.json
  ↓
Smartphone app generation UI
```

## Current decision

Do not integrate this project into the current PR.

Do not copy code before runtime validation.

Use it as a reference after the current minimum Analyzer + Flutter runtime path is proven.

## Why not now

```text
- Current PR is still waiting for runtime validation.
- Adding Playwright / Chromium would expand the test surface.
- Auto-install behavior may conflict with this project's conservative safety model.
- RunPod Network Volume 0GB / Terminate operation may make heavy dependency install costly each startup.
```

## Future evaluation checklist

After Claude runtime validation, evaluate:

```text
1. Should our Analyzer implement UI workflow conversion directly?
2. Should UI conversion be an optional adapter?
3. Can we avoid Playwright/Chromium for the MVP?
4. If Playwright is needed, can it be optional and user-approved?
5. Can we reimplement the idea without copying code?
6. If any code is copied or bundled, are MIT license and copyright preserved?
```

## Clean implementation principle

If this project inspires future work, implement from our own specification:

```text
- Our endpoint names.
- Our profile schema.
- Our safety rules.
- Our storage rules.
- Our runtime validation steps.
- Our mobile app requirements.
```

The external project should be treated as proof that the approach is possible, not as code to absorb into this PR.
