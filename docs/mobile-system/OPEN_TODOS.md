# Open TODOs

## Purpose

This file records important design and implementation items that must not be lost while the mobile workflow system is still evolving.

These are not final decisions yet. They are items that need specification, review, and implementation planning.

## Timing rule

These TODOs are **post-install-validation work**.

Do not start these items until the PR passes the runtime checks described in:

```text
docs/mobile-system/CLAUDE_FINAL_REVIEW_AND_INSTALL.md
docs/mobile-system/PRE_CLAUDE_STATUS.md
```

Current rule:

```text
Before install validation: fix only blockers, docs, and shape mismatches.
After install validation: revisit and reprioritize this file.
```

## Do not mix with current install validation

The following items are important, but they should not block first install validation:

```text
- workflow node color matching
- production file storage
- re-run polish beyond MVP proof
- bypass handling
- subgraph handling
- advanced node handling
```

## TODO 1: Match app node colors to workflow node colors

When a workflow node has a color in ComfyUI, the app-side representation of that node should use the same or equivalent color.

Goal:

- Make the app view feel connected to the original ComfyUI workflow.
- Help users recognize node groups and node roles quickly.
- Preserve visual meaning from the original workflow where possible.

Needs design:

- Where node color is stored in UI-format workflow JSON.
- How API-format workflows represent or lose this color information.
- How `app_profile.json` should carry node color metadata.
- Fallback colors when node color is missing.

Reason to wait:

```text
API workflow may not contain color metadata. This should wait until UI workflow metadata import/conversion is designed.
```

Possible profile addition:

```json
{
  "node_id": "10",
  "class_type": "KSampler",
  "color": "#223344",
  "bgcolor": "#334455"
}
```

## TODO 2: Save and load analyzed workflows on the app side

After analysis, the app should save the imported/analyzed workflow locally and load it later.

Goal:

- User does not need to download the same profile every time.
- Imported profiles remain available offline on the phone.
- Saved profiles can be reopened from Local Profiles.

Current MVP status:

- Flutter MVP stores local profiles using `LocalProfileStore` and `shared_preferences`.
- This is acceptable for initial testing.

Needs design:

- Whether production storage should move from `shared_preferences` to file-based storage.
- How to store large workflow JSON safely.
- How to store app_profile, workflow, preview image, source_info, and generated history.
- How profile version updates should work.

Reason to wait:

```text
Changing storage before runtime validation can introduce Android path/permission issues. First prove MVP save/load works.
```

## TODO 3: Re-run generation after loading a saved workflow

After a saved profile/workflow is loaded, the app should be able to generate again.

Goal:

- User can reopen a saved workflow and press generate again.
- The app should patch only allowed fields and submit the workflow to ComfyUI.
- Re-run should support changing prompt, seed, steps, image input, and other simple fields.

Current MVP status:

- Flutter MVP can open a saved LocalProfile.
- GenerateScreen can patch workflow, submit `/prompt`, listen to `/ws`, read `/history`, and display `/view` images.

Needs verification:

- Runtime test with real ComfyUI.
- Confirm saved workflows stay valid after ComfyUI restarts.
- Confirm uploaded image names remain valid or are re-uploaded when needed.

Reason to wait:

```text
MVP already attempts re-run behavior. Polish and edge cases should wait until the first runtime proof succeeds.
```

## TODO 4: Handle bypassed nodes that are not loaded/active in the workflow

Some workflow nodes may be bypassed or not active in the current workflow path.

Question:

- If the app needs a bypassed node for a feature, should it temporarily un-bypass that node, generate, then return it to bypassed state?

Goal:

- Keep the original workflow state safe.
- Allow app-side feature toggles that activate optional workflow branches.
- Avoid permanently changing the user's workflow structure.

Needs design:

- How bypass state is represented in ComfyUI UI workflow JSON.
- Whether API workflow contains bypass information or if it is lost during conversion.
- How `app_profile.json` should represent optional/bypassed branches.
- Whether toggles should be modeled as patch_targets.
- How to restore bypass state after generation.

Important rule:

```text
The original stored workflow must not be permanently changed just because the app temporarily un-bypasses a node for generation.
```

Reason to wait:

```text
Bypass handling can accidentally mutate saved workflows. Do not implement it until copied-generation workflow tests exist.
```

Possible approach:

```text
saved workflow
  ↓ copy workflow for generation
  ↓ temporarily un-bypass needed node
  ↓ submit copied workflow
  ↓ discard copied workflow
  ↓ saved workflow remains unchanged
```

## TODO 5: Decide how to handle subgraphs

ComfyUI subgraphs may appear in workflows and need special handling.

Questions:

- Should Analyzer flatten subgraphs?
- Should the app treat subgraphs as one grouped unit?
- Should subgraph internals be visible only in expert mode?
- Can patch_targets safely point inside a subgraph?

Goal:

- Do not break workflows that use subgraphs.
- Keep the app simple for normal users.
- Preserve subgraph structure when possible.

Needs design:

- How ComfyUI represents subgraphs in workflow JSON.
- Whether API workflow export keeps subgraph boundaries.
- How `app_profile.json.nodes` should describe subgraph membership.
- How UI should display subgraph fields.
- How patch rules work inside subgraphs.

Reason to wait:

```text
Subgraph support may change node addressing and patch target rules. It should wait until flat workflow runtime validation passes.
```

Initial direction:

```text
MVP should preserve subgraphs and avoid editing subgraph structure.
Only expose safe patch_targets generated by Analyzer.
Subgraph internals should default to expert or hidden unless Analyzer marks a field as simple.
```

## Post-install suggested priority

After runtime validation passes, use this suggested order:

```text
1. Confirm saved workflow re-run behavior and image re-upload behavior.
2. Decide production storage: shared_preferences vs file-based profile storage.
3. Add model/node existence checks using runtime ComfyUI information.
4. Add UI workflow import/conversion if needed.
5. Add bypass handling for optional branches.
6. Add subgraph handling.
7. Add node color matching.
```

Reason:

```text
Re-run and storage are core app behavior. Runtime checks improve reliability. UI conversion expands compatible workflows. Bypass and subgraph support affect correctness. Node color improves usability but can come after functional safety.
```
