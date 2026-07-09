# Image Generation First: Model Branching Plan

Status: DRAFT - pending user review

## Relationship to existing docs

`IMAGE_MODEL_LOADER_STRATEGY_FIRST.md` already recorded the high-level decision to
solve image-generation model/loader strategy before video/audio/3D, and sketched a
`ModelFamilyAndLoaderStrategyDetector` concept with broad draft enums (including
`pony`, `hunyuan`, `video_model`, `audio_model`, etc.).

This document is a narrower, more concrete follow-up, scoped to the branching this
project actually needs right now (`sd15` / `sdxl` / `flux` / `unknown`), and it adds
one distinction the earlier doc did not make: **Flux.1 and Flux.2 Klein use
different loader node configurations**, confirmed against a live ComfyUI instance
(see "Verification method" below). It does not replace
`IMAGE_MODEL_LOADER_STRATEGY_FIRST.md`; treat both as complementary.

## Scope decision (unchanged from prior doc)

```text
Deepen image generation model/loader analysis first.
Video, audio, and 3D generation branching is deferred.
```

Reason: model loading is already highly branched within image generation alone
(checkpoint vs split-component loading, quantization, VAE bundling, LoRA family).
Solving this shakily and moving on to video/audio/3D would just repeat the same
mistake in more domains at once.

## Verification method (fact vs. assumption)

All node class names, input field names, and combo option values below marked
"confirmed" were read from a live `/object_info` response of a local ComfyUI
0.27.0 instance (CPU-only sandbox, `scratchpad/ComfyUI`) with a large set of
custom node packs installed (795 node types total). Anything not obtainable that
way is explicitly marked "unconfirmed" and must not be treated as fact until a
real ComfyUI environment with the relevant custom node pack confirms it.

## model_family branching

```text
sd15
sdxl
flux
unknown
```

Detection is based on the `type` combo value passed to CLIP loader nodes, and on
which loader node class is present, not on filename guessing.

### flux — critical sub-split: Flux.1 vs Flux.2 Klein

Per this project's own CLAUDE.md, "Flux.2" (without qualification) means Flux.2
Klein 9B, and it is architecturally distinct from the Flux.1 family. That
distinction is **confirmed at the node-input level**, not just conceptually:

| | Flux.1 (Dev/Schnell) | Flux.2 Klein 9B |
|---|---|---|
| Diffusion model loader | `UNETLoader` (confirmed) | `UNETLoader` (confirmed) — GGUF-quantized variant expected per project CLAUDE.md, **unconfirmed** in this session's environment (no GGUF-loader custom node installed there) |
| Text encoder loader | `DualCLIPLoader` (confirmed) | `CLIPLoader` (confirmed) |
| Text encoder `type` value | `"flux"` (confirmed combo option on `DualCLIPLoader.type`) | `"flux2"` (confirmed combo option on `CLIPLoader.type`) |
| VAE loader | `VAELoader` (confirmed) | `VAELoader` (confirmed) |

This means `class_type == "DualCLIPLoader" and type == "flux"` vs.
`class_type == "CLIPLoader" and type == "flux2"` is a reliable, node-input-level
signal to distinguish the two Flux generations — not a naming heuristic on the
workflow author's title/filename.

## loader_strategy branching

```text
checkpoint_single_file
diffusion_model_plus_text_encoders_plus_vae
gguf_quantized
fp8_checkpoint
fp8_diffusion_model
merged_checkpoint
custom_loader
unknown
```

| loader_strategy | Confirmed node signal |
|---|---|
| `checkpoint_single_file` | `class_type == "CheckpointLoaderSimple"` (confirmed; `RETURN_TYPES = (MODEL, CLIP, VAE)`, single `ckpt_name` input) |
| `diffusion_model_plus_text_encoders_plus_vae` | `class_type == "UNETLoader"` (confirmed, `RETURN_TYPES = (MODEL,)`) feeding a sampler, alongside a CLIP loader (`DualCLIPLoader`/`CLIPLoader`/`TripleCLIPLoader`/`QuadrupleCLIPLoader`, all confirmed to exist) and a `VAELoader` (confirmed) |
| `fp8_diffusion_model` | `class_type == "UNETLoader"` whose `weight_dtype` input value starts with `"fp8"` — confirmed real combo options: `["default", "fp8_e4m3fn", "fp8_e4m3fn_fast", "fp8_e5m2"]` |
| `gguf_quantized` | **Decided (user, 2026-07-10): implementation deferred.** Would require a GGUF-loader node class (e.g. the ComfyUI-GGUF custom pack). No such node was present in this session's `/object_info` dump, so its real class name is unconfirmed. Do not implement detection against an assumed/unconfirmed GGUF loader class name — wait until a RunPod environment with ComfyUI-GGUF installed can confirm the real class name via `/object_info`, then implement. |
| `fp8_checkpoint` | **Decided (user, 2026-07-10):判定保留・RunPod実機確認待ち (detection deferred, pending RunPod hardware verification).** `CheckpointLoaderSimple` has only a `ckpt_name` string input — there is no confirmed node-level field indicating fp8 vs bf16 quantization for a merged single-file checkpoint. Filename-substring guessing would repeat the exact class of bug just fixed in `infer_output_type()` and is not proposed here. This stays `unknown` until a RunPod environment can confirm whether a reliable node-level or model-registry signal exists. |
| `merged_checkpoint` | Same node signal as `checkpoint_single_file` (`CheckpointLoaderSimple`); the distinction from a "regular" checkpoint is semantic/model-registry information, not something derivable from the workflow graph alone. Likely folds into `checkpoint_single_file` unless a reliable graph-level signal is found. |
| `custom_loader` | Any loader-shaped node (an `expert_unknown`-classified node whose output includes `MODEL` and/or `CLIP` and/or `VAE`) that is not one of the above confirmed classes |
| `unknown` | No loader node found, or the loader class is not in the confirmed set above |

