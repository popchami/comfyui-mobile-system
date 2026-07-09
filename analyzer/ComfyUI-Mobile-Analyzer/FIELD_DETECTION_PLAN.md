# Field Detection Plan

## Purpose

Improve `MobileProfileExporter` so the generated `app_profile.json` has better simple UI fields.

## Current issue

The first skeleton detects every `CLIPTextEncode` as a generic prompt.

That is not enough because common workflows have:

- positive prompt
- negative prompt
- sampler settings
- latent size settings
- batch size
- image input

## Target MVP detection

### KSampler

Detect and expose:

- seed
- steps
- cfg
- sampler_name
- scheduler
- denoise

### CLIPTextEncode

Use the first KSampler connections:

- KSampler `positive` input points to Prompt
- KSampler `negative` input points to Negative Prompt

If a CLIPTextEncode node is not connected to those inputs, put it in expert or use a unique prompt field id.

### EmptyLatentImage

If connected to KSampler `latent_image`, expose:

- width
- height
- batch_size as batch

### LoadImage

Expose as image input:

- image

Image upload handling can remain later. The field should exist in the profile first.

### Model loaders

Detect model name strings and report them as unverified model references.

Initial model references:

- CheckpointLoaderSimple.ckpt_name -> checkpoint
- UNETLoader.unet_name -> unet
- VAELoader.vae_name -> vae
- LoraLoader.lora_name -> lora
- ControlNetLoader.control_net_name -> controlnet
- UpscaleModelLoader.model_name -> upscale_model

For now, these are detected names, not confirmed missing files.

## Compatibility status

Until real ComfyUI model file checking is implemented, use:

```text
partial
```

and add a warning:

```text
Model names were detected but not verified. Confirm files exist in ComfyUI models folders.
```

## Important rule

Do not delete unknown nodes.

Unknown nodes stay in `workflow.json` and should appear in expert or hidden depending on whether they have editable values.
