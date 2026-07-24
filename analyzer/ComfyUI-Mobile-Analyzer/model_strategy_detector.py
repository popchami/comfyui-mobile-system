"""model_family / loader_strategy / vae_strategy / lora_family detection.

Design reference: docs/mobile-system/IMAGE_GENERATION_FIRST_MODEL_BRANCHING_PLAN.md

Scope (per that draft's decided "first implementation pass"):
    model_family (including the Flux.1 / Flux.2 Klein split), checkpoint_single_file,
    diffusion_model_plus_text_encoders_plus_vae, fp8_diffusion_model, vae_strategy,
    lora_family.

Explicitly NOT implemented (deferred by user decision, see HANDOFF.md):
    fp8_checkpoint  - CheckpointLoaderSimple/CheckpointLoader have no confirmed
                      node-level dtype signal; would require filename/registry
                      guessing, which is not done here.
    gguf_quantized  - would require a GGUF-loader custom node class name that was
                      not present in this project's local /object_info
                      verification session. Not hardcoded until confirmed on a
                      real RunPod environment with ComfyUI-GGUF installed.

Every node class name and combo value used below was confirmed via a live
/object_info query against a local ComfyUI 0.27.0 instance during this
project's analysis sessions (see HANDOFF.md for dates). Where a signal could
not be confirmed, detection falls back to "unknown" instead of guessing.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple

from .nodes_v2_debug import is_connection

# Confirmed via /object_info: RETURN_TYPES = (MODEL, CLIP, VAE)
CHECKPOINT_LOADER_TYPES = {"CheckpointLoaderSimple", "CheckpointLoader"}

# Confirmed via /object_info: RETURN_TYPES = (MODEL,), inputs unet_name + weight_dtype
DIFFUSION_MODEL_LOADER_TYPES = {"UNETLoader"}

# Confirmed via /object_info: all RETURN_TYPES = (CLIP,)
CLIP_LOADER_TYPES = {"DualCLIPLoader", "CLIPLoader", "TripleCLIPLoader", "QuadrupleCLIPLoader"}

# Confirmed via /object_info: RETURN_TYPES = (VAE,), input vae_name
VAE_LOADER_TYPES = {"VAELoader"}

# Confirmed via /object_info
LORA_LOADER_TYPES = {"LoraLoader", "LoraLoaderModelOnly"}

# Confirmed via /object_info: SDXL-specific text encode nodes with a distinct
# signature (text_g/text_l/width/height/crop/target inputs) not shared with
# the generic CLIPTextEncode(text, clip) used by SD1.5/Flux workflows.
SDXL_MARKER_NODE_TYPES = {"CLIPTextEncodeSDXL", "CLIPTextEncodeSDXLRefiner"}

# Confirmed via /object_info: DualCLIPLoader.type combo includes "flux";
# CLIPLoader.type combo includes "flux2". These are the real, distinct values
# ComfyUI itself uses to tell Flux.1-style dual-encoder loading apart from
# Flux.2 Klein's single-CLIPLoader loading.
FLUX1_DUAL_CLIP_TYPE_VALUE = "flux"
FLUX2_CLIP_TYPE_VALUE = "flux2"

# Confirmed via /object_info: UNETLoader.weight_dtype combo options are
# ["default", "fp8_e4m3fn", "fp8_e4m3fn_fast", "fp8_e5m2"].
FP8_WEIGHT_DTYPE_PREFIX = "fp8"


def detect_model_strategy(workflow: Dict[str, Any], runtime_node_defs: Dict[str, Any]) -> Dict[str, Any]:
    reasons: List[str] = []
    node_id_to_class = _build_node_id_to_class(workflow)

    checkpoint_nodes = _nodes_of_class(workflow, CHECKPOINT_LOADER_TYPES)
    unet_nodes = _nodes_of_class(workflow, DIFFUSION_MODEL_LOADER_TYPES)
    clip_loader_nodes = _nodes_of_class(workflow, CLIP_LOADER_TYPES)
    vae_loader_nodes = _nodes_of_class(workflow, VAE_LOADER_TYPES)

    model_family, flux_generation = _detect_model_family(workflow, clip_loader_nodes, reasons)
    loader_strategy = _detect_loader_strategy(
        checkpoint_nodes=checkpoint_nodes,
        unet_nodes=unet_nodes,
        clip_loader_nodes=clip_loader_nodes,
        vae_loader_nodes=vae_loader_nodes,
        runtime_node_defs=runtime_node_defs,
        node_id_to_class=node_id_to_class,
        reasons=reasons,
    )
    vae_strategy = _detect_vae_strategy(workflow, loader_strategy, node_id_to_class, reasons)
    lora_family = _detect_lora_family(workflow, node_id_to_class, model_family, reasons)

    confidence = _decide_confidence(model_family, loader_strategy, vae_strategy)

    result: Dict[str, Any] = {
        "model_family": model_family,
        "loader_strategy": loader_strategy,
        "vae_strategy": vae_strategy,
        "lora_family": lora_family,
        "confidence": confidence,
        "reasons": reasons,
        "warnings": [],
    }
    if model_family == "flux":
        result["flux_generation"] = flux_generation
    return result


def _build_node_id_to_class(workflow: Dict[str, Any]) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    for node_id, node in workflow.items():
        if isinstance(node, dict) and node.get("class_type"):
            mapping[str(node_id)] = str(node["class_type"])
    return mapping


def _nodes_of_class(workflow: Dict[str, Any], class_types: Set[str]) -> List[Tuple[str, Dict[str, Any]]]:
    result: List[Tuple[str, Dict[str, Any]]] = []
    for node_id, node in workflow.items():
        if isinstance(node, dict) and str(node.get("class_type")) in class_types:
            result.append((str(node_id), node))
    return result


def _input_value(node: Dict[str, Any], input_name: str) -> Any:
    inputs = node.get("inputs", {})
    if not isinstance(inputs, dict):
        return None
    return inputs.get(input_name)


def _detect_model_family(
    workflow: Dict[str, Any],
    clip_loader_nodes: List[Tuple[str, Dict[str, Any]]],
    reasons: List[str],
) -> Tuple[str, Optional[str]]:
    for _, node in clip_loader_nodes:
        class_type = str(node.get("class_type"))
        type_value = _input_value(node, "type")
        if class_type == "CLIPLoader" and type_value == FLUX2_CLIP_TYPE_VALUE:
            reasons.append(
                "CLIPLoader with type='flux2' found (confirmed real combo value) -> model_family=flux, flux_generation=flux2_klein"
            )
            return "flux", "flux2_klein"
        if class_type == "DualCLIPLoader" and type_value == FLUX1_DUAL_CLIP_TYPE_VALUE:
            reasons.append(
                "DualCLIPLoader with type='flux' found (confirmed real combo value) -> model_family=flux, flux_generation=flux1"
            )
            return "flux", "flux1"

    for node in workflow.values():
        if isinstance(node, dict) and str(node.get("class_type")) in SDXL_MARKER_NODE_TYPES:
            reasons.append(
                "CLIPTextEncodeSDXL/CLIPTextEncodeSDXLRefiner found (SDXL-specific node, distinct signature from generic CLIPTextEncode) -> model_family=sdxl"
            )
            return "sdxl", None

    reasons.append(
        "No confirmed Flux (DualCLIPLoader type='flux' / CLIPLoader type='flux2') or SDXL "
        "(CLIPTextEncodeSDXL) signal found. A bare CheckpointLoaderSimple/CheckpointLoader "
        "cannot be reliably distinguished as sd15 vs sdxl without guessing, so model_family "
        "stays unknown."
    )
    return "unknown", None


def _detect_loader_strategy(
    *,
    checkpoint_nodes: List[Tuple[str, Dict[str, Any]]],
    unet_nodes: List[Tuple[str, Dict[str, Any]]],
    clip_loader_nodes: List[Tuple[str, Dict[str, Any]]],
    vae_loader_nodes: List[Tuple[str, Dict[str, Any]]],
    runtime_node_defs: Dict[str, Any],
    node_id_to_class: Dict[str, str],
    reasons: List[str],
) -> str:
    if unet_nodes:
        fp8_unet_ids = [
            node_id
            for node_id, node in unet_nodes
            if str(_input_value(node, "weight_dtype") or "").startswith(FP8_WEIGHT_DTYPE_PREFIX)
        ]
        if fp8_unet_ids:
            reasons.append(
                "UNETLoader with weight_dtype starting with 'fp8' found (confirmed real combo "
                "options: default/fp8_e4m3fn/fp8_e4m3fn_fast/fp8_e5m2) -> loader_strategy=fp8_diffusion_model"
            )
            return "fp8_diffusion_model"
        if clip_loader_nodes and vae_loader_nodes:
            reasons.append(
                "UNETLoader + a CLIP loader (DualCLIPLoader/CLIPLoader/TripleCLIPLoader/"
                "QuadrupleCLIPLoader) + VAELoader all present -> "
                "loader_strategy=diffusion_model_plus_text_encoders_plus_vae"
            )
            return "diffusion_model_plus_text_encoders_plus_vae"
        reasons.append(
            "UNETLoader present but a CLIP loader and/or VAELoader was not found alongside it; "
            "the split-component pattern is incomplete in this workflow, so loader_strategy stays unknown "
            "rather than guessing the missing piece."
        )
        return "unknown"

    if checkpoint_nodes:
        reasons.append(
            "CheckpointLoaderSimple/CheckpointLoader present (RETURN_TYPES = MODEL, CLIP, VAE) -> "
            "loader_strategy=checkpoint_single_file. Note: this project has no confirmed node-level "
            "signal to distinguish a 'merged_checkpoint' from a regular single-file checkpoint, so "
            "that separate category is not produced."
        )
        return "checkpoint_single_file"

    custom_loader_id = _find_custom_model_returning_loader(
        workflow_class_names=set(node_id_to_class.values()),
        runtime_node_defs=runtime_node_defs,
        known_classes=CHECKPOINT_LOADER_TYPES | DIFFUSION_MODEL_LOADER_TYPES,
    )
    if custom_loader_id:
        reasons.append(
            f"Node class '{custom_loader_id}' has a confirmed RETURN_TYPES including MODEL per "
            "runtime_node_defs, but is not one of the known checkpoint/UNETLoader classes -> "
            "loader_strategy=custom_loader"
        )
        return "custom_loader"

    reasons.append("No checkpoint, UNETLoader, or MODEL-returning loader node found in this workflow.")
    return "unknown"


def _find_custom_model_returning_loader(
    *,
    workflow_class_names: Set[str],
    runtime_node_defs: Dict[str, Any],
    known_classes: Set[str],
) -> Optional[str]:
    for class_type in sorted(workflow_class_names - known_classes):
        runtime_def = runtime_node_defs.get(class_type)
        if not isinstance(runtime_def, dict):
            continue
        return_types = runtime_def.get("return_types") or []
        if isinstance(return_types, list) and any(str(t).upper() == "MODEL" for t in return_types):
            return class_type
    return None


def _trace_vae_input_sources(workflow: Dict[str, Any], node_id_to_class: Dict[str, str]) -> Set[str]:
    sources: Set[str] = set()
    for node in workflow.values():
        if not isinstance(node, dict):
            continue
        value = _input_value(node, "vae")
        if is_connection(value):
            source_class = node_id_to_class.get(str(value[0]))
            if source_class:
                sources.add(source_class)
    return sources


def _detect_vae_strategy(
    workflow: Dict[str, Any],
    loader_strategy: str,
    node_id_to_class: Dict[str, str],
    reasons: List[str],
) -> str:
    vae_sources = _trace_vae_input_sources(workflow, node_id_to_class)
    vae_loader_used = "VAELoader" in vae_sources
    checkpoint_vae_used = bool(vae_sources & CHECKPOINT_LOADER_TYPES)

    if loader_strategy in {"diffusion_model_plus_text_encoders_plus_vae", "fp8_diffusion_model"}:
        if vae_loader_used:
            reasons.append("A 'vae' input is connected to a VAELoader output, matching the architecturally required external VAE for split-component loading.")
        else:
            reasons.append("Split-component (UNETLoader-based) loading architecturally requires an external VAE, but no VAELoader connection to a 'vae' input was found in this workflow.")
        return "external_required"

    if loader_strategy == "checkpoint_single_file":
        if vae_loader_used:
            reasons.append("CheckpointLoaderSimple/CheckpointLoader bundles a VAE output, but a separate VAELoader is also connected to a 'vae' input, overriding the bundled VAE.")
            return "external_optional"
        if checkpoint_vae_used or not vae_sources:
            reasons.append("CheckpointLoaderSimple/CheckpointLoader bundled VAE output is used (or no explicit override was found).")
            return "bundled"

    reasons.append("No confirmed loader_strategy pattern; vae_strategy cannot be determined.")
    return "unknown"


def _find_root_model_loader_class(
    workflow: Dict[str, Any],
    start_node_id: str,
    max_depth: int = 10,
) -> Optional[str]:
    current_id = start_node_id
    visited: Set[str] = set()
    for _ in range(max_depth):
        if current_id in visited:
            return None
        visited.add(current_id)
        node = workflow.get(current_id)
        if not isinstance(node, dict):
            return None
        class_type = str(node.get("class_type"))
        if class_type in CHECKPOINT_LOADER_TYPES or class_type in DIFFUSION_MODEL_LOADER_TYPES:
            return class_type
        if class_type in LORA_LOADER_TYPES:
            model_value = _input_value(node, "model")
            if is_connection(model_value):
                current_id = str(model_value[0])
                continue
        return None
    return None


def _detect_lora_family(
    workflow: Dict[str, Any],
    node_id_to_class: Dict[str, str],
    model_family: str,
    reasons: List[str],
) -> str:
    lora_nodes = _nodes_of_class(workflow, LORA_LOADER_TYPES)
    if not lora_nodes:
        reasons.append("No LoraLoader/LoraLoaderModelOnly node found; lora_family is unknown (not applicable).")
        return "unknown"

    traced_root_classes: Set[str] = set()
    for _, lora_node in lora_nodes:
        model_value = _input_value(lora_node, "model")
        if not is_connection(model_value):
            continue
        root_class = _find_root_model_loader_class(workflow, str(model_value[0]))
        if root_class:
            traced_root_classes.add(root_class)

    if not traced_root_classes:
        reasons.append("LoraLoader present, but its 'model' input could not be traced back to a recognized base-model loader; lora_family stays unknown rather than guessing.")
        return "unknown"

    if model_family == "unknown":
        reasons.append("LoraLoader traced back to a recognized base-model loader, but the overall model_family itself is unknown, so lora_family stays unknown.")
        return "unknown"

    reasons.append(f"LoraLoader 'model' input traced back to a recognized base-model loader ({', '.join(sorted(traced_root_classes))}); lora_family set to the detected model_family ('{model_family}').")
    return model_family


def _decide_confidence(model_family: str, loader_strategy: str, vae_strategy: str) -> str:
    resolved = sum(1 for value in (model_family, loader_strategy, vae_strategy) if value != "unknown")
    if resolved == 3:
        return "high"
    if resolved >= 1:
        return "medium"
    return "low"
