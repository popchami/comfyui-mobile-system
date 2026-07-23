#!/usr/bin/env python3
"""scripts/one_panel_pilot.py(「ハルト1人・1コマ生成試験」事前準備)のテスト。

RunPod API・GPU画像生成・大容量モデルダウンロードは一切行わない。
news-game-translator側scripts/manga_schema.py(実在するローカルリポジトリ、
ネットワークアクセスなし)への依存は、既存の接続契約を検証する意図で
実際にimportして使う。reference_image解決は、既存tests/
test_resolve_reference_image.pyと同じ手法(REFERENCE_IMAGES_ROOTを
tempdirへ差し替え)で完全に隔離する。
"""
import copy
import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import one_panel_pilot as opp  # noqa: E402
import resolve_reference_image as rri  # noqa: E402

FIXTURE_PATH = (
    ROOT / "profiles" / "sdxl" / "isekai_nihon_manga" / "one_panel_pilot" / "haruto_panel1.example.json"
)
CONFIG_PATH = ROOT / "profiles" / "sdxl" / "isekai_nihon_manga" / "one_panel_pilot" / "config.example.json"


def load_fixture_packet():
    with FIXTURE_PATH.open(encoding="utf-8") as f:
        return json.load(f)


class IsolatedReferenceImagesTestCase(unittest.TestCase):
    """resolve_reference_image.REFERENCE_IMAGES_ROOTをtempdirへ差し替え、
    ハルトの表情2種だけを持つ最小構成を用意する(既存test_resolve_reference_image.py
    と同じ隔離手法)。
    """

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.root = pathlib.Path(self._tmpdir.name)

        haruto_dir = self.root / "haruto"
        (haruto_dir / "images").mkdir(parents=True)
        (haruto_dir / "manifest.json").write_text(
            json.dumps({"neutral": "00-neutral.png", "surprise-weak": "04-surprise-weak.png"}),
            encoding="utf-8",
        )
        (haruto_dir / "images" / "00-neutral.png").write_bytes(b"fake-neutral-png-bytes")
        (haruto_dir / "images" / "04-surprise-weak.png").write_bytes(b"fake-surprise-weak-png-bytes")

        self._patcher = mock.patch.object(rri, "REFERENCE_IMAGES_ROOT", self.root)
        self._patcher.start()
        self.addCleanup(self._patcher.stop)


