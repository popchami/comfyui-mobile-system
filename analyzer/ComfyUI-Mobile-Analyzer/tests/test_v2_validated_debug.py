from __future__ import annotations

import importlib.util
import pathlib
import sys
import types
import unittest


MODULE_DIR = pathlib.Path(__file__).resolve().parents[1]
PACKAGE_NAME = "comfyui_mobile_analyzer_testpkg"


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
nodes_v2_validated_debug = load_module("nodes_v2_validated_debug", "nodes_v2_validated_debug.py")


class V2ValidatedDebugTests(unittest.TestCase):
    def test_basic_txt2img_candidates_become_validated_fields(self):
        workflow = {
            "1": {"class_type": "CLIPTextEncode", "inputs": {"text": "a cat"}},
            "2": {"class_type": "KSampler", "inputs": {"seed": 123, "steps": 20, "cfg": 7.0}},
            "3": {"class_type": "SaveImage", "inputs": {"images": ["2", 0], "filename_prefix": "test"}},
        }
        candidates = nodes_v2_debug.extract_operation_candidates(workflow, runtime_node_defs={})
        results = nodes_v2_validated_debug.validate_operation_candidates(workflow, candidates)
        fields, patches = nodes_v2_validated_debug.build_validated_fields(results)

        field_ids = {field["field_id"] for field in fields}
        self.assertIn("field_1_text", field_ids)
        self.assertIn("field_2_seed", field_ids)
        self.assertIn("field_2_steps", field_ids)
        self.assertIn("field_2_cfg", field_ids)
        self.assertIn("pt_1_text", patches)
        self.assertIn("pt_2_seed", patches)

    def test_connection_input_is_not_candidate(self):
        workflow = {
            "1": {"class_type": "CLIPTextEncode", "inputs": {"text": "a cat"}},
            "2": {"class_type": "SomeNode", "inputs": {"conditioning": ["1", 0], "strength": 0.8}},
        }
        candidates = nodes_v2_debug.extract_operation_candidates(workflow, runtime_node_defs={})
        candidate_inputs = {(candidate["node_id"], candidate["input"]) for candidate in candidates}

        self.assertNotIn(("2", "conditioning"), candidate_inputs)
        self.assertIn(("2", "strength"), candidate_inputs)

    def test_sensitive_api_key_is_disabled(self):
        workflow = {
            "1": {"class_type": "ExternalApiNode", "inputs": {"api_key": "secret", "prompt": "hello"}},
        }
        candidates = nodes_v2_debug.extract_operation_candidates(workflow, runtime_node_defs={})
        results = nodes_v2_validated_debug.validate_operation_candidates(workflow, candidates)
        result_by_input = {result["input"]: result for result in results}

        self.assertEqual(result_by_input["api_key"]["status"], "disabled")
        self.assertFalse(result_by_input["api_key"]["editable"])
        self.assertIn(result_by_input["prompt"]["status"], {"safe_editable", "expert_editable"})

    def test_url_like_field_requires_review(self):
        workflow = {
            "1": {"class_type": "FetchNode", "inputs": {"url": "https://example.invalid/file.png"}},
        }
        candidates = nodes_v2_debug.extract_operation_candidates(workflow, runtime_node_defs={})
        results = nodes_v2_validated_debug.validate_operation_candidates(workflow, candidates)

        self.assertEqual(results[0]["status"], "review_required")
        self.assertFalse(results[0]["editable"])

    def test_unknown_custom_string_goes_to_expert_editable(self):
        workflow = {
            "1": {"class_type": "SomePromptMixer", "inputs": {"style_text": "cinematic lighting"}},
        }
        candidates = nodes_v2_debug.extract_operation_candidates(workflow, runtime_node_defs={})
        results = nodes_v2_validated_debug.validate_operation_candidates(workflow, candidates)
        fields, patches = nodes_v2_validated_debug.build_validated_fields(results)

        self.assertEqual(results[0]["status"], "expert_editable")
        self.assertEqual(fields[0]["section"], "expert_unknown")
        self.assertTrue(fields[0]["safety"]["requires_warning"])
        self.assertIn("pt_1_style_text", patches)

    def test_output_detection_for_save_image(self):
        workflow = {
            "1": {"class_type": "SaveImage", "inputs": {"images": ["2", 0]}},
        }
        outputs = nodes_v2_debug.detect_outputs(workflow, runtime_node_defs={})

        self.assertEqual(len(outputs), 1)
        self.assertEqual(outputs[0]["output_type"], "image")
        self.assertEqual(outputs[0]["viewer"], "image_viewer")

    def test_validated_profile_contains_validation_block(self):
        workflow = {
            "1": {"class_type": "CLIPTextEncode", "inputs": {"text": "a cat"}},
            "2": {"class_type": "SaveImage", "inputs": {"images": ["1", 0]}},
        }
        candidates = nodes_v2_debug.extract_operation_candidates(workflow, runtime_node_defs={})
        outputs = nodes_v2_debug.detect_outputs(workflow, runtime_node_defs={})
        runtime_requirements = nodes_v2_debug.detect_runtime_requirements(workflow)
        results = nodes_v2_validated_debug.validate_operation_candidates(workflow, candidates)
        fields, patches = nodes_v2_validated_debug.build_validated_fields(results)
        warnings = nodes_v2_validated_debug.build_validated_warnings(
            workflow=workflow,
            runtime_node_defs={},
            candidates=candidates,
            validation_results=results,
            outputs=outputs,
        )
        compatibility = nodes_v2_validated_debug.decide_validated_compatibility(
            fields=fields,
            patch_targets=patches,
            outputs=outputs,
            warnings=warnings,
            runtime_requirements=runtime_requirements,
        )

        self.assertIn("level", compatibility)
        self.assertTrue(fields)
        self.assertTrue(patches)
        self.assertEqual(nodes_v2_validated_debug.summarize_validation_results(results)["editable"], len(fields))

    def test_lora_inputs_become_model_and_strength_fields(self):
        workflow = {
            "1": {
                "class_type": "LoraLoader",
                "inputs": {
                    "lora_name": "style.safetensors",
                    "strength_model": 0.75,
                    "strength_clip": 0.65,
                    "model": ["2", 0],
                    "clip": ["3", 0],
                },
            }
        }
        candidates = nodes_v2_debug.extract_operation_candidates(workflow, runtime_node_defs={})
        results = nodes_v2_validated_debug.validate_operation_candidates(workflow, candidates)
        fields, patches = nodes_v2_validated_debug.build_validated_fields(results)
        field_by_input = {field["source"]["input"]: field for field in fields}

        self.assertEqual(field_by_input["lora_name"]["control_type"], "model_picker")
        self.assertEqual(field_by_input["lora_name"]["section"], "model")
        self.assertIn("strength_model", field_by_input)
        self.assertIn("strength_clip", field_by_input)
        self.assertIn("pt_1_lora_name", patches)
        self.assertNotIn("pt_1_model", patches)
        self.assertNotIn("pt_1_clip", patches)

    def test_controlnet_like_strength_is_advanced_field(self):
        workflow = {
            "1": {
                "class_type": "ControlNetApplyAdvanced",
                "inputs": {
                    "strength": 0.8,
                    "start_percent": 0.0,
                    "end_percent": 1.0,
                    "conditioning": ["2", 0],
                },
            }
        }
        candidates = nodes_v2_debug.extract_operation_candidates(workflow, runtime_node_defs={})
        results = nodes_v2_validated_debug.validate_operation_candidates(workflow, candidates)
        fields, _ = nodes_v2_validated_debug.build_validated_fields(results)
        field_inputs = {field["source"]["input"]: field for field in fields}

        self.assertIn("strength", field_inputs)
        self.assertEqual(field_inputs["strength"]["section"], "advanced")
        self.assertNotIn("conditioning", field_inputs)

    def test_video_and_audio_outputs_are_detected(self):
        workflow = {
            "1": {"class_type": "VHS_VideoCombine", "inputs": {"frame_rate": 24.0}},
            "2": {"class_type": "SaveAudio", "inputs": {"filename_prefix": "voice"}},
        }
        outputs = nodes_v2_debug.detect_outputs(workflow, runtime_node_defs={})
        output_types = {output["output_type"] for output in outputs}
        viewers = {output["viewer"] for output in outputs}

        self.assertIn("video", output_types)
        self.assertIn("audio", output_types)
        self.assertIn("video_viewer", viewers)
        self.assertIn("audio_player", viewers)

    def test_external_api_warning_is_emitted(self):
        workflow = {
            "1": {"class_type": "OpenAIImageNode", "inputs": {"prompt": "a cat", "api_key": "secret"}},
            "2": {"class_type": "SaveImage", "inputs": {"images": ["1", 0]}},
        }
        candidates = nodes_v2_debug.extract_operation_candidates(workflow, runtime_node_defs={})
        outputs = nodes_v2_debug.detect_outputs(workflow, runtime_node_defs={})
        results = nodes_v2_validated_debug.validate_operation_candidates(workflow, candidates)
        warnings = nodes_v2_validated_debug.build_validated_warnings(
            workflow=workflow,
            runtime_node_defs={},
            candidates=candidates,
            validation_results=results,
            outputs=outputs,
        )
        warning_types = {warning["type"] for warning in warnings}

        self.assertIn("external_api", warning_types)
        self.assertIn("validator_blocked_candidate", warning_types)

    def test_missing_runtime_definition_warning_is_emitted(self):
        workflow = {
            "1": {"class_type": "UnknownCustomNode", "inputs": {"style_text": "cinematic"}},
            "2": {"class_type": "SaveImage", "inputs": {"images": ["1", 0]}},
        }
        candidates = nodes_v2_debug.extract_operation_candidates(workflow, runtime_node_defs={})
        outputs = nodes_v2_debug.detect_outputs(workflow, runtime_node_defs={})
        results = nodes_v2_validated_debug.validate_operation_candidates(workflow, candidates)
        warnings = nodes_v2_validated_debug.build_validated_warnings(
            workflow=workflow,
            runtime_node_defs={},
            candidates=candidates,
            validation_results=results,
            outputs=outputs,
        )
        missing_defs = [warning for warning in warnings if warning["type"] == "missing_runtime_definition"]

        self.assertTrue(missing_defs)
        self.assertTrue(any(warning.get("related_class_type") == "UnknownCustomNode" for warning in missing_defs))

    def test_runtime_definition_metadata_sets_required_and_confidence(self):
        workflow = {
            "1": {"class_type": "CustomTextNode", "inputs": {"text": "hello"}},
        }
        runtime_node_defs = {
            "CustomTextNode": {
                "inputs": {
                    "required": {
                        "text": {
                            "raw_type": "STRING",
                            "normalized_value_type": "string",
                            "candidate_control_type": "textarea",
                            "config": {"multiline": True},
                            "options": None,
                        }
                    }
                }
            }
        }
        candidates = nodes_v2_debug.extract_operation_candidates(workflow, runtime_node_defs=runtime_node_defs)
        results = nodes_v2_validated_debug.validate_operation_candidates(workflow, candidates)
        fields, patches = nodes_v2_validated_debug.build_validated_fields(results)

        self.assertEqual(candidates[0]["source_confidence"], "runtime_definition")
        self.assertEqual(candidates[0]["input_group"], "required")
        self.assertEqual(fields[0]["control_type"], "textarea")
        self.assertTrue(patches["pt_1_text"]["validator"]["required"])

    def test_no_output_makes_compatibility_unsupported(self):
        workflow = {
            "1": {"class_type": "CLIPTextEncode", "inputs": {"text": "a cat"}},
        }
        candidates = nodes_v2_debug.extract_operation_candidates(workflow, runtime_node_defs={})
        outputs = nodes_v2_debug.detect_outputs(workflow, runtime_node_defs={})
        runtime_requirements = nodes_v2_debug.detect_runtime_requirements(workflow)
        results = nodes_v2_validated_debug.validate_operation_candidates(workflow, candidates)
        fields, patches = nodes_v2_validated_debug.build_validated_fields(results)
        warnings = nodes_v2_validated_debug.build_validated_warnings(
            workflow=workflow,
            runtime_node_defs={},
            candidates=candidates,
            validation_results=results,
            outputs=outputs,
        )
        compatibility = nodes_v2_validated_debug.decide_validated_compatibility(
            fields=fields,
            patch_targets=patches,
            outputs=outputs,
            warnings=warnings,
            runtime_requirements=runtime_requirements,
        )

        self.assertEqual(compatibility["level"], "unsupported")
        self.assertFalse(compatibility["safe_to_generate"])


if __name__ == "__main__":
    unittest.main()
