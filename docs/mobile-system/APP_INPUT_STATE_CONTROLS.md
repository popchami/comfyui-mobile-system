# App Input State Controls

## Purpose

This file records smartphone-app-side input state features that can be implemented safely before RunPod and Android runtime validation.

These features must not edit `workflow.json` directly. They only update UI field values, and the actual workflow update must still go through `app_profile.json.patch_targets`.

## Current implementation status

```text
Implemented in:
mobile-app/flutter_mvp/lib/screens/generate_screen.dart
```

Current implemented controls:

```text
- Restore previous text/number/select values per profile.
- Save current text/number/select values per profile before /prompt submission.
- Reset visible input fields to app_profile default values.
- Clear selected/uploaded image state when resetting fields.
- Detect seed fields from field_id / label / section / type.
- Keep last submitted seed in the current screen session.
- Reuse last seed with a Use last seed button.
- Set a Random seed value with a Random seed button.
```

## Profile-specific previous values

Previous values are stored with `shared_preferences` using a profile-specific key:

```text
profile_field_values_<profile_id>
```

Stored values are limited to non-image controller fields.

Reason:

```text
Image file paths and uploaded image names can become stale or invalid between app launches.
```

Restore behavior:

```text
1. Build controllers from app_profile defaults.
2. Read saved field values for this profile id.
3. If saved values are valid, apply them to matching controllers.
4. Ignore unknown saved fields.
5. Ignore broken saved JSON.
```

Save behavior:

```text
1. User submits generation.
2. Current controller values are saved before /prompt submission.
3. Workflow patching still happens through patch_targets.
```

## Reset to profile defaults

Reset behavior:

```text
- Set every controller field back to its app_profile default value.
- Clear selected local image files.
- Clear uploaded image filenames.
- Recalculate last seed from the reset field values.
```

Important:

```text
Reset does not edit workflow.json directly.
Reset only changes the UI field values.
```

## Seed controls

Seed fields are detected from:

```text
field_id
label
section
type
```

Current seed controls:

```text
Use last seed
  - Appears only after a last seed exists in the current screen session.
  - Restores the last submitted seed value into the seed field.

Random seed
  - Appears on detected seed fields.
  - Generates a non-negative random integer below 0x7fffffff.
  - Writes the value to the seed field only.
```

## Safety rules

```text
- Do not bypass patch_targets.
- Do not directly mutate rawWorkflowJson.
- Do not persist image file paths as reusable generation inputs yet.
- Do not assume every workflow has a seed field.
- Do not require a seed field for generation.
- Keep these controls optional and field-driven.
```

## Deferred until Android validation

```text
- Persist selected image references safely.
- Save generation history permanently.
- Persist last seed with richer metadata.
- Add clipboard copy for seed.
- Add profile-level input presets.
- Add per-section reset.
- Add undo/redo for field changes.
```

## Runtime validation checklist

During Android validation, confirm:

```text
1. Previous field values restore after reopening the same local profile.
2. Previous field values are isolated per profile id.
3. Submit saves current field values.
4. Reset to profile defaults restores default text/number values.
5. Reset clears selected image preview state.
6. Random seed updates only seed fields.
7. Use last seed restores the last submitted seed.
8. Generated workflow is still patched only through patch_targets.
```