class ComputePanelFitTest(unittest.TestCase):
    def test_normal_case_matches_documented_values(self):
        # 採用した生成解像度1536x640→対象コマinner 1009x345。
        fit = opp.compute_panel_fit(1536, 640, 1009, 345)
        self.assertEqual(fit["resize_to"], {"width": 1009, "height": 420.42})
        self.assertEqual(fit["crop_box"], {"left": 0, "upper": 37.71, "right": 1009, "lower": 382.71})
        self.assertEqual(fit["final_size"], {"width": 1009, "height": 345})
        self.assertAlmostEqual(fit["crop_ratio"], 0.1794, places=3)

    def test_exact_fit_boundary_zero_crop(self):
        # 生成解像度を縮小した結果がちょうどtarget_heightと一致する場合、
        # クロップ量は0で成功する。
        fit = opp.compute_panel_fit(2000, 690, 1000, 345)
        self.assertEqual(fit["resize_to"], {"width": 1000, "height": 345.0})
        self.assertEqual(fit["crop_box"], {"left": 0, "upper": 0.0, "right": 1000, "lower": 345.0})
        self.assertEqual(fit["crop_ratio"], 0.0)

    def test_resolution_too_short_rejected(self):
        # 縮小後の高さが対象コマの高さに届かない生成解像度は明確なエラーにする。
        with self.assertRaises(opp.PilotError) as ctx:
            opp.compute_panel_fit(1536, 300, 1009, 345)
        self.assertIn("収まりません", str(ctx.exception))

    def test_non_positive_dimensions_rejected(self):
        for args in [(0, 640, 1009, 345), (1536, -1, 1009, 345), (1536, 640, 0, 345), (1536, 640, 1009, 0)]:
            with self.subTest(args=args):
                with self.assertRaises(opp.PilotError):
                    opp.compute_panel_fit(*args)

    def test_non_numeric_dimension_rejected(self):
        with self.assertRaises(opp.PilotError):
            opp.compute_panel_fit("1536", 640, 1009, 345)

    def test_integer_pixel_contract_matches_documented_values(self):
        # Codexレビュー指摘(Major)の回帰テスト: 連続座標の丸め値だけでは
        # 実ピクセル処理を一意に再現できない。整数ピクセル契約
        # (resize_to_px/crop_box_px/resampling_method)を検証する。
        fit = opp.compute_panel_fit(1536, 640, 1009, 345)
        self.assertEqual(fit["resize_to_px"], {"width": 1009, "height": 421})
        self.assertEqual(fit["crop_box_px"], {"left": 0, "upper": 38, "right": 1009, "lower": 383})
        self.assertEqual(fit["resampling_method"], opp.PANEL_FIT_RESAMPLING_METHOD)

    def test_integer_pixel_contract_zero_crop_case(self):
        fit = opp.compute_panel_fit(2000, 690, 1000, 345)
        self.assertEqual(fit["resize_to_px"], {"width": 1000, "height": 345})
        self.assertEqual(fit["crop_box_px"], {"left": 0, "upper": 0, "right": 1000, "lower": 345})

    def test_integer_pixel_crop_box_height_matches_target(self):
        # crop_box_pxのlower-upperは常にtarget_heightと一致しなければならない。
        fit = opp.compute_panel_fit(1536, 640, 1009, 345)
        box = fit["crop_box_px"]
        self.assertEqual(box["lower"] - box["upper"], 345)

    def test_float_dimension_rejected(self):
        # 2回目のCodexレビュー指摘(Major)の回帰テスト: 以前はfloatも
        # 正の数値として許可していたため、resize_to_px/crop_box_pxへ
        # floatが混入し、整数ピクセル契約が破られていた。
        for args in [
            (1536, 640, 1009.5, 345.5),
            (1536.0, 640, 1009, 345),
            (1536, 640.5, 1009, 345),
            (1536, 640, 1009, 345.0),
        ]:
            with self.subTest(args=args):
                with self.assertRaises(opp.PilotError):
                    opp.compute_panel_fit(*args)

    def test_bool_dimension_rejected(self):
        # boolはintのサブクラスであるため明示的に除外する。
        for args in [(True, 640, 1009, 345), (1536, 640, 1009, True)]:
            with self.subTest(args=args):
                with self.assertRaises(opp.PilotError):
                    opp.compute_panel_fit(*args)

    def test_integer_pixel_contract_exact_for_large_integers(self):
        # 2回目のCodexレビュー指摘(Major)の回帰テスト: 以前は
        # math.ceil(resized_height - 1e-9)という浮動小数点経由の切り上げが、
        # 極端に大きい整数入力で文書記載の式とずれていた。整数演算のみで
        # 計算することで、巨大な入力でも正確なceilになることを確認する。
        fit = opp.compute_panel_fit(1_000_000_000, 1_000_000_001, 1, 1)
        self.assertEqual(fit["resize_to_px"], {"width": 1, "height": 2})


class NegativePromptTest(unittest.TestCase):
    def test_includes_existing_baseline_verbatim(self):
        negative = opp.build_negative_prompt()
        self.assertIn(opp.BASE_NEGATIVE_PROMPT, negative)

    def test_includes_all_required_additional_concepts(self):
        negative = opp.build_negative_prompt().lower()
        for concept in opp.REQUIRED_ADDITIONAL_NEGATIVE_CONCEPTS:
            with self.subTest(concept=concept):
                self.assertIn(concept.lower(), negative)

    def test_does_not_duplicate_terms_already_in_baseline(self):
        negative = opp.build_negative_prompt()
        # "watermark"は既存正本に既に含まれるため、重複追加されていないこと
        # (カンマ区切りでの出現回数が1回であること)を確認する。
        terms = [t.strip().lower() for t in negative.split(",")]
        self.assertEqual(terms.count("watermark"), 1)

    def test_panel_specific_negative_prompt_reaches_result(self):
        # Codexレビュー指摘(Minor)の回帰テスト: 以前はpanel["negative_prompt"]
        # (Packetのコマ固有除外事項)が完全に無視されていた。
        panel = {"negative_prompt": "a-panel-specific-exclusion-term"}
        negative = opp.build_negative_prompt(panel)
        self.assertIn("a-panel-specific-exclusion-term", negative)

    def test_panel_specific_negative_prompt_not_duplicated(self):
        panel = {"negative_prompt": "watermark, blurry"}
        negative = opp.build_negative_prompt(panel)
        terms = [t.strip().lower() for t in negative.split(",")]
        self.assertEqual(terms.count("watermark"), 1)
        self.assertEqual(terms.count("blurry"), 1)

    def test_panel_specific_negative_prompt_internal_duplicates_not_repeated(self):
        # 2回目のCodexレビュー指摘(Minor)の回帰テスト: 以前は内包表記が
        # existing_termsを更新せずに判定していたため、panel["negative_prompt"]
        # 自身の内部重複(大文字小文字違い含む)が素通りしていた。
        panel = {"negative_prompt": "custom term, CUSTOM TERM, custom term"}
        negative = opp.build_negative_prompt(panel)
        terms = [t.strip().lower() for t in negative.split(",")]
        self.assertEqual(terms.count("custom term"), 1)

    def test_no_panel_argument_still_works(self):
        self.assertEqual(opp.build_negative_prompt(), opp.build_negative_prompt(None))


