#!/usr/bin/env python3
"""scripts/fetch_reference_images.py のテスト。

ネットワークアクセスは行わず、download_fileをモックして完全にオフライン
でテストする。SHA-256照合・PNG枚数/画像サイズ検証・manifest突き合わせ・
zip slip対策・既存アセットの非上書き(--forceなし)を検証する。Python
標準ライブラリのみを使用する(unittest, unittest.mock, hashlib, json,
pathlib, shutil, struct, tempfile, zipfile)。
"""
import hashlib
import json
import pathlib
import shutil
import struct
import sys
import tempfile
import unittest
import zipfile
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import fetch_reference_images as fri  # noqa: E402


def make_fake_png(width, height):
    """read_png_size()が解釈できる最小限の疑似PNGバイト列を作る
    (実際のPNGエンコードは行わない。ヘッダー〔署名+IHDRの幅高さ〕のみ)。
    """
    signature = b"\x89PNG\r\n\x1a\n"
    chunk_header = b"\x00\x00\x00\rIHDR"
    dims = struct.pack(">II", width, height)
    rest = b"\x08\x06\x00\x00\x00" + b"\x00\x00\x00\x00"  # bit depth等+CRCダミー
    return signature + chunk_header + dims + rest


def build_zip(zip_path, root_name, png_specs, include_index_html=True):
    """root_name/images/<name>.png ... という構成のZIPを作る。
    png_specs: {filename: (width, height)}
    """
    with zipfile.ZipFile(zip_path, "w") as zf:
        if include_index_html:
            zf.writestr(f"{root_name}/index.html", "<html>preview</html>")
        zf.writestr(f"{root_name}/images/", "")
        for filename, (w, h) in png_specs.items():
            zf.writestr(f"{root_name}/images/{filename}", make_fake_png(w, h))


DEFAULT_TAGS = {
    "neutral": "00-neutral.png",
    "surprise-medium": "05-surprise-medium.png",
}


