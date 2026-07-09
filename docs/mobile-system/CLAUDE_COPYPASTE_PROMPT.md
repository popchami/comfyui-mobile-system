# Claude Copy-Paste Prompt

Use this prompt when handing PR #1 to Claude or another runtime reviewer again.

Claude already completed the first architecture alignment review and a limited CPU-only runtime validation pass. The next handoff is no longer a first review; it is for the remaining RunPod GPU + Android validation.

```text
Repository:
https://github.com/popchami/comfyui-mobile-system

PR:
#1 Add ComfyUI mobile system architecture and MVP scaffold

Branch:
docs/mobile-system-spec

Important:
Review the PR branch, not only main.
This PR is intentionally Draft.
Do not merge it yet.
Do not install ComfyUI on the smartphone as the product direction.
The product direction remains: ComfyUI runs on RunPod, Android app connects to it.

Current status:
- Architecture alignment review: complete
- Limited CPU-only runtime validation: complete
- OUTPUT_NODE blocker: fixed
- WEB_DIRECTORY cleanup: committed
- RunPod GPU validation: not complete
- Android device/emulator validation: not complete

Start with these current source-of-truth files:
1. docs/mobile-system/HANDOFF.md
2. docs/mobile-system/RUNTIME_VALIDATION_RESULT.md
3. docs/mobile-system/BLOCKERS_AFTER_CLAUDE.md
4. docs/mobile-system/NEXT_PHASE_PLAN.md

Then read supporting decision files if needed:
5. docs/mobile-system/PROJECT_DIRECTION_GUARDRAILS.md
6. docs/mobile-system/PRE_IMPLEMENTATION_ALIGNMENT_DECISIONS.md
7. docs/mobile-system/EXISTING_PLATFORMS_REVIEW.md
8. docs/mobile-system/COMFY_PORTAL_ENDPOINT_REFERENCE_REVIEW.md
9. docs/mobile-system/TEST_PLAN.md
10. mobile-app/flutter_mvp/RUN_CHECKLIST.md

Current edited decision remains valid:
- Do not discard the current system.
- Do change the implementation strategy.
- Use official ComfyUI APIs wherever possible.
- Keep custom code focused on the missing mobile profile layer.
- Move /object_info and /models earlier than originally planned, but do not fully implement them before real validation unless they are blockers.
- Keep UI workflow conversion optional for now.
- Use comfy-portal-endpoint as a reference only, not as a dependency or identity.

Important fixes already included:
- analyzer/ComfyUI-Mobile-Analyzer/nodes.py has OUTPUT_NODE = True.
- analyzer/ComfyUI-Mobile-Analyzer/__init__.py no longer declares unused WEB_DIRECTORY = "web".

Next validation goal:
RunPod GPU + Android real-device validation.

RunPod checks:
1. Start RunPod Pod with ComfyUI.
2. Place ComfyUI-Mobile-Analyzer under ComfyUI/custom_nodes/.
3. Start or restart ComfyUI.
4. Confirm no import errors.
5. Confirm Mobile Profile Exporter appears.
6. Export a profile zip.
7. Confirm zip includes workflow.json and app_profile.json.
8. Confirm GET /mobile_analyzer/profiles works.
9. Confirm GET /mobile_analyzer/profiles/{id}/download works.
10. Confirm real image generation with an already-installed checkpoint.
11. Confirm /prompt -> /ws -> /history -> /view works.

Android checks:
1. Create a real Flutter Android project shell if platform folders are missing.
2. Copy mobile-app/flutter_mvp/lib/ into it.
3. Copy mobile-app/flutter_mvp/pubspec.yaml into it.
4. Add Android INTERNET permission:
   <uses-permission android:name="android.permission.INTERNET" />
5. Run flutter pub get.
6. Run flutter analyze.
7. Run on Android device or emulator.
8. Enter the current RunPod ComfyUI URL.
9. Confirm /system_stats connection.
10. Download profile zip.
11. Save/open local profile.
12. Patch only patch_targets.
13. Submit generation.
14. Display at least one generated image.

Important rules:
- Do not merge the PR yet.
- Do not auto-install custom nodes.
- Do not auto-download models.
- Do not turn the app into a full ComfyUI workflow editor.
- Do not add Playwright/Chromium as a required MVP dependency.
- Do not add Google Drive sync.
- Do not add payment/monetization.
- Patch only fields listed in app_profile.json.patch_targets.
- Preserve unknown workflow nodes.
- Patch a generation copy of the workflow, not the saved original.
- Prefer official ComfyUI APIs over custom reimplementation where they already solve the problem.

If anything fails:
- Fix only the minimum blocker.
- Document what failed, what changed, and what remains unverified.
- Update docs/mobile-system/HANDOFF.md.
- Keep the PR Draft until RunPod GPU validation and Android validation both pass.
```