class PositivePromptTest(unittest.TestCase):
    def test_includes_fixed_character_and_style_constraints(self):
        packet = load_fixture_packet()
        panel = opp.get_panel(packet, 1)
        performer = panel["performers"][0]
        prompt = opp.build_positive_prompt(panel, performer)
        for required in (
            "cherry blossom charm",
            "yellow-green",
            "no chinese-style clothing",
            "no korean-style clothing",
            "no romance elements",
        ):
            with self.subTest(required=required):
                self.assertIn(required, prompt)

    def test_includes_panel_image_prompt_as_base(self):
        packet = load_fixture_packet()
        panel = opp.get_panel(packet, 1)
        performer = panel["performers"][0]
        prompt = opp.build_positive_prompt(panel, performer)
        self.assertIn(panel["image_prompt"], prompt)

    def test_includes_composition_terms_from_panel_and_performer(self):
        # Codexレビュー指摘(Major)の回帰テスト: 以前はpanel.framing/
        # camera_angle・performer.position/facing/gazeがpositive promptへ
        # まったく反映されていなかった。
        packet = load_fixture_packet()
        panel = opp.get_panel(packet, 1)
        performer = panel["performers"][0]
        self.assertEqual(panel["framing"], "waist")
        self.assertEqual(panel["camera_angle"], "eye_level")
        self.assertEqual(performer["position"], "left")
        self.assertEqual(performer["facing"], "three_quarter_right")
        self.assertEqual(performer["gaze"], "object")

        prompt = opp.build_positive_prompt(panel, performer)
        for required in (
            opp.FRAMING_PROMPT_TERMS["waist"],
            opp.CAMERA_ANGLE_PROMPT_TERMS["eye_level"],
            opp.POSITION_PROMPT_TERMS["left"],
            opp.FACING_PROMPT_TERMS["three_quarter_right"],
            opp.GAZE_PROMPT_TERMS["object"],
        ):
            with self.subTest(required=required):
                self.assertIn(required, prompt)

    def test_unknown_composition_value_silently_omitted(self):
        panel = {"image_prompt": "base", "framing": "unknown-framing", "camera_angle": None}
        performer = {"position": "unknown-position", "facing": None, "gaze": None}
        prompt = opp.build_positive_prompt(panel, performer)
        self.assertIn("base", prompt)


class ValidatePilotScopeTest(unittest.TestCase):
    def setUp(self):
        self.manga_schema = opp.load_manga_schema()

    def test_valid_fixture_passes(self):
        packet = load_fixture_packet()
        reasons = opp.validate_pilot_scope(packet, self.manga_schema, 1, "ハルト")
        self.assertEqual(reasons, [])

    def test_two_performers_in_target_panel_rejected(self):
        packet = load_fixture_packet()
        packet["panels"][0]["performers"].append(copy.deepcopy(packet["panels"][2]["performers"][0]))
        # 2人になった場合、直前のdialogues整合性検証等でスキーマ側が先に
        # 拒否する可能性があるため、reasonsが非空であることのみ確認する
        # (試験固有チェックか一般構造検証かは問わない)。
        reasons = opp.validate_pilot_scope(packet, self.manga_schema, 1, "ハルト")
        self.assertTrue(reasons)

    def test_wrong_character_in_target_panel_rejected(self):
        packet = load_fixture_packet()
        packet["panels"][0]["performers"][0]["name"] = "アキラ"
        packet["panels"][0]["performers"][0]["reference_image"] = "akira/surprise-weak.png"
        reasons = opp.validate_pilot_scope(packet, self.manga_schema, 1, "ハルト")
        self.assertTrue(any("ハルト" in r for r in reasons))

    def test_missing_target_panel_rejected(self):
        packet = load_fixture_packet()
        packet["panels"] = [p for p in packet["panels"] if p["panel_no"] != 1]
        # panel_no=1が無くなるとPANEL_COUNT=4のチェックでスキーマ側が
        # 先に拒否するため、いずれにせよreasonsが非空であることを確認する。
        reasons = opp.validate_pilot_scope(packet, self.manga_schema, 1, "ハルト")
        self.assertTrue(reasons)

    def test_expression_reference_image_tag_mismatch_rejected(self):
        packet = load_fixture_packet()
        packet["panels"][0]["performers"][0]["reference_image"] = "haruto/neutral.png"
        reasons = opp.validate_pilot_scope(packet, self.manga_schema, 1, "ハルト")
        self.assertTrue(any("タグ" in r or "reference_image" in r for r in reasons))

    def test_wrong_packet_version_rejected(self):
        packet = load_fixture_packet()
        packet["packet_version"] = 1
        reasons = opp.validate_pilot_scope(packet, self.manga_schema, 1, "ハルト")
        self.assertTrue(any("packet_version" in r for r in reasons))

    def test_non_dict_packet_does_not_crash(self):
        for bad_packet in ([], "not-a-dict", None, 123):
            with self.subTest(bad_packet=bad_packet):
                reasons = opp.validate_pilot_scope(bad_packet, self.manga_schema, 1, "ハルト")
                self.assertTrue(reasons)

    def test_performers_as_dict_instead_of_list_does_not_crash(self):
        packet = load_fixture_packet()
        packet["panels"][0]["performers"] = {"name": "ハルト"}
        reasons = opp.validate_pilot_scope(packet, self.manga_schema, 1, "ハルト")
        self.assertTrue(reasons)

    def test_panels_as_dict_instead_of_list_does_not_crash(self):
        packet = load_fixture_packet()
        packet["panels"] = {"panel_no": 1}
        reasons = opp.validate_pilot_scope(packet, self.manga_schema, 1, "ハルト")
        self.assertTrue(reasons)


