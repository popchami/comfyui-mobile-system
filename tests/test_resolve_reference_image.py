#!/usr/bin/env python3
"""scripts/resolve_reference_image.py のテスト。

Manga News Packetのreference_image(論理ID)を、manifest.jsonを介して
実ファイルへ解決するロジックを検証する。2形式(表情の`<character>/<tag>.png`
既存互換形式、および`<character>/<category>/<tag>.png`の新形式)、未知の
category・予約語・ディレクトリトラバーサルの拒否を含む。Python標準
ライブラリのみを使用する。
"""
import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import resolve_reference_image as rri  # noqa: E402


class ParseReferenceImageTest(unittest.TestCase):
    def test_bare_two_segment_form_defaults_to_expressions(self):
        character, category, tag = rri.parse_reference_image("haruto/surprise-medium.png")
        self.assertEqual(character, "haruto")
        self.assertEqual(category, "expressions")
        self.assertEqual(tag, "surprise-medium")

    def test_explicit_category_form(self):
        character, category, tag = rri.parse_reference_image("haruto/turnaround/front.png")
        self.assertEqual(character, "haruto")
        self.assertEqual(category, "turnaround")
        self.assertEqual(tag, "front")

    def test_explicit_expressions_category_is_equivalent_to_bare_form(self):
        character, category, tag = rri.parse_reference_image("haruto/expressions/surprise-medium.png")
        self.assertEqual((character, category, tag), ("haruto", "expressions", "surprise-medium"))

    def test_equipment_category(self):
        character, category, tag = rri.parse_reference_image("natsuki/equipment/mitsugake-right.png")
        self.assertEqual((character, category, tag), ("natsuki", "equipment", "mitsugake-right"))

    def test_missing_slash_rejected(self):
        with self.assertRaises(rri.ResolveError):
            rri.parse_reference_image("haruto-surprise-medium.png")

    def test_non_png_extension_rejected(self):
        with self.assertRaises(rri.ResolveError):
            rri.parse_reference_image("haruto/surprise-medium.jpg")

    def test_reserved_underscore_expression_rejected(self):
        with self.assertRaises(rri.ResolveError):
            rri.parse_reference_image("haruto/_comment.png")

    def test_reserved_underscore_character_rejected(self):
        with self.assertRaises(rri.ResolveError):
            rri.parse_reference_image("_secret/neutral.png")

    def test_reserved_underscore_category_rejected(self):
        with self.assertRaises(rri.ResolveError):
            rri.parse_reference_image("haruto/_secret/front.png")

    def test_unknown_category_rejected(self):
        with self.assertRaises(rri.ResolveError):
            rri.parse_reference_image("haruto/poses/front.png")

    def test_path_traversal_rejected(self):
        for bad in [
            "../etc/passwd.png",
            "haruto/../../../etc/passwd.png",
            "haruto//surprise-medium.png",
            "haruto/sub/dir/tag.png",
            "",
            None,
        ]:
            with self.subTest(bad=bad):
                with self.assertRaises(rri.ResolveError):
                    rri.parse_reference_image(bad)

    def test_dot_only_character_segment_rejected(self):
        # character/categoryはそのままファイルシステムパスへ使われるため、
        # ".."単体がセグメントとして通ってしまうとトラバーサルにつながる。
        # 文字クラス自体は"."を許可するため、別途明示的に拒否する。
        with self.assertRaises(rri.ResolveError):
            rri.parse_reference_image("../neutral.png")

    def test_dot_only_tag_segment_rejected(self):
        with self.assertRaises(rri.ResolveError):
            rri.parse_reference_image("haruto/...png")

    def test_dot_only_category_segment_looks_like_unknown_category(self):
        # ".."がcategory位置に来た場合、既知category集合にも含まれないため
        # 未知category判定でも拒否されるが、念のためドット専用チェックが
        # 先に効くことを確認する(防御多重化)。
        with self.assertRaises(rri.ResolveError):
            rri.parse_reference_image("haruto/../front.png")


