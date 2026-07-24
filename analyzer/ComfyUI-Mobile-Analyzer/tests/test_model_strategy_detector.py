from __future__ import annotations

import importlib.util
import pathlib
import sys
import types
import unittest


MODULE_DIR = pathlib.Path(__file__).resolve().parents[1]
PACKAGE_NAME = "comfyui_mobile_analyzer_testpkg_model_strategy"


def load_module(module_name: str, file_name: str):
    package = sys.modules.setdefault(PACKAGE_NAME, types.ModuleType(PACKAGE_NAME))
    package.__path__ = [str(MODULE_DIR)]
    spec = importlib.util.spec_from_file_location(f"{PACKAGE_NAME}.{module_name}", MODULE_DIR / file_name)
    module = importlib.util.module_from_spec(spec)
    sys.modules[f"{PACKAGE_NAME}.{module_name}"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


nodes_v2_debug = load_module("nodes_v2_debug", "nodes_v2_debug.py")
model_strategy_detector = load_module("model_strategy_detector", "model_strategy_detector.py")


class ModelStrategyDetectorTests(unittest.TestCase):
    def test_flux1_dual_clip_loader_pattern(self):
        workflow = {
            "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "flux1-dev.safetensors", "weight_dtype": "default"}},
            "2": {
                "class_type": "DualCLIPLoader",
                "inputs": {"clip_name1": "clip_l.safetensors", "clip_name2": "t5xxl.safetensors", "type": "flux"},
            },
            "3": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
            "4": {"class_type": "VAEDecode", "inputs": {"samples": ["5", 0], "vae": ["3", 0]}},
        }
        result = model_strategy_detector.detect_model_strategy(workflow, runtime_node_defs={})

        self.assertEqual(result["model_family"], "flux")
        self.assertEqual(result["flux_generation"], "flux1")
        self.assertEqual(result["loader_strategy"], "diffusion_model_plus_text_encoders_plus_vae")
        self.assertEqual(result["vae_strategy"], "external_required")
        self.assertTrue(result["reasons"])

    def test_flux2_klein_clip_loader_is_distinct_from_flux1(self):
        flux1_workflow = {
            "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "flux1-dev.safetensors", "weight_dtype": "default"}},
            "2": {
                "class_type": "DualCLIPLoader",
                "inputs": {"clip_name1": "clip_l.safetensors", "clip_name2": "t5xxl.safetensors", "type": "flux"},
            },
            "3": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
        }
        flux2_workflow = {
            "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "flux2-klein.safetensors", "weight_dtype": "default"}},
            "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3_8b_fp8.safetensors", "type": "flux2"}},
            "3": {"class_type": "VAELoader", "inputs": {"vae_name": "flux2-vae.safetensors"}},
        }

        flux1_result = model_strategy_detector.detect_model_strategy(flux1_workflow, runtime_node_defs={})
        flux2_result = model_strategy_detector.detect_model_strategy(flux2_workflow, runtime_node_defs={})

        self.assertEqual(flux1_result["model_family"], "flux")
        self.assertEqual(flux2_result["model_family"], "flux")
        self.assertEqual(flux1_result["flux_generation"], "flux1")
        self.assertEqual(flux2_result["flux_generation"], "flux2_klein")
        self.assertNotEqual(flux1_result["flux_generation"], flux2_result["flux_generation"])

    def test_checkpoint_single_file_with_bundled_vae(self):
        workflow = {
            "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "sd_xl_base.safetensors"}},
            "2": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["1", 2]}},
        }
        result = model_strategy_detector.detect_model_strategy(workflow, runtime_node_defs={})

        self.assertEqual(result["loader_strategy"], "checkpoint_single_file")
        self.assertEqual(result["vae_strategy"], "bundled")

    def test_lora_family_inferred_from_traced_model_loader(self):
        workflow = {
            "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "flux1-dev.safetensors", "weight_dtype": "default"}},
            "2": {
                "class_type": "DualCLIPLoader",
                "inputs": {"clip_name1": "clip_l.safetensors", "clip_name2": "t5xxl.safetensors", "type": "flux"},
            },
            "3": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
            "4": {
                "class_type": "LoraLoaderModelOnly",
                "inputs": {"model": ["1", 0], "lora_name": "flux_style.safetensors", "strength_model": 0.8},
            },
        }
        result = model_strategy_detector.detect_model_strategy(workflow, runtime_node_defs={})

        self.assertEqual(result["model_family"], "flux")
        self.assertEqual(result["lora_family"], "flux")

    def test_lora_family_unknown_when_root_loader_not_recognized(self):
        workflow = {
            "1": {"class_type": "SomeUnknownCustomLoader", "inputs": {}},
            "2": {
                "class_type": "LoraLoaderModelOnly",
                "inputs": {"model": ["1", 0], "lora_name": "mystery.safetensors", "strength_model": 0.8},
            },
        }
        result = model_strategy_detector.detect_model_strategy(workflow, runtime_node_defs={})

        self.assertEqual(result["lora_family"], "unknown")

    def test_workflow_with_no_loader_material_is_all_unknown_low_confidence(self):
        workflow = {
            "1": {"class_type": "CLIPTextEncode", "inputs": {"text": "a cat"}},
            "2": {"class_type": "KSampler", "inputs": {"seed": 1, "steps": 20, "cfg": 7.0}},
            "3": {"class_type": "SaveImage", "inputs": {"images": ["2", 0]}},
        }
        result = model_strategy_detector.detect_model_strategy(workflow, runtime_node_defs={})

        self.assertEqual(result["model_family"], "unknown")
        self.assertEqual(result["loader_strategy"], "unknown")
        self.assertEqual(result["vae_strategy"], "unknown")
        self.assertEqual(result["lora_family"], "unknown")
        self.assertEqual(result["confidence"], "low")

    def test_fp8_diffusion_model_detected_from_weight_dtype(self):
        workflow = {
            "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "flux1-dev-fp8.safetensors", "weight_dtype": "fp8_e4m3fn"}},
            "2": {
                "class_type": "DualCLIPLoader",
                "inputs": {"clip_name1": "clip_l.safetensors", "clip_name2": "t5xxl.safetensors", "type": "flux"},
            },
            "3": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
        }
        result = model_strategy_detector.detect_model_strategy(workflow, runtime_node_defs={})

        self.assertEqual(result["loader_strategy"], "fp8_diffusion_model")

    def test_fp8_checkpoint_and_gguf_are_not_implemented(self):
        # Explicitly documents the deferred scope: neither category is ever
        # produced by this detector version, per the user's decision to defer
        # both until RunPod hardware verification is available.
        workflow = {
            "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "some_model_fp8.safetensors"}},
        }
        result = model_strategy_detector.detect_model_strategy(workflow, runtime_node_defs={})

        self.assertNotEqual(result["loader_strategy"], "fp8_checkpoint")
        self.assertNotEqual(result["loader_strategy"], "gguf_quantized")


if __name__ == "__main__":
    unittest.main()