class ResolvePerformerReferenceImageTest(IsolatedReferenceImagesTestCase):
    def test_resolves_to_existing_isolated_fixture_file(self):
        performer = {"name": "ハルト", "expression": "surprise-weak", "reference_image": "haruto/surprise-weak.png"}
        path = opp.resolve_performer_reference_image(performer, rri)
        self.assertTrue(path.is_file())
        self.assertEqual(path.name, "04-surprise-weak.png")

    def test_unresolvable_logical_id_raises_pilot_error(self):
        performer = {"name": "ハルト", "expression": "joy-strong", "reference_image": "haruto/joy-strong.png"}
        with self.assertRaises(opp.PilotError):
            opp.resolve_performer_reference_image(performer, rri)

    def test_nonexistent_character_raises_pilot_error(self):
        performer = {"name": "アキラ", "expression": "neutral", "reference_image": "akira/neutral.png"}
        with self.assertRaises(opp.PilotError):
            opp.resolve_performer_reference_image(performer, rri)

    def test_non_png_resolved_file_rejected(self):
        # Codexレビュー指摘(Minor)の回帰テスト: manifest.jsonが有効な論理IDを
        # 画像ではないファイルへ対応付けていても、LoadImageへ渡す前に拒否する。
        haruto_dir = self.root / "haruto"
        manifest_path = haruto_dir / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["not-an-image"] = "not-an-image.txt"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        (haruto_dir / "images" / "not-an-image.txt").write_bytes(b"not a png")

        performer = {"name": "ハルト", "expression": "not-an-image", "reference_image": "haruto/not-an-image.png"}
        with self.assertRaises(opp.PilotError):
            opp.resolve_performer_reference_image(performer, rri)


class BuildComfyuiWorkflowTest(IsolatedReferenceImagesTestCase):
    def setUp(self):
        super().setUp()
        self.config = opp.load_config(CONFIG_PATH)
        self.packet = load_fixture_packet()
        self.panel = opp.get_panel(self.packet, 1)
        self.performer = self.panel["performers"][0]
        self.reference_image_path = opp.resolve_performer_reference_image(self.performer, rri)

    def test_workflow_contains_all_required_nodes(self):
        workflow, _, _ = opp.build_comfyui_workflow(
            self.panel, self.performer, self.reference_image_path, self.config, seed=12345
        )
        for node_id in opp.REQUIRED_WORKFLOW_NODE_IDS:
            self.assertIn(node_id, workflow)
            self.assertIn("class_type", workflow[node_id])
            self.assertIn("inputs", workflow[node_id])

    def test_workflow_passes_shape_validation(self):
        workflow, _, _ = opp.build_comfyui_workflow(
            self.panel, self.performer, self.reference_image_path, self.config, seed=12345
        )
        self.assertEqual(opp.validate_workflow_shape(workflow), [])

    def test_workflow_uses_config_model_names_not_hardcoded(self):
        custom_config = dict(self.config)
        custom_config["checkpoint_name"] = "custom_checkpoint.safetensors"
        custom_config["clip_vision_name"] = "custom_clip_vision.safetensors"
        workflow, _, _ = opp.build_comfyui_workflow(
            self.panel, self.performer, self.reference_image_path, custom_config, seed=1
        )
        self.assertEqual(workflow["1"]["inputs"]["ckpt_name"], "custom_checkpoint.safetensors")
        self.assertEqual(workflow["35"]["inputs"]["clip_name"], "custom_clip_vision.safetensors")

    def test_seed_is_fixed_not_randomized(self):
        workflow, _, _ = opp.build_comfyui_workflow(
            self.panel, self.performer, self.reference_image_path, self.config, seed=999
        )
        self.assertEqual(workflow["10"]["inputs"]["seed"], 999)
        self.assertEqual(workflow["10"]["inputs"]["control_after_generate"], "fixed")

    def test_batch_size_defaults_to_one(self):
        workflow, _, _ = opp.build_comfyui_workflow(
            self.panel, self.performer, self.reference_image_path, self.config, seed=1
        )
        self.assertEqual(workflow["9"]["inputs"]["batch_size"], 1)


