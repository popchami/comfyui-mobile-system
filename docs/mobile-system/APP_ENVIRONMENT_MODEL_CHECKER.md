# App Environment Model Checker

## Purpose

This file records the read-only service that checks whether the connected ComfyUI environment appears to contain the missing nodes and missing models reported by `app_profile.json`.

This is a read-only check. It must not download models, install custom nodes, or modify workflows.

## Current implementation status

```text
Implemented in:
mobile-app/flutter_mvp/lib/services/environment_model_checker.dart
```

## Related files

```text
mobile-app/flutter_mvp/lib/services/comfy_api_client.dart
mobile-app/flutter_mvp/lib/services/model_folder_resolver.dart
mobile-app/flutter_mvp/lib/models/app_profile.dart
```

## What it checks

The checker reads:

```text
GET /object_info
GET /models/{folder}
```

It compares:

```text
missing_nodes[].class_type
  against /object_info keys

missing_models[].name
  against /models/{resolved_folder}
```

## Model folder resolution

`EnvironmentModelChecker` uses `ModelFolderResolver` to group missing models by folder.

Examples:

```text
checkpoint -> checkpoints
lora       -> loras
vae        -> vae
controlnet -> controlnet
upscale    -> upscale_models
```

If `path_hint` contains a folder after `models/`, that folder is preferred.

Example:

```text
path_hint: models/loras
folder: loras
```

## Result object

The service returns `EnvironmentModelCheckResult` with:

```text
objectNodeTypeCount
foldersChecked
foldersUnavailable
foundNodeCount
totalMissingNodeCount
foundModelCount
totalCheckableModelCount
uncheckableModelCount
```

It also provides:

```text
toDisplayText()
```

for a compact mobile-readable summary.

## Example display text

```text
Environment check: node types 321.
Custom nodes found 1 / 2; still missing 1.
Models found 2 / 3; still missing 1.
Folders checked: checkpoints 4, loras 12.
Folders unavailable: vae.
No models or custom nodes were installed automatically.
```

## Safety rules

```text
- Read-only only.
- Do not download missing models.
- Do not install missing custom nodes.
- Do not modify workflow.json.
- Do not block the whole app if one /models/{folder} endpoint is unavailable.
- Do not assume every ComfyUI version supports every model folder route.
```

## Current UI integration note

`GenerateScreen` already has a basic read-only `Check environment` button.

The next cleanup step is to replace the inline checkpoint-only logic in `GenerateScreen` with `EnvironmentModelChecker`, so the button can check multiple model folders without making `GenerateScreen` larger.

## Runtime validation checklist

During RunPod + Android validation, confirm:

```text
1. /object_info node type comparison works.
2. /models/checkpoints check works.
3. /models/loras check works if supported.
4. /models/vae check works if supported.
5. Unsupported /models/{folder} routes do not crash the app.
6. Display text is readable on Android.
7. No automatic install or download occurs.
```