## vae_strategy branching

```text
bundled
external_required
external_optional
unknown
```

| vae_strategy | Confirmed node signal |
|---|---|
| `bundled` | `CheckpointLoaderSimple` output already includes `VAE` (confirmed `RETURN_TYPES` includes `VAE`) and no separate `VAELoader` feeds the sampler's VAE input |
| `external_required` | `UNETLoader`-based loading (Flux.1/Flux.2 pattern): `RETURN_TYPES = (MODEL,)` only, no VAE — a `VAELoader` (confirmed node) is structurally required for `VAEDecode` to have a VAE input |
| `external_optional` | `CheckpointLoaderSimple` bundled VAE output present, but a separate `VAELoader` output is connected instead (workflow author chose to override the bundled VAE) |
| `unknown` | Neither pattern detected with confidence |

## lora_family branching

```text
sd15
sdxl
flux
unknown
```

Important constraint confirmed via `/object_info`: `LoraLoader` and
`LoraLoaderModelOnly` are generic nodes (confirmed inputs:
`model, clip, lora_name, strength_model, strength_clip` / `model, lora_name,
strength_model`) — the node class itself carries **no family information**.
`lora_family` cannot be read off the LoRA loader node in isolation; it must be
inferred by tracing which `model_family`-classified loader feeds the `model`
input the LoRA loader is chained from. This is a graph-traversal requirement, not
a per-node lookup, and should be documented as such in the detector design so it
is not implemented as a naive per-node classifier.

## Model Family / Loader Strategy Detector — design sketch

Extends the existing `nodes_v2_debug.py` / `nodes_v2_validated_debug.py` debug
exporters only. **Does not change the production `app_profile.json` (v1)
contract.**

- Add a new pure function, e.g. `detect_model_strategy(workflow, runtime_node_defs)`,
  alongside the existing `detect_outputs` / `detect_runtime_requirements` functions
  in `nodes_v2_debug.py`.
- **Decided (user, 2026-07-10): `model_strategy` is a new top-level key** in the
  v2-debug/v2-validated-debug profile, a sibling of `runtime_requirements`,
  `capabilities`, `outputs`, and `warnings` — it is not nested inside
  `runtime_requirements`.
- Follows the same safety posture already established in this codebase:
  read-only analysis, no patch_targets are generated from this, and any
  uncertain classification must surface as a `warnings` entry
  (`type: "model_strategy_uncertain"` or similar) rather than a silent guess.
- Example shape (illustrative, not final) — `model_strategy` shown as a
  top-level sibling of the existing v2 profile keys:

```json
{
  "runtime_requirements": { "...": "unchanged, existing key" },
  "capabilities": { "...": "unchanged, existing key" },
  "outputs": [ "...unchanged, existing key" ],
  "warnings": [ "...unchanged, existing key" ],
  "model_strategy": {
    "model_family": "flux",
    "flux_generation": "flux2_klein",
    "loader_strategy": "diffusion_model_plus_text_encoders_plus_vae",
    "vae_strategy": "external_required",
    "lora_family": "flux",
    "confidence": "medium",
    "evidence": [
      "CLIPLoader.type == 'flux2'",
      "UNETLoader present, no bundled VAE output used"
    ],
    "warnings": []
  }
}
```

- Follows the LoRA constraint above: `lora_family` is set only after tracing the
  LoRA loader's `model` connection back to a classified `model_family` loader,
  not read from the LoRA node itself.

## Hard constraint (per project rule)

Every node class name and input/combo value in this document is either:
(a) marked "confirmed", meaning it was read directly from a live `/object_info`
response in this session, or
(b) marked "unconfirmed", meaning it is expected per this project's own CLAUDE.md
or general ComfyUI ecosystem knowledge, but was not verified against this
session's environment (typically because the relevant custom node pack was not
installed there).

No node class name in this document is invented. Where a signal is genuinely
unresolved (`fp8_checkpoint`, `gguf_quantized`), that is stated plainly instead of
guessing a plausible-sounding node name.

## Decisions (user, 2026-07-10)

```text
1. model_strategy placement: new top-level key in the v2 profile schema,
   a sibling of runtime_requirements/capabilities/outputs/warnings — not
   nested inside runtime_requirements.
2. fp8_checkpoint detection: stays "unknown" for now. Implementation is
   deferred until a RunPod environment can confirm whether a reliable
   node-level or model-registry signal exists for this case.
3. gguf_quantized detection: implementation deferred. Do not implement
   against an assumed/unconfirmed GGUF loader class name. Wait for a
   RunPod environment with ComfyUI-GGUF installed to confirm the real
   node class name via /object_info first.
```

These three items are therefore explicitly out of scope for the first
implementation pass of `detect_model_strategy()`; that first pass should cover
`model_family` (including the Flux.1/Flux.2 Klein split), `checkpoint_single_file`,
`diffusion_model_plus_text_encoders_plus_vae`, `fp8_diffusion_model`,
`vae_strategy`, and `lora_family` only.
