# App Model Folder Resolver

## Purpose

This file records the app-side preparation for checking model folders beyond checkpoints.

This is read-only preparation for environment checks. It must not download models, install models, or modify workflows.

## Current implementation status

```text
Implemented in:
mobile-app/flutter_mvp/lib/services/model_folder_resolver.dart
```

## Why this exists

`app_profile.json` may report missing models with different types and path hints:

```text
checkpoint
lora
vae
clip
controlnet
upscale
unet / diffusion model
embedding
```

The app needs a small safe mapper so it can decide which official ComfyUI model folder endpoint to check:

```text
GET /models/{folder}
```

## Current mapping

```text
checkpoint / ckpt        -> checkpoints
lora                     -> loras
vae                      -> vae
clip                     -> clip
controlnet / control_net -> controlnet
upscale                  -> upscale_models
unet / diffusion_model   -> diffusion_models
embedding / embeddings   -> embeddings
```

## path_hint support

If Analyzer provides a path hint such as:

```text
models/checkpoints
models/loras
models/vae
```

then the resolver prefers the folder after `models/`.

Example:

```text
path_hint: models/loras
resolved folder: loras
```

## Safety rules

```text
- Read-only only.
- Do not download missing models.
- Do not install missing models.
- Do not change workflow.json.
- Do not assume every ComfyUI version supports every /models/{folder} endpoint.
- If a model folder endpoint fails, show that the folder check is unavailable rather than blocking the whole app.
```

## Current limitation

The resolver is prepared, but broad multi-folder model checking should be validated carefully on RunPod/Android before being treated as final behavior.

Current GenerateScreen environment check already checks:

```text
/object_info
/models/checkpoints
```

Next safe integration step:

```text
Use ModelFolderResolver to group missing_models by folder and check each folder with /models/{folder}, while tolerating unsupported folders.
```

## Runtime validation checklist

During RunPod + Android validation, confirm:

```text
1. checkpoints folder check still works.
2. loras folder check works if ComfyUI supports /models/loras.
3. vae folder check works if ComfyUI supports /models/vae.
4. unsupported model folders do not crash the app.
5. no model download is triggered.
6. no workflow mutation happens.
```