class ValidateWorkflowShapeTest(unittest.TestCase):
    def _make_valid_workflow(self):
        return {
            "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "x.safetensors"}},
            "6": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 1], "text": "positive"}},
            "8": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 1], "text": opp.build_negative_prompt()}},
            "9": {"class_type": "EmptyLatentImage", "inputs": {"width": 1536, "height": 640, "batch_size": 1}},
            "10": {
                "class_type": "KSampler",
                "inputs": {
                    "model": ["31", 0], "positive": ["6", 0], "negative": ["8", 0], "latent_image": ["9", 0],
                    "seed": 1, "control_after_generate": "fixed", "steps": 20, "cfg": 5.0,
                    "sampler_name": "euler_ancestral", "scheduler": "simple", "denoise": 1.0,
                },
            },
            "11": {"class_type": "VAEDecode", "inputs": {"samples": ["10", 0], "vae": ["1", 2]}},
            "12": {"class_type": "SaveImage", "inputs": {"images": ["11", 0], "filename_prefix": "x"}},
            "30": {"class_type": "IPAdapterUnifiedLoader", "inputs": {"model": ["1", 0], "preset": "PLUS (high strength)", "provider": "autocast"}},
            "31": {"class_type": "IPAdapterAdvanced", "inputs": {"model": ["30", 0], "ipadapter": ["30", 1], "image": ["36", 0], "clip_vision": ["35", 0], "weight": 0.8, "weight_type": "linear", "combine_embeds": "concat", "start_at": 0.0, "end_at": 1.0, "embeds_scaling": "V only"}},
            "35": {"class_type": "CLIPVisionLoader", "inputs": {"clip_name": "x.safetensors"}},
            "36": {"class_type": "LoadImage", "inputs": {"image": "x.png", "upload": "image"}},
        }

    def test_valid_workflow_passes(self):
        self.assertEqual(opp.validate_workflow_shape(self._make_valid_workflow()), [])

    def test_missing_node_rejected(self):
        workflow = self._make_valid_workflow()
        del workflow["30"]
        reasons = opp.validate_workflow_shape(workflow)
        self.assertTrue(any("30" in r for r in reasons))

    def test_non_int_seed_rejected(self):
        workflow = self._make_valid_workflow()
        workflow["10"]["inputs"]["seed"] = "not-a-seed"
        reasons = opp.validate_workflow_shape(workflow)
        self.assertTrue(any("seed" in r for r in reasons))

    def test_bool_seed_rejected(self):
        # bool は int のサブクラスであるため明示的に除外する。
        workflow = self._make_valid_workflow()
        workflow["10"]["inputs"]["seed"] = True
        reasons = opp.validate_workflow_shape(workflow)
        self.assertTrue(any("seed" in r for r in reasons))

    def test_batch_size_not_one_rejected(self):
        workflow = self._make_valid_workflow()
        workflow["9"]["inputs"]["batch_size"] = 4
        reasons = opp.validate_workflow_shape(workflow)
        self.assertTrue(any("生成枚数" in r for r in reasons))

    def test_non_positive_width_rejected(self):
        workflow = self._make_valid_workflow()
        workflow["9"]["inputs"]["width"] = 0
        reasons = opp.validate_workflow_shape(workflow)
        self.assertTrue(any("width" in r for r in reasons))

    def test_negative_prompt_missing_required_concept_rejected(self):
        workflow = self._make_valid_workflow()
        workflow["8"]["inputs"]["text"] = "lowres, blurry"
        reasons = opp.validate_workflow_shape(workflow)
        self.assertTrue(any("negative prompt" in r for r in reasons))

    def test_negative_seed_rejected(self):
        # Codexレビュー指摘(Major)の回帰テスト: seed/steps/cfgは型チェックのみで
        # 範囲・有限性を検証していなかった。
        workflow = self._make_valid_workflow()
        workflow["10"]["inputs"]["seed"] = -5
        reasons = opp.validate_workflow_shape(workflow)
        self.assertTrue(any("seed" in r for r in reasons))

    def test_seed_zero_is_allowed(self):
        workflow = self._make_valid_workflow()
        workflow["10"]["inputs"]["seed"] = 0
        self.assertEqual(opp.validate_workflow_shape(workflow), [])

    def test_negative_steps_rejected(self):
        workflow = self._make_valid_workflow()
        workflow["10"]["inputs"]["steps"] = -5
        reasons = opp.validate_workflow_shape(workflow)
        self.assertTrue(any("steps" in r for r in reasons))

    def test_zero_steps_rejected(self):
        workflow = self._make_valid_workflow()
        workflow["10"]["inputs"]["steps"] = 0
        reasons = opp.validate_workflow_shape(workflow)
        self.assertTrue(any("steps" in r for r in reasons))

    def test_negative_cfg_rejected(self):
        workflow = self._make_valid_workflow()
        workflow["10"]["inputs"]["cfg"] = -5
        reasons = opp.validate_workflow_shape(workflow)
        self.assertTrue(any("cfg" in r for r in reasons))

    def test_zero_cfg_rejected(self):
        workflow = self._make_valid_workflow()
        workflow["10"]["inputs"]["cfg"] = 0
        reasons = opp.validate_workflow_shape(workflow)
        self.assertTrue(any("cfg" in r for r in reasons))

    def test_nan_cfg_rejected(self):
        workflow = self._make_valid_workflow()
        workflow["10"]["inputs"]["cfg"] = float("nan")
        reasons = opp.validate_workflow_shape(workflow)
        self.assertTrue(any("cfg" in r for r in reasons))

    def test_infinite_cfg_rejected(self):
        workflow = self._make_valid_workflow()
        workflow["10"]["inputs"]["cfg"] = float("inf")
        reasons = opp.validate_workflow_shape(workflow)
        self.assertTrue(any("cfg" in r for r in reasons))