class ResolveReferenceImageTest(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.root = pathlib.Path(self._tmpdir.name)
        self._patcher = mock.patch.object(rri, "REFERENCE_IMAGES_ROOT", self.root)
        self._patcher.start()
        self.addCleanup(self._patcher.stop)

        self.character_dir = self.root / "haruto"
        self.character_dir.mkdir(parents=True)
        with (self.character_dir / "manifest.json").open("w", encoding="utf-8") as f:
            json.dump(
                {
                    "_comment": "これはドキュメント用の文字列であり、実ファイル名ではない",
                    "neutral": "00-neutral.png",
                    "surprise-medium": "05-surprise-medium.png",
                },
                f,
            )
        (self.character_dir / "turnaround").mkdir()
        with (self.character_dir / "turnaround" / "manifest.json").open("w", encoding="utf-8") as f:
            json.dump({"front": "00-front.png", "left-profile": "01-left-facing-profile.png"}, f)

    def test_resolves_expressions_without_requiring_file_when_allowed(self):
        path = rri.resolve_reference_image("haruto/surprise-medium.png", require_file_exists=False)
        self.assertEqual(path, self.character_dir / "images" / "05-surprise-medium.png")

    def test_resolves_turnaround_without_requiring_file_when_allowed(self):
        path = rri.resolve_reference_image("haruto/turnaround/front.png", require_file_exists=False)
        self.assertEqual(path, self.character_dir / "turnaround" / "images" / "00-front.png")

    def test_turnaround_naming_variation_absorbed_by_manifest(self):
        # 実ファイル名の表記揺れ(left-facing-profile)は論理ID
        # (left-profile)とは独立し、manifestが吸収する。
        path = rri.resolve_reference_image("haruto/turnaround/left-profile.png", require_file_exists=False)
        self.assertEqual(
            path, self.character_dir / "turnaround" / "images" / "01-left-facing-profile.png"
        )

    def test_missing_actual_file_raises_when_required(self):
        with self.assertRaises(rri.ResolveError):
            rri.resolve_reference_image("haruto/surprise-medium.png", require_file_exists=True)

    def test_resolves_successfully_when_file_exists(self):
        images_dir = self.character_dir / "images"
        images_dir.mkdir()
        (images_dir / "05-surprise-medium.png").write_bytes(b"fake-png-bytes")

        path = rri.resolve_reference_image("haruto/surprise-medium.png")
        self.assertEqual(path, images_dir / "05-surprise-medium.png")
        self.assertTrue(path.is_file())

    def test_unknown_expression_tag_raises(self):
        with self.assertRaises(rri.ResolveError):
            rri.resolve_reference_image("haruto/nonexistent-tag.png", require_file_exists=False)

    def test_manifest_comment_key_not_resolvable_as_expression(self):
        with self.assertRaises(rri.ResolveError):
            rri.resolve_reference_image("haruto/_comment.png", require_file_exists=False)

    def test_unknown_character_raises(self):
        with self.assertRaises(rri.ResolveError):
            rri.resolve_reference_image("nonexistent_character/neutral.png", require_file_exists=False)

    def test_invalid_reference_image_format_raises(self):
        with self.assertRaises(rri.ResolveError):
            rri.resolve_reference_image("not-a-valid-reference", require_file_exists=False)

    def test_unknown_tag_in_turnaround_category_raises(self):
        with self.assertRaises(rri.ResolveError):
            rri.resolve_reference_image("haruto/turnaround/diagonal.png", require_file_exists=False)


class NatsukiEquipmentResolveTest(unittest.TestCase):
    """ナツキ装備カテゴリ(2論理ID)の解決を検証する。"""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.root = pathlib.Path(self._tmpdir.name)
        self._patcher = mock.patch.object(rri, "REFERENCE_IMAGES_ROOT", self.root)
        self._patcher.start()
        self.addCleanup(self._patcher.stop)

        self.character_dir = self.root / "natsuki"
        (self.character_dir / "equipment").mkdir(parents=True)
        with (self.character_dir / "equipment" / "manifest.json").open("w", encoding="utf-8") as f:
            json.dump(
                {
                    "crest-hariyumi-himawari": "crest-hariyumi-himawari.png",
                    "mitsugake-right": "mitsugake-right.png",
                },
                f,
            )

    def test_both_equipment_logical_ids_resolve(self):
        path1 = rri.resolve_reference_image(
            "natsuki/equipment/crest-hariyumi-himawari.png", require_file_exists=False
        )
        self.assertEqual(
            path1, self.character_dir / "equipment" / "images" / "crest-hariyumi-himawari.png"
        )

        path2 = rri.resolve_reference_image(
            "natsuki/equipment/mitsugake-right.png", require_file_exists=False
        )
        self.assertEqual(path2, self.character_dir / "equipment" / "images" / "mitsugake-right.png")


class NatsukiExpressionsSameTagSetAsHarutoTest(unittest.TestCase):
    """ナツキの表情タグ集合がハルトと同一であることを確認する
    (「natsuki表情31タグがハルトと同じタグ集合で解決できる」)。
    """

    def test_tag_sets_match(self):
        haruto_manifest_path = (
            ROOT
            / "profiles"
            / "sdxl"
            / "isekai_nihon_manga"
            / "reference_images"
            / "haruto"
            / "manifest.json"
        )
        natsuki_manifest_path = (
            ROOT
            / "profiles"
            / "sdxl"
            / "isekai_nihon_manga"
            / "reference_images"
            / "natsuki"
            / "manifest.json"
        )
        with haruto_manifest_path.open(encoding="utf-8") as f:
            haruto_tags = {k for k in json.load(f) if not k.startswith("_")}
        with natsuki_manifest_path.open(encoding="utf-8") as f:
            natsuki_tags = {k for k in json.load(f) if not k.startswith("_")}

        self.assertEqual(len(haruto_tags), 31)
        self.assertEqual(haruto_tags, natsuki_tags)


if __name__ == "__main__":
    unittest.main()
