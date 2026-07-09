# Test Plan

## Purpose

This document defines the first checks needed before merging the mobile system design and skeleton into `main`.

The goal is not full production validation. The goal is to confirm that the architecture can work end-to-end.

## Phase 1: Documentation review

Reviewer: Claude or another AI/code reviewer.

Check:

- `app_profile.json` has enough information for the mobile app.
- `patch_targets` are safe and clear.
- UI visibility levels are practical.
- MVP scope is not too large.
- Analyzer and mobile app responsibilities are separated correctly.
- Unknown nodes are preserved.
- Missing requirements are reported, not auto-installed.

Pass condition:

- Reviewer confirms the design is understandable and implementable.
- Any blocking issues are fixed in the PR branch.

## Phase 2: Static code review

Check analyzer skeleton files:

- `__init__.py`
- `nodes.py`
- `server.py`

Check:

- No auto-install behavior.
- No model download behavior.
- No arbitrary shell execution.
- Output path is limited to `output/mobile_profiles/`.
- Zip contains `workflow.json` and `app_profile.json`.
- Unknown nodes are not removed.
- Generated profile uses `schema_version`.
- Positive and negative prompt detection uses KSampler connections.
- Width, height, and batch are detected from EmptyLatentImage.
- LoadImage creates an image field.
- Detected model names are reported as unverified references.

Pass condition:

- No obvious unsafe behavior.
- No obvious syntax or import issue.

## Phase 3: ComfyUI runtime smoke test

Install draft custom node folder into ComfyUI custom_nodes.

Expected location:

```text
ComfyUI/custom_nodes/ComfyUI-Mobile-Analyzer/
```

Check:

- ComfyUI starts.
- `MobileProfileExporter` appears in node menu.
- Node accepts pasted API-format workflow JSON.
- Node creates a zip under `output/mobile_profiles/`.
- Zip can be opened.
- Zip contains `workflow.json`.
- Zip contains `app_profile.json`.
- `app_profile.json.ui.simple` contains prompt.
- `app_profile.json.ui.simple` contains negative when workflow has KSampler negative connection.
- `app_profile.json.ui.simple` contains seed / steps / cfg.
- `app_profile.json.ui.simple` contains width / height / batch when EmptyLatentImage exists.
- `app_profile.json.ui.simple` contains image field when LoadImage exists.

Pass condition:

- One valid zip is created without crashing ComfyUI.
- app_profile.json contains the expected simple fields.

## Phase 4: API smoke test

After a zip exists, check:

```text
GET /mobile_analyzer/profiles
GET /mobile_analyzer/profiles/{id}/download
```

Pass condition:

- Profile list returns at least one profile.
- Download endpoint returns the zip.

## Phase 5: Mobile app prototype test

Use `mobile-app/prototype/index.html`.

Check:

- Register ComfyUI URL.
- Fetch profile list.
- Download selected remote profile zip.
- Import local profile zip.
- Extract `app_profile.json` and `workflow.json` from zip.
- Render simple fields.
- Render image fields as file pickers.
- Upload selected image to `/upload/image`.
- Patch `LoadImage.image` with uploaded filename.
- Patch prompt / negative / seed / steps / cfg / width / height / batch.
- Submit patched workflow to `/prompt`.
- Poll `/history/{prompt_id}`.
- Display output image with `/view`.

Pass condition:

- One profile zip can be imported without manual JSON paste.
- One image can be generated from a profile imported through the new flow.
- If the workflow uses LoadImage, one selected smartphone image can be uploaded and used.

## Merge rule

Do not merge to `main` until at least documentation review and static code review are complete.

Runtime smoke test should be completed before treating the skeleton as usable.
