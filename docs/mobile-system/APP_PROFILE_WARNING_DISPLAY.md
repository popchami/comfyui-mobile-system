# App Profile Warning Display

## Purpose

This file records how the smartphone app displays profile-level warnings from `app_profile.json`.

The app must warn the user about missing models, missing custom nodes, and Analyzer warnings without attempting automatic installation or downloads.

## Current implementation status

```text
Implemented in:
mobile-app/flutter_mvp/lib/models/app_profile.dart
mobile-app/flutter_mvp/lib/screens/generate_screen.dart
```

## Parsed fields

`AppProfile` now parses:

```text
missing_nodes
missing_models
warnings
```

Supported shapes:

```json
"missing_nodes": [
  {
    "node_id": "12",
    "class_type": "SomeCustomNode"
  }
]
```

```json
"missing_models": [
  {
    "type": "checkpoint",
    "name": "example.safetensors",
    "path_hint": "models/checkpoints"
  }
]
```

```json
"warnings": [
  "Detected model names are listed as unverified references."
]
```

## Generate screen behavior

`GenerateScreen` now shows a `Profile warnings` card near the top of the generation screen when any of these are present:

```text
- missing model references
- missing custom node references
- general Analyzer warnings
```

Displayed examples:

```text
Missing checkpoint model: example.safetensors (models/checkpoints)
Missing custom node node 12: SomeCustomNode
Detected model names are listed as unverified references.
```

The card also reminds the user:

```text
No models or custom nodes are installed automatically.
```

## Safety rules

```text
- Do not auto-download missing models.
- Do not auto-install missing custom nodes.
- Do not modify workflow.json to remove missing nodes.
- Do not hide warnings just because generation might still work.
- Keep warnings visible before Submit /prompt.
```

## Deferred until RunPod + Android validation

```text
- Verify warnings with real exported profiles.
- Compare missing model names against /models/checkpoints.
- Compare missing node class_type against /object_info.
- Add severity levels such as info/warning/blocking.
- Add links or local instructions for where to place models.
```

## Runtime validation checklist

During RunPod + Android validation, confirm:

```text
1. Profile warnings card appears when app_profile has warnings.
2. Missing models are readable.
3. Missing custom nodes are readable.
4. Warnings do not trigger automatic download or install.
5. Warnings appear before Submit /prompt.
6. Profiles with no warnings do not show an empty warning card.
```
