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


if __name__ == "__main__":
    unittest.main()
