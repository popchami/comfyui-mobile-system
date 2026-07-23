#!/usr/bin/env python3
"""profiles/sdxl/isekai_nihon_manga/five_panel_template.json(5コマテンプレート
座標の数値正本)の検証。

- 完成画像全体(1080×1920)・枠線6px・コマ間隔19pxの確認
- 5コマ全ての外枠・内側・安全領域座標が仕様どおりであることの確認
- 安全領域が対応する内側領域へ完全に収まること、各コマがキャンバス外へ
  出ないことの確認
- five_panel_template.md が five_panel_template.json から生成した内容と
  一致すること(数値の不一致を防ぐドリフト検出)
"""
import json
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEMPLATE_JSON_PATH = ROOT / "profiles" / "sdxl" / "isekai_nihon_manga" / "five_panel_template.json"
TEMPLATE_MD_PATH = ROOT / "profiles" / "sdxl" / "isekai_nihon_manga" / "five_panel_template.md"

sys.path.insert(0, str(ROOT / "scripts"))
import generate_five_panel_template_doc as gen  # noqa: E402

EXPECTED_OUTER = {
    1: {"x": 30, "y": 30, "width": 1021, "height": 357},
    2: {"x": 30, "y": 406, "width": 1021, "height": 357},
    3: {"x": 30, "y": 782, "width": 1021, "height": 357},
    4: {"x": 30, "y": 1158, "width": 1021, "height": 357},
    5: {"x": 30, "y": 1534, "width": 1021, "height": 357},
}
EXPECTED_INNER = {
    1: {"x": 36, "y": 36, "width": 1009, "height": 345},
    2: {"x": 36, "y": 412, "width": 1009, "height": 345},
    3: {"x": 36, "y": 788, "width": 1009, "height": 345},
    4: {"x": 36, "y": 1164, "width": 1009, "height": 345},
    5: {"x": 36, "y": 1540, "width": 1009, "height": 345},
}
EXPECTED_SAFE_AREA = {
    1: {"x": 61, "y": 61, "width": 959, "height": 295},
    2: {"x": 61, "y": 437, "width": 959, "height": 295},
    3: {"x": 61, "y": 813, "width": 959, "height": 295},
    4: {"x": 61, "y": 1189, "width": 959, "height": 295},
    5: {"x": 61, "y": 1565, "width": 959, "height": 295},
}


def load_template():
    with TEMPLATE_JSON_PATH.open(encoding="utf-8") as f:
        return json.load(f)


class CanvasTest(unittest.TestCase):
    def test_canvas_is_1080x1920(self):
        data = load_template()
        self.assertEqual(data["canvas"]["width"], 1080)
        self.assertEqual(data["canvas"]["height"], 1920)

    def test_border_is_6px_black(self):
        data = load_template()
        self.assertEqual(data["border"]["width_px"], 6)
        self.assertEqual(data["border"]["color"], "black")

    def test_panel_gap_is_19px(self):
        data = load_template()
        self.assertEqual(data["panel_gap_px"], 19)

    def test_panel_count_is_5(self):
        data = load_template()
        self.assertEqual(data["panel_count"], 5)
        self.assertEqual(len(data["panels"]), 5)


class PanelCoordinatesTest(unittest.TestCase):
    def test_outer_coordinates_match_spec(self):
        data = load_template()
        for panel in data["panels"]:
            with self.subTest(panel_no=panel["panel_no"]):
                self.assertEqual(panel["outer"], EXPECTED_OUTER[panel["panel_no"]])

    def test_inner_coordinates_match_spec(self):
        data = load_template()
        for panel in data["panels"]:
            with self.subTest(panel_no=panel["panel_no"]):
                self.assertEqual(panel["inner"], EXPECTED_INNER[panel["panel_no"]])

    def test_safe_area_coordinates_match_spec(self):
        data = load_template()
        for panel in data["panels"]:
            with self.subTest(panel_no=panel["panel_no"]):
                self.assertEqual(panel["safe_area"], EXPECTED_SAFE_AREA[panel["panel_no"]])

    def test_gap_between_consecutive_panels_is_19px(self):
        data = load_template()
        panels = sorted(data["panels"], key=lambda p: p["panel_no"])
        for prev, cur in zip(panels, panels[1:]):
            prev_bottom = prev["outer"]["y"] + prev["outer"]["height"]
            gap = cur["outer"]["y"] - prev_bottom
            with self.subTest(panel_no=cur["panel_no"]):
                self.assertEqual(gap, data["panel_gap_px"])

    def test_inner_is_border_width_inside_outer(self):
        data = load_template()
        border = data["border"]["width_px"]
        for panel in data["panels"]:
            outer = panel["outer"]
            inner = panel["inner"]
            with self.subTest(panel_no=panel["panel_no"]):
                self.assertEqual(inner["x"], outer["x"] + border)
                self.assertEqual(inner["y"], outer["y"] + border)
                self.assertEqual(inner["width"], outer["width"] - 2 * border)
                self.assertEqual(inner["height"], outer["height"] - 2 * border)


class SafeAreaContainmentTest(unittest.TestCase):
    def test_safe_area_fits_entirely_inside_inner_area(self):
        data = load_template()
        for panel in data["panels"]:
            inner = panel["inner"]
            safe = panel["safe_area"]
            with self.subTest(panel_no=panel["panel_no"]):
                self.assertGreaterEqual(safe["x"], inner["x"])
                self.assertGreaterEqual(safe["y"], inner["y"])
                self.assertLessEqual(safe["x"] + safe["width"], inner["x"] + inner["width"])
                self.assertLessEqual(safe["y"] + safe["height"], inner["y"] + inner["height"])

    def test_no_panel_exceeds_canvas_bounds(self):
        data = load_template()
        canvas = data["canvas"]
        for panel in data["panels"]:
            outer = panel["outer"]
            with self.subTest(panel_no=panel["panel_no"]):
                self.assertGreaterEqual(outer["x"], 0)
                self.assertGreaterEqual(outer["y"], 0)
                self.assertLessEqual(outer["x"] + outer["width"], canvas["width"])
                self.assertLessEqual(outer["y"] + outer["height"], canvas["height"])


class ScribePanelLayoutTest(unittest.TestCase):
    def test_layout_id_matches_packet_schema_constant(self):
        data = load_template()
        self.assertEqual(data["scribe_panel_layout"]["layout_id"], "scribe-left_note-right")

    def test_scribe_and_note_fractions_are_within_safe_area(self):
        data = load_template()
        layout = data["scribe_panel_layout"]
        total = layout["scribe_area_fraction_of_safe_area"] + layout["note_area_fraction_of_safe_area"]
        self.assertLessEqual(total, 1.0)


class MarkdownGenerationDriftTest(unittest.TestCase):
    """five_panel_template.md が five_panel_template.json から生成した内容と
    一致することを確認する(数値の正本はJSON、Markdownは手書きしない)。
    """

    def test_committed_markdown_matches_generated_output(self):
        data = load_template()
        generated = gen.generate_markdown(data)
        self.assertTrue(TEMPLATE_MD_PATH.is_file(), "five_panel_template.mdが存在しません")
        actual = TEMPLATE_MD_PATH.read_text(encoding="utf-8")
        self.assertEqual(actual, generated)

    def test_generator_check_mode_reports_ok(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "generate_five_panel_template_doc.py"), "--check"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
