# Claude Copy-Paste Prompt

Use this prompt when handing PR #1 to Claude for runtime validation.

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
Review the PR, run install/runtime checks, fix only blocking errors, and confirm whether it is install-ready.
This is not final product completion.

Read these files first, in this order:
1. docs/mobile-system/PRE_CLAUDE_STATUS.md
2. docs/mobile-system/PRIORITY_CONFLICT_REVIEW.md
3. docs/mobile-system/CLAUDE_FINAL_REVIEW_AND_INSTALL.md
4. docs/mobile-system/STATIC_REVIEW_NOTES.md

Current intended scope:
- ComfyUI-Mobile-Analyzer can be installed into ComfyUI/custom_nodes.
- Mobile Profile Exporter appears in ComfyUI.
- A minimal API workflow can be exported as a profile zip.
- The profile zip contains workflow.json and app_profile.json.
- /mobile_analyzer/profiles returns profile metadata.
- /mobile_analyzer/profiles/{id}/download downloads the zip.
- Flutter Android MVP can download/save/open a profile.
- Flutter Android MVP can patch only patch_targets.
- Flutter Android MVP can submit /prompt, poll /history, and display /view images.

Important rules:
- Do not merge the PR yet.
- Do not auto-install custom nodes.
- Do not auto-download models.
- Do not turn the app into a full ComfyUI workflow editor.
- Do not prioritize future TODOs until the install/runtime path is confirmed.
- Patch only fields listed in app_profile.json.patch_targets.
- Preserve unknown workflow nodes.
- Patch a generation copy of the workflow, not the saved original.

Runtime pass condition:
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