class RunpodRequestDryRunTest(unittest.TestCase):
    def test_no_env_var_names_leak_secret_values(self):
        workflow = {"1": {"class_type": "CheckpointLoaderSimple", "inputs": {}}}
        config = {"filename_prefix": "x"}
        with mock.patch.dict("os.environ", {"RUNPOD_API_KEY": "sk-super-secret-value-12345"}):
            request = opp.build_runpod_request_dry_run(workflow, config)
            serialized = json.dumps(request, ensure_ascii=False)
            self.assertNotIn("sk-super-secret-value-12345", serialized)

    def test_check_runpod_env_vars_reports_presence_only(self):
        with mock.patch.dict("os.environ", {"RUNPOD_API_KEY": "sk-secret-value"}, clear=False):
            status = opp.check_runpod_env_vars()
        self.assertTrue(status["RUNPOD_API_KEY"])
        serialized = json.dumps(status, ensure_ascii=False)
        self.assertNotIn("sk-secret-value", serialized)

    def test_env_var_absent_reports_false(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            status = opp.check_runpod_env_vars()
        self.assertFalse(status["RUNPOD_API_KEY"])
        self.assertFalse(status["RUNPOD_ENDPOINT_URL"])


class LoadConfigTest(unittest.TestCase):
    def test_example_config_loads_and_strips_comment_key(self):
        config = opp.load_config(CONFIG_PATH)
        self.assertNotIn("_comment", config)
        for field in (
            "checkpoint_name", "clip_vision_name", "ipadapter_preset", "ipadapter_weight",
            "sampler_name", "scheduler", "steps", "cfg", "seed", "generation_width", "generation_height",
        ):
            self.assertIn(field, config)

    def test_missing_config_file_raises_pilot_error(self):
        with self.assertRaises(opp.PilotError):
            opp.load_config("/nonexistent/path/config.json")

    def test_missing_required_key_raises_pilot_error_not_keyerror(self):
        # Codexレビュー指摘(Minor)の回帰テスト: 必須キー欠落時にbare KeyErrorが
        # 送出されず、PilotErrorとして欠落キー名を含んで報告されること。
        config = opp.load_config(CONFIG_PATH)
        del config["checkpoint_name"]
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "config.json"
            path.write_text(json.dumps(config), encoding="utf-8")
            with self.assertRaises(opp.PilotError) as ctx:
                opp.load_config(str(path))
            self.assertIn("checkpoint_name", str(ctx.exception))

    def test_non_object_config_root_raises_pilot_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "config.json"
            path.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
            with self.assertRaises(opp.PilotError):
                opp.load_config(str(path))


class FivePanelTemplateGeometryTest(unittest.TestCase):
    def test_panel_one_geometry_matches_five_panel_template_json(self):
        template = opp.load_five_panel_template()
        geometry = opp.get_panel_geometry(template, 1)
        self.assertEqual(geometry["outer"], {"x": 30, "y": 30, "width": 1021, "height": 357})
        self.assertEqual(geometry["inner"], {"x": 36, "y": 36, "width": 1009, "height": 345})
        self.assertEqual(geometry["safe_area"], {"x": 61, "y": 61, "width": 959, "height": 295})

    def test_missing_panel_no_raises_pilot_error(self):
        template = opp.load_five_panel_template()
        with self.assertRaises(opp.PilotError):
            opp.get_panel_geometry(template, 99)


class LoadMangaSchemaTest(unittest.TestCase):
    def test_default_path_imports_successfully(self):
        module = opp.load_manga_schema()
        self.assertEqual(module.PACKET_VERSION, 2)

    def test_missing_news_game_translator_root_raises_pilot_error(self):
        with mock.patch.dict("os.environ", {"NEWS_GAME_TRANSLATOR_ROOT": "/nonexistent/ngt/root"}):
            with self.assertRaises(opp.PilotError):
                opp.load_manga_schema()

    def test_override_path_value_not_leaked_in_exception(self):
        # Codexレビュー指摘(Minor)の回帰テスト: NEWS_GAME_TRANSLATOR_ROOTの
        # 実際の値が例外メッセージへそのまま出力されないこと。
        secret_looking_path = "/definitely/nonexistent/ngt-secret-path"
        with mock.patch.dict("os.environ", {"NEWS_GAME_TRANSLATOR_ROOT": secret_looking_path}):
            with self.assertRaises(opp.PilotError) as ctx:
                opp.load_manga_schema()
            self.assertNotIn(secret_looking_path, str(ctx.exception))

    def test_switching_root_after_success_does_not_return_stale_module(self):
        # Codexレビュー指摘(Major)の回帰テスト: 1プロセス内で最初にデフォルト
        # rootで正常にロードした後、scripts/はあるがmanga_schema.pyが存在
        # しないrootへ切り替えて再度呼び出すと、sys.modulesキャッシュにより
        # 古いモジュールがサイレントに返っていた(修正前)。
        first = opp.load_manga_schema()
        self.assertEqual(first.PACKET_VERSION, 2)
        with tempfile.TemporaryDirectory() as tmp:
            (pathlib.Path(tmp) / "scripts").mkdir()
            with mock.patch.dict("os.environ", {"NEWS_GAME_TRANSLATOR_ROOT": tmp}):
                with self.assertRaises(opp.PilotError):
                    opp.load_manga_schema()

    def test_switching_between_two_valid_roots_does_not_reuse_stale_sibling_module(self):
        # 2回目のCodexレビュー指摘(Major)の回帰テスト: manga_schema.py本体は
        # importlib経由でキャッシュを回避するようになったが、以前はsys.path
        # へroot固有のscripts/を追加していたため、manga_schema.pyが同じ
        # scripts/内の別モジュールをimportする場合、そちらは通常のimport文
        # 経由でsys.modulesにモジュール名キャッシュされ、root切替後も古い
        # rootの依存モジュールがサイレントに使われ得た。現在はsys.path登録
        # 自体を行わないため、そのような依存importは明確な失敗になる
        # (サイレントな旧データ混在にはならない)ことを確認する。
        with tempfile.TemporaryDirectory() as root_a, tempfile.TemporaryDirectory() as root_b:
            for root, value in ((root_a, "A"), (root_b, "B")):
                scripts_dir = pathlib.Path(root) / "scripts"
                scripts_dir.mkdir()
                (scripts_dir / "schema_helper_for_cache_repro.py").write_text(
                    f'VALUE = "{value}"\n', encoding="utf-8"
                )
                (scripts_dir / "manga_schema.py").write_text(
                    "import schema_helper_for_cache_repro\n"
                    "PACKET_VERSION = 2\n"
                    "VALUE = schema_helper_for_cache_repro.VALUE\n",
                    encoding="utf-8",
                )

            with mock.patch.dict("os.environ", {"NEWS_GAME_TRANSLATOR_ROOT": root_a}):
                try:
                    opp.load_manga_schema()
                except opp.PilotError:
                    pass  # root_aの依存importが解決できない場合も許容する

            # root_b切替後、サイレントにroot_a側の依存モジュール("A")を
            # 使い回さないこと。読み込みが成功するならVALUEは"B"でなければ
            # ならず、"A"がサイレントに返るのは修正前の回帰状態を意味する。
            with mock.patch.dict("os.environ", {"NEWS_GAME_TRANSLATOR_ROOT": root_b}):
                try:
                    second = opp.load_manga_schema()
                except opp.PilotError:
                    second = None
            if second is not None:
                self.assertEqual(second.VALUE, "B")

    def test_override_runtime_exception_body_not_leaked_in_exception(self):
        # 2回目のCodexレビュー指摘(Minor)の回帰テスト: manga_schema.py自体の
        # 実行時例外(exec_module失敗)の本文にNEWS_GAME_TRANSLATOR_ROOTの
        # 値(__file__経由)が含まれていても、そのままPilotErrorへ埋め込まない。
        with tempfile.TemporaryDirectory() as root:
            scripts_dir = pathlib.Path(root) / "scripts"
            scripts_dir.mkdir()
            (scripts_dir / "manga_schema.py").write_text(
                "raise RuntimeError(__file__)\n", encoding="utf-8"
            )
            with mock.patch.dict("os.environ", {"NEWS_GAME_TRANSLATOR_ROOT": root}):
                with self.assertRaises(opp.PilotError) as ctx:
                    opp.load_manga_schema()
                self.assertNotIn(root, str(ctx.exception))


class LoadPacketTest(unittest.TestCase):
    def test_missing_file_raises_pilot_error(self):
        with self.assertRaises(opp.PilotError):
            opp.load_packet("/nonexistent/packet.json")

    def test_invalid_json_raises_pilot_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad_path = pathlib.Path(tmp) / "broken.json"
            bad_path.write_text("{not valid json", encoding="utf-8")
            with self.assertRaises(opp.PilotError):
                opp.load_packet(bad_path)

    def test_fixture_packet_loads(self):
        packet = opp.load_packet(FIXTURE_PATH)
        self.assertEqual(packet["packet_version"], 2)


class RunDryRunEndToEndTest(IsolatedReferenceImagesTestCase):
    """resolve_reference_image側だけ隔離し、他はfixture Packet・実正本
    config・実five_panel_template.jsonを使った統合的なdry-run確認。
    ネットワーク通信・GPU生成は一切発生しない。
    """

    def test_full_dry_run_succeeds_with_isolated_fixture(self):
        # 秘密情報が紛れ込んでいないことを、実際のダミー値がシリアライズ結果へ
        # 現れないことで確認する(「Authorization」という語自体は、実送信時に
        # ヘッダーへ別途設定する旨の説明文中に正当に現れるため、語の有無では
        # なく値の有無で判定する)。
        with mock.patch.dict(
            "os.environ",
            {"RUNPOD_API_KEY": "sk-super-secret-value-12345", "RUNPOD_ENDPOINT_URL": "https://secret-pod.example/prompt"},
        ):
            result = opp.run_dry_run(FIXTURE_PATH, panel_no=1, config_path=CONFIG_PATH, seed=42)
        self.assertEqual(result["performer_name"], "ハルト")
        self.assertEqual(result["performer_expression"], "surprise-weak")
        self.assertTrue(pathlib.Path(result["reference_image_path"]).is_file())
        self.assertEqual(result["panel_fit"]["final_size"], {"width": 1009, "height": 345})
        self.assertEqual(result["workflow"]["10"]["inputs"]["seed"], 42)
        self.assertEqual(result["workflow"]["9"]["inputs"]["batch_size"], 1)
        serialized = json.dumps(result, ensure_ascii=False)
        self.assertNotIn("sk-super-secret-value-12345", serialized)
        self.assertNotIn("secret-pod.example", serialized)

    def test_wrong_panel_no_fails_clearly(self):
        with self.assertRaises(opp.PilotError):
            opp.run_dry_run(FIXTURE_PATH, panel_no=2, config_path=CONFIG_PATH)

    def test_unsupported_character_rejected_before_processing(self):
        # Codexレビュー指摘(Minor)の回帰テスト: build_positive_prompt()の
        # 固定サフィックスはハルト専用のため、他キャラクターを指定した場合は
        # scope検証まで進む前に明確に拒否されなければならない。
        with self.assertRaises(opp.PilotError) as ctx:
            opp.run_dry_run(FIXTURE_PATH, panel_no=1, config_path=CONFIG_PATH, expected_character="ナツキ")
        self.assertIn("ハルト", str(ctx.exception))

    def test_malformed_packet_fails_clearly_not_crash(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad_path = pathlib.Path(tmp) / "bad_packet.json"
            bad_path.write_text(json.dumps({"panels": "not-a-list"}), encoding="utf-8")
            with self.assertRaises(opp.PilotError):
                opp.run_dry_run(bad_path, panel_no=1, config_path=CONFIG_PATH)

    def test_unresolvable_reference_image_fails_clearly(self):
        packet = load_fixture_packet()
        packet["panels"][0]["performers"][0]["reference_image"] = "haruto/joy-strong.png"
        packet["panels"][0]["performers"][0]["expression"] = "joy-strong"
        with tempfile.TemporaryDirectory() as tmp:
            packet_path = pathlib.Path(tmp) / "packet.json"
            packet_path.write_text(json.dumps(packet, ensure_ascii=False), encoding="utf-8")
            with self.assertRaises(opp.PilotError):
                opp.run_dry_run(packet_path, panel_no=1, config_path=CONFIG_PATH)


if __name__ == "__main__":
    unittest.main()