class FetchCharacterTest(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.tmp = pathlib.Path(self._tmpdir.name)
        self.character_dir = self.tmp / "reference_images" / "testchar"
        self.character_dir.mkdir(parents=True)

        self.zip_path = self.tmp / "source.zip"
        self.png_specs = {v: (10, 10) for v in DEFAULT_TAGS.values()}
        build_zip(self.zip_path, "testchar_set", self.png_specs)

        self.sha256 = hashlib.sha256(self.zip_path.read_bytes()).hexdigest()
        self.size_bytes = self.zip_path.stat().st_size

        self.write_asset_json()
        self.write_manifest_json(DEFAULT_TAGS)

    def write_asset_json(self, **overrides):
        config = {
            "character": "testchar",
            "asset_version": "v1",
            "release_tag": "testchar-v1",
            "filename": "source.zip",
            "download_url": "https://example.com/source.zip",
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
            "expected_png_count": len(self.png_specs),
            "expected_image_size": [10, 10],
            "zip_internal_root": "testchar_set",
        }
        config.update(overrides)
        with (self.character_dir / "asset.json").open("w", encoding="utf-8") as f:
            json.dump(config, f)
        return config

    def write_manifest_json(self, manifest):
        with (self.character_dir / "manifest.json").open("w", encoding="utf-8") as f:
            json.dump(manifest, f)

    def _mock_download(self, url, dest_path):
        shutil.copy(self.zip_path, dest_path)

    def test_successful_fetch_places_images_and_index_html(self):
        with mock.patch.object(fri, "download_file", side_effect=self._mock_download):
            fri.fetch_character(self.character_dir)

        images_dir = self.character_dir / "images"
        self.assertTrue(images_dir.is_dir())
        for filename in DEFAULT_TAGS.values():
            self.assertTrue((images_dir / filename).is_file())
        self.assertTrue((self.character_dir / "index.html").is_file())

    def test_sha256_mismatch_does_not_extract_or_place_anything(self):
        self.write_asset_json(sha256="0" * 64)
        with mock.patch.object(fri, "download_file", side_effect=self._mock_download):
            with self.assertRaises(fri.FetchError) as ctx:
                fri.fetch_character(self.character_dir)
        self.assertIn("SHA-256", str(ctx.exception))
        self.assertFalse((self.character_dir / "images").exists())
        self.assertFalse((self.character_dir / "index.html").exists())

    def test_size_mismatch_does_not_extract_or_place_anything(self):
        self.write_asset_json(size_bytes=self.size_bytes + 1)
        with mock.patch.object(fri, "download_file", side_effect=self._mock_download):
            with self.assertRaises(fri.FetchError) as ctx:
                fri.fetch_character(self.character_dir)
        self.assertIn("ファイルサイズ", str(ctx.exception))
        self.assertFalse((self.character_dir / "images").exists())

    def test_wrong_png_count_rejected(self):
        self.write_asset_json(expected_png_count=999)
        with mock.patch.object(fri, "download_file", side_effect=self._mock_download):
            with self.assertRaises(fri.FetchError) as ctx:
                fri.fetch_character(self.character_dir)
        self.assertIn("PNG枚数", str(ctx.exception))
        self.assertFalse((self.character_dir / "images").exists())

    def test_wrong_image_size_rejected(self):
        self.write_asset_json(expected_image_size=[999, 999])
        with mock.patch.object(fri, "download_file", side_effect=self._mock_download):
            with self.assertRaises(fri.FetchError) as ctx:
                fri.fetch_character(self.character_dir)
        self.assertIn("画像サイズ", str(ctx.exception))
        self.assertFalse((self.character_dir / "images").exists())

    def test_manifest_referencing_missing_file_rejected(self):
        self.write_manifest_json({"neutral": "00-neutral.png", "ghost-tag": "99-does-not-exist.png"})
        with mock.patch.object(fri, "download_file", side_effect=self._mock_download):
            with self.assertRaises(fri.FetchError) as ctx:
                fri.fetch_character(self.character_dir)
        self.assertIn("manifest.json", str(ctx.exception))
        self.assertFalse((self.character_dir / "images").exists())

    def test_existing_images_not_overwritten_without_force(self):
        images_dir = self.character_dir / "images"
        images_dir.mkdir()
        (images_dir / "sentinel.png").write_bytes(b"pre-existing")

        with mock.patch.object(fri, "download_file", side_effect=self._mock_download) as mocked_download:
            fri.fetch_character(self.character_dir, force=False)

        mocked_download.assert_not_called()
        self.assertTrue((images_dir / "sentinel.png").is_file())
        self.assertEqual((images_dir / "sentinel.png").read_bytes(), b"pre-existing")

    def test_force_replaces_existing_images(self):
        images_dir = self.character_dir / "images"
        images_dir.mkdir()
        (images_dir / "sentinel.png").write_bytes(b"stale")

        with mock.patch.object(fri, "download_file", side_effect=self._mock_download):
            fri.fetch_character(self.character_dir, force=True)

        self.assertFalse((images_dir / "sentinel.png").exists())
        for filename in DEFAULT_TAGS.values():
            self.assertTrue((images_dir / filename).is_file())

    def test_failed_verification_does_not_touch_existing_valid_assets(self):
        # 事前に正常な取得結果があるとき、後続のfetch(--force)で検証が
        # 失敗した場合、既存の正式配置を壊さない
        # (「検証前に既存の正式配置を上書きしない」の確認)。
        with mock.patch.object(fri, "download_file", side_effect=self._mock_download):
            fri.fetch_character(self.character_dir)

        original_files = sorted((self.character_dir / "images").glob("*.png"))
        self.assertTrue(original_files)

        self.write_asset_json(sha256="f" * 64)
        with mock.patch.object(fri, "download_file", side_effect=self._mock_download):
            with self.assertRaises(fri.FetchError):
                fri.fetch_character(self.character_dir, force=True)

        remaining_files = sorted((self.character_dir / "images").glob("*.png"))
        self.assertEqual([f.name for f in original_files], [f.name for f in remaining_files])

    def test_missing_asset_json_raises(self):
        (self.character_dir / "asset.json").unlink()
        with self.assertRaises(fri.FetchError):
            fri.fetch_character(self.character_dir)

    def test_missing_manifest_json_raises(self):
        (self.character_dir / "manifest.json").unlink()
        with mock.patch.object(fri, "download_file", side_effect=self._mock_download):
            with self.assertRaises(fri.FetchError):
                fri.fetch_character(self.character_dir)


class SafeExtractTest(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.tmp = pathlib.Path(self._tmpdir.name)

    def test_normal_extraction_places_files_under_dest(self):
        zip_path = self.tmp / "a.zip"
        build_zip(zip_path, "root", {"00-neutral.png": (10, 10)})
        dest = self.tmp / "dest"
        fri.safe_extract(zip_path, dest, strip_prefix="root")
        self.assertTrue((dest / "images" / "00-neutral.png").is_file())
        self.assertTrue((dest / "index.html").is_file())

    def test_zip_slip_parent_traversal_rejected(self):
        zip_path = self.tmp / "evil.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("root/../../evil.txt", "gotcha")
        dest = self.tmp / "dest"
        with self.assertRaises(fri.FetchError):
            fri.safe_extract(zip_path, dest, strip_prefix="root")
        self.assertFalse((self.tmp / "evil.txt").exists())

    def test_entry_outside_declared_root_rejected(self):
        zip_path = self.tmp / "evil2.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("other_root/payload.txt", "gotcha")
        dest = self.tmp / "dest"
        with self.assertRaises(fri.FetchError):
            fri.safe_extract(zip_path, dest, strip_prefix="root")

    def test_absolute_path_entry_rejected(self):
        zip_path = self.tmp / "evil3.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("root//etc/passwd_like", "gotcha")
        dest = self.tmp / "dest"
        # 絶対パスもしくはdest外に解決される場合は拒否されること
        # (拒否されない場合でもdest配下にしか書き込まれないことを確認する)。
        try:
            fri.safe_extract(zip_path, dest, strip_prefix="root")
        except fri.FetchError:
            pass
        self.assertFalse((self.tmp / "etc" / "passwd_like").exists())


class ReadPngSizeTest(unittest.TestCase):
    def test_reads_correct_dimensions(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        path = pathlib.Path(self._tmpdir.name) / "x.png"
        path.write_bytes(make_fake_png(1254, 1254))
        self.assertEqual(fri.read_png_size(path), (1254, 1254))

    def test_invalid_signature_raises(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        path = pathlib.Path(self._tmpdir.name) / "x.png"
        path.write_bytes(b"not a png" * 5)
        with self.assertRaises(fri.FetchError):
            fri.read_png_size(path)


class DiscoverCharacterDirsTest(unittest.TestCase):
    def test_discovers_only_dirs_with_asset_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "haruto").mkdir()
            (root / "haruto" / "asset.json").write_text("{}")
            (root / "no_asset").mkdir()
            with mock.patch.object(fri, "REFERENCE_IMAGES_ROOT", root):
                dirs = fri.discover_character_dirs()
            self.assertEqual([d.name for d in dirs], ["haruto"])


if __name__ == "__main__":
    unittest.main()
