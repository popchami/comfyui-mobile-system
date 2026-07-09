# Claude Copy-Paste Prompt

Use this prompt when handing PR #1 to Claude.

The handoff is no longer only runtime validation.

Because this is still before implementation hardens, Claude should first review whether the current design should be adjusted based on official ComfyUI/RunPod capabilities and the external reference review.

```text
Repository:
https://github.com/popchami/comfyui-mobile-system

PR:
#1 Add ComfyUI mobile system architecture and MVP scaffold

Branch:
docs/mobile-system-spec

This PR is intentionally Draft and labeled runtime-validation-pending.
Do not merge it yet.

Goal:
First perform a pre-runtime architecture inventory and official API alignment review.
Then run install/runtime checks only after confirming the current direction still makes sense.
Fix only blocking errors or small alignment issues.
This is not final product completion.

Read these files first, in this order:
1. docs/mobile-system/PRE_CLAUDE_STATUS.md
2. docs/mobile-system/PROJECT_DIRECTION_GUARDRAILS.md
3. docs/mobile-system/SYSTEM_INVENTORY_BEFORE_CLAUDE.md
4. docs/mobile-system/EXISTING_PLATFORMS_REVIEW.md
5. docs/mobile-system/COMFY_PORTAL_ENDPOINT_REFERENCE_REVIEW.md
6. docs/mobile-system/PRIORITY_CONFLICT_REVIEW.md
7. docs/mobile-system/CLAUDE_FINAL_REVIEW_AND_INSTALL.md
8. docs/mobile-system/STATIC_REVIEW_NOTES.md

Important context:
- The project should remain mobile-first.
- This is not a full ComfyUI replacement.
- This is not a generic workflow portal.
- This is not a ComfyUI Manager replacement.
- This should use official ComfyUI APIs where possible.
- Custom code should focus on the missing mobile profile layer.

Architecture review questions to answer before runtime validation:
1. Which current custom logic duplicates official ComfyUI APIs?
2. Should /object_info be moved earlier to avoid manual field-type guessing?
3. Should /models and /models/{folder} be moved earlier for missing model checks?
4. Which /mobile_analyzer custom routes are still necessary?
5. Should UI workflow to API workflow conversion remain optional for now?
6. Does comfy-portal-endpoint provide a useful reference without shifting this project into a workflow portal?
7. What is the minimum blocker-free path to validate the current MVP?

Current intended MVP scope:
- ComfyUI-Mobile-Analyzer can be installed into ComfyUI/custom_nodes.
- Mobile Profile Exporter appears in ComfyUI.
- A minimal API workflow can be exported as a profile zip.
- The profile zip contains workflow.json and app_profile.json.
- /mobile_analyzer/profiles returns profile metadata.
- /mobile_analyzer/profiles/{id}/download downloads the zip.
- Flutter Android MVP can download/save/open a profile.
- Flutter Android MVP can patch only patch_targets.
- Flutter Android MVP can submit /prompt, monitor /ws, read /history, and display /view images.

Official ComfyUI APIs that should be treated as source-of-truth where applicable:
- /prompt
- /ws
- /history/{prompt_id}
- /view
- /upload/image
- /upload/mask
- /system_stats
- /object_info
- /object_info/{node_class}
- /models
- /models/{folder}

External reference stance:
- comfy-portal-endpoint may be studied as a reference for UI workflow to API workflow conversion.
- Do not copy its code.
- Do not make Playwright/Chromium required for this MVP.
- Do not shift this project into a generic workflow management server.
- If inspired by it later, implement our own optional converter from our own requirements.

Important rules:
- Do not merge the PR yet.
- Do not auto-install custom nodes.
- Do not auto-download models.
- Do not turn the app into a full ComfyUI workflow editor.
- Do not prioritize future TODOs until architecture alignment and runtime path are confirmed.
- Patch only fields listed in app_profile.json.patch_targets.
- Preserve unknown workflow nodes.
- Patch a generation copy of the workflow, not the saved original.
- Prefer official ComfyUI APIs over custom reimplementation where they already solve the problem.

Runtime pass condition after architecture review:
1. ComfyUI starts with ComfyUI-Mobile-Analyzer installed.
2. Mobile Profile Exporter appears in ComfyUI.
3. Mobile Profile Exporter creates a zip under output/mobile_profiles.
4. Zip contains workflow.json and app_profile.json.
5. /mobile_analyzer/profiles returns profile metadata.
6. /mobile_analyzer/profiles/{id}/download downloads the zip.
7. Flutter MVP passes flutter pub get.
8. Flutter MVP passes flutter analyze or only has documented non-blocking warnings.
9. Flutter Android app can connect to ComfyUI.
10. Flutter Android app can download, save, open, patch, submit, and display at least one generated image.

If anything fails:
- Fix only the minimum blocker.
- Document what failed, what changed, and what remains unverified.
- Keep the PR Draft until all pass conditions are confirmed.
```
