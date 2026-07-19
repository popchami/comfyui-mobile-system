#!/usr/bin/env python3
"""scripts/resolve_reference_image.py のテスト。

Manga News Packetのreference_image(論理ID、例: haruto/surprise-medium.png)
を、manifest.jsonを介して実ファイルへ解決するロジックを検証する。Python
標準ライブラリのみを使用する(unittest, unittest.mock, json, pathlib,
tempfile)。
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
    def test_valid_format_parsed(self):
        character, expression = rri.parse_reference_image("haruto/surprise-medium.png")
        self.assertEqual(character, "haruto")
        self.assertEqual(expression, "surprise-medium")

    def test_missing_slash_rejected(self):
        with self.assertRaises(rri.ResolveError):
            rri.parse_reference_image("haruto-surprise-medium.png")

    def test_non_png_extension_rejected(self):
        with self.assertRaises(rri.ResolveError):
            rri.parse_reference_image("haruto/surprise-medium.jpg")

    def test_reserved_underscore_expression_rejected(self):
        # manifest.jsonの予約キー(例: "_comment")を表情タグとして解決
        # できてしまう問題の回帰テスト(Codexレビュー指摘)。
        with self.assertRaises(rri.ResolveError):
            rri.parse_reference_image("haruto/_comment.png")

    def test_reserved_underscore_character_rejected(self):
        with self.assertRaises(rri.ResolveError):
            rri.parse_reference_image("_secret/neutral.png")

    def test_path_traversal_rejected(self):
        for bad in [
            "../etc/passwd.png",
            "haruto/../../../etc/passwd.png",
            "haruto//surprise-medium.png",
            "haruto/sub/dir.png",
            "",
            None,
        ]:
            with self.subTest(bad=bad):
                with self.assertRaises(rri.ResolveError):
                    rri.parse_reference_image(bad)


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

    def test_resolves_without_requiring_file_when_allowed(self):
        path = rri.resolve_reference_image("haruto/surprise-medium.png", require_file_exists=False)
        self.assertEqual(path, self.character_dir / "images" / "05-surprise-medium.png")

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
        # manifest.jsonに実在する"_comment"キーを、表情タグとして解決
        # できてしまわないことを確認する(Codexレビュー指摘の回帰テスト)。
        # parse_reference_imageの時点で拒否されるため、resolve_reference_
        # imageまで到達してもmanifest.get("_comment")の説明文字列が
        # 画像パスとして返らないことを保証する。
        with self.assertRaises(rri.ResolveError):
            rri.resolve_reference_image("haruto/_comment.png", require_file_exists=False)

    def test_unknown_character_raises(self):
        with self.assertRaises(rri.ResolveError):
            rri.resolve_reference_image("nonexistent_character/neutral.png", require_file_exists=False)

    def test_invalid_reference_image_format_raises(self):
        with self.assertRaises(rri.ResolveError):
            rri.resolve_reference_image("not-a-valid-reference", require_file_exists=False)


if __name__ == "__main__":
    unittest.main()
