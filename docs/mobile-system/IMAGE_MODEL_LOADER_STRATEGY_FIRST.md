# Image Model Loader Strategy First

## Purpose

This document records an important product and Analyzer direction.

The product owner pointed out that even within image generation, model loading is already highly branched and cannot be treated as a single generic model picker.

Examples:

```text
Flux regular model
Flux merged model
Flux quantized model
SDXL model
VAE bundled / not bundled
Flux LoRA
SDXL LoRA
LoRA loader node variants
custom model loader variants
```

This means the Analyzer must reason about fine-grained model loader strategy, not only prompt and sampler fields.

## Core decision

```text
Do not try to solve every generation type at once.
Finish image generation model/loader strategy first.
```

Image generation alone has enough complexity.

Video, audio, text, 3D, and external API generation will likely have similar fine-grained branches later.

Therefore, the immediate focus should be:

```text
image generation
  -> model family
  -> loader strategy
  -> VAE strategy
  -> text encoder strategy
  -> LoRA strategy
  -> required files
  -> compatibility warnings
```

## Why this matters

Model selection appears early in the workflow.

If the Analyzer misunderstands the model/loader strategy, the rest of the workflow may still look editable but not actually be runnable.

For example:

```text
Prompt fields may be editable.
Sampler fields may be editable.
But the workflow still fails because the required model loader setup is wrong or missing files.
```

So model/loader strategy must be treated as a first-class analysis target.

## Problem examples

### Flux regular model

May require separated components:

```text
diffusion model / UNet
text encoder: t5xxl
text encoder: clip_l
VAE
```

Likely loader pattern:

```text
UNETLoader / Load Diffusion Model
DualCLIPLoader / text encoder loaders
VAELoader
```

### Flux checkpoint / merged model

May use checkpoint-style loading:

```text
CheckpointLoaderSimple / Load Checkpoint
```

Some components may be bundled or implied.

VAE may be bundled, external, optional, or unknown depending on the checkpoint and workflow.

### Flux quantized model

May require specialized loader nodes:

```text
GGUF loader
NF4 loader
FP8 loader
custom quantized model loader
```

The Analyzer must not assume the same loader as regular Flux.

### LoRA variants

LoRA is not a single universal case.

Possible variants:

```text
SD1.5 LoRA
SDXL LoRA
Flux LoRA
Control LoRA
Motion LoRA
LoRA stack nodes
Power LoRA loader nodes
custom LoRA selector nodes
```

A simple `LoraLoader` detector is not enough.

## Required new Analyzer concept

Add a detector layer:

```text
ModelFamilyAndLoaderStrategyDetector
```

It should classify:

```text
model_family
loader_strategy
vae_strategy
text_encoder_strategy
lora_strategy
required_files
missing_or_unverified_requirements
compatibility_warnings
```

## Draft classification fields

### model_family

```text
sd15
sdxl
flux
pony
hunyuan
video_model
audio_model
unknown
```

### loader_strategy

```text
checkpoint_single_file
diffusion_model_plus_text_encoders_plus_vae
gguf_quantized
nf4_quantized
fp8_checkpoint
fp8_diffusion_model
merged_checkpoint
custom_loader
unknown
```

### vae_strategy

```text
bundled
external_required
external_optional
not_used
unknown
```

### text_encoder_strategy

```text
bundled
clip_only
dual_clip
t5xxl_plus_clip_l
external_required
unknown
```

### lora_strategy

```text
none
standard_lora
sdxl_lora
flux_lora
control_lora
motion_lora
lora_stack
custom_lora_loader
unknown
```

## Required app display

The smartphone app should eventually show model requirements clearly.

Examples:

```text
This workflow appears to use Flux regular loading.
Required files:
- diffusion model
- t5xxl text encoder
- clip_l text encoder
- VAE
```

```text
This workflow appears to use Flux checkpoint loading.
Required files:
- checkpoint
VAE / CLIP may be bundled or workflow-dependent.
```

```text
This workflow appears to use a quantized Flux loader.
Required files:
- quantized model file
- required custom loader node
- text encoder files if not bundled
- VAE if not bundled
```

## Runtime requirements implication

`runtime_requirements` must become more detailed than a flat model list.

It should include structured information such as:

```json
{
  "model_strategy": {
    "model_family": "flux",
    "loader_strategy": "diffusion_model_plus_text_encoders_plus_vae",
    "vae_strategy": "external_required",
    "text_encoder_strategy": "t5xxl_plus_clip_l",
    "lora_strategy": "flux_lora",
    "confidence": "medium",
    "warnings": []
  },
  "required_files": [
    {"type": "diffusion_model", "name": "...", "status": "unverified"},
    {"type": "text_encoder", "name": "t5xxl...", "status": "unverified"},
    {"type": "text_encoder", "name": "clip_l...", "status": "unverified"},
    {"type": "vae", "name": "...", "status": "unverified"}
  ]
}
```

## Image-first scope

The next deep Analyzer work should focus on image generation only.

Do not attempt to fully solve all generation types at the same time.

Immediate image-first scope:

```text
CheckpointLoaderSimple
UNETLoader / diffusion model loader variants
DualCLIPLoader / CLIP loaders / T5 loaders
VAELoader
Flux loader patterns
SDXL checkpoint patterns
GGUF / NF4 / FP8 quantized loader indicators
LoRA loader variants
model file references
VAE required vs bundled vs unknown
missing model warnings
LoRA compatibility warnings
```

## Later generation types

Video, audio, text, 3D, and external API generation should remain structurally anticipated, but not fully implemented before image model strategy is solid.

Reason:

```text
Every generation type likely has its own model family / loader strategy complexity.
```

Examples:

```text
video: motion model, video model, frame model, image-to-video loaders, motion LoRA
 audio: TTS model, voice model, vocoder, speaker embedding, audio encoder
 text/LLM: model provider, local/API, tokenizer, context limit, system prompt, credentials
3D: mesh model, texture model, multiview image model, external provider, file format
```

These should be handled after the image-generation loader strategy is proven.

## Guardrail

```text
Do not assume prompt/sampler extraction is enough.
Do not assume Flux has one loader pattern.
Do not assume LoRA has one node type.
Do not assume VAE is always bundled.
Do not assume checkpoint loading means every requirement is satisfied.
Do not hide model/loader uncertainty from the user.
```

## Next implementation target

```text
Add ModelFamilyAndLoaderStrategyDetector for image generation.
```

Start with detection and warnings only.

Do not yet make the app auto-fix missing files.

Do not auto-download models.

Do not auto-install custom nodes.
