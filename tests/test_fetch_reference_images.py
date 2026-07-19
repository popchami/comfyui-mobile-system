#!/usr/bin/env python3
"""scripts/fetch_reference_images.py のテスト。

1キャラクターが複数package(Release ZIP)を持てること、1つのpackageが
複数category(expressions/turnaround/equipment)を持てること、旧形式
asset.jsonとの後方互換、category間の配置先衝突検出、ファイルごとの
画像サイズ検証、zip slip・重複パス対策、_atomic_replace()の安全性、
_character_lock()による排他制御を検証する。ネットワークアクセスは行わず、
download_fileをモックして完全にオフラインでテストする。Python標準
ライブラリのみを使用する。
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


def build_zip(zip_path, root_name, subdirs, include_index_html=True):
    """root_name/<subdir>/<name>.png ... という構成のZIPを作る。
    subdirs: {subdir_name: {filename: (width, height)}}
    """
    with zipfile.ZipFile(zip_path, "w") as zf:
        if include_index_html:
            zf.writestr(f"{root_name}/index.html", "<html>preview</html>")
        for subdir, png_specs in subdirs.items():
            zf.writestr(f"{root_name}/{subdir}/", "")
            for filename, (w, h) in png_specs.items():
                zf.writestr(f"{root_name}/{subdir}/{filename}", make_fake_png(w, h))


DEFAULT_EXPR_TAGS = {
    "neutral": "00-neutral.png",
    "surprise-medium": "05-surprise-medium.png",
}


# ---------------------------------------------------------------------------
# safe_extract / read_png_size / _atomic_replace / _character_lock
# (既存互換の基盤部分。挙動は変更していない)
# ---------------------------------------------------------------------------

class SafeExtractTest(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.tmp = pathlib.Path(self._tmpdir.name)

    def test_normal_extraction_places_files_under_dest(self):
        zip_path = self.tmp / "a.zip"
        build_zip(zip_path, "root", {"images": {"00-neutral.png": (10, 10)}})
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
        try:
            fri.safe_extract(zip_path, dest, strip_prefix="root")
        except fri.FetchError:
            pass
        self.assertFalse((self.tmp / "etc" / "passwd_like").exists())

    def test_duplicate_target_path_rejected(self):
        # 異なるZIPエントリ名が、正規化後に同じ展開先パスを指す場合を
        # 拒否する(重複パス対策)。
        zip_path = self.tmp / "dup.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("root/images/00-neutral.png", make_fake_png(10, 10))
            zf.writestr("root/images/./00-neutral.png", make_fake_png(10, 10))
        dest = self.tmp / "dest"
        with self.assertRaises(fri.FetchError):
            fri.safe_extract(zip_path, dest, strip_prefix="root")


class ReadPngSizeTest(unittest.TestCase):
    def test_reads_correct_dimensions(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "x.png"
            path.write_bytes(make_fake_png(1254, 1254))
            self.assertEqual(fri.read_png_size(path), (1254, 1254))

    def test_invalid_signature_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "x.png"
            path.write_bytes(b"not a png" * 5)
            with self.assertRaises(fri.FetchError):
                fri.read_png_size(path)


class AtomicReplaceTest(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.root = pathlib.Path(self._tmpdir.name)

    def test_replaces_existing_directory_and_leaves_no_backup(self):
        final = self.root / "images"
        final.mkdir()
        (final / "old.png").write_bytes(b"old")

        new = self.root / "images.new"
        new.mkdir()
        (new / "new.png").write_bytes(b"new")

        fri._atomic_replace(new, final)

        self.assertFalse((final / "old.png").exists())
        self.assertTrue((final / "new.png").is_file())
        self.assertFalse(new.exists())
        self.assertEqual(list(self.root.glob("images.old-*")), [])

    def test_places_new_directory_when_no_existing_final(self):
        final = self.root / "images"
        new = self.root / "images.new"
        new.mkdir()
        (new / "new.png").write_bytes(b"new")

        fri._atomic_replace(new, final)

        self.assertTrue((final / "new.png").is_file())

    def test_replaces_existing_file(self):
        final = self.root / "index.html"
        final.write_text("old")
        new = self.root / "index.html.new"
        new.write_text("new")

        fri._atomic_replace(new, final)

        self.assertEqual(final.read_text(), "new")

    def test_rename_failure_restores_original_content(self):
        final = self.root / "images"
        final.mkdir()
        (final / "old.png").write_bytes(b"old")

        new = self.root / "images.new"
        new.mkdir()
        (new / "new.png").write_bytes(b"new")

        original_rename = pathlib.Path.rename

        def flaky_rename(self_path, target):
            if self_path == new and pathlib.Path(target) == final:
                raise OSError("simulated rename failure")
            return original_rename(self_path, target)

        with mock.patch.object(pathlib.Path, "rename", flaky_rename):
            with self.assertRaises(OSError):
                fri._atomic_replace(new, final)

        self.assertTrue((final / "old.png").is_file())
        self.assertEqual((final / "old.png").read_bytes(), b"old")
        self.assertEqual(list(self.root.glob("images.old-*")), [])

    def test_stale_backup_from_previous_crash_is_not_deleted(self):
        final = self.root / "images"
        final.mkdir()
        (final / "current.png").write_bytes(b"current")

        stale_backup = self.root / "images.old-99999-deadbeef"
        stale_backup.mkdir()
        (stale_backup / "crashed-run.png").write_bytes(b"from a previous crashed run")

        new = self.root / "images.new"
        new.mkdir()
        (new / "new.png").write_bytes(b"new")

        fri._atomic_replace(new, final)

        self.assertTrue((final / "new.png").is_file())
        self.assertTrue(stale_backup.is_dir())
        self.assertTrue((stale_backup / "crashed-run.png").is_file())


class CharacterLockTest(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.character_dir = pathlib.Path(self._tmpdir.name) / "haruto"

    def test_lock_file_created(self):
        with fri._character_lock(self.character_dir):
            pass
        self.assertTrue((self.character_dir / ".fetch.lock").is_file())

    def test_lock_serializes_concurrent_access(self):
        import threading
        import time

        order = []
        first_entered = threading.Event()

        def first():
            with fri._character_lock(self.character_dir):
                order.append("first-enter")
                first_entered.set()
                time.sleep(0.2)
                order.append("first-exit")

        def second():
            first_entered.wait(timeout=5)
            with fri._character_lock(self.character_dir):
                order.append("second-enter")

        t1 = threading.Thread(target=first)
        t2 = threading.Thread(target=second)
        t1.start()
        t2.start()
        t1.join(timeout=5)
        t2.join(timeout=5)

        self.assertEqual(order, ["first-enter", "first-exit", "second-enter"])


class DiscoverCharacterDirsTest(unittest.TestCase):
    def test_discovers_dirs_with_asset_json_or_packages_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "haruto").mkdir()
            (root / "haruto" / "asset.json").write_text("{}")
            (root / "natsuki").mkdir()
            (root / "natsuki" / "packages.json").write_text("{}")
            (root / "no_config").mkdir()
            with mock.patch.object(fri, "REFERENCE_IMAGES_ROOT", root):
                dirs = fri.discover_character_dirs()
            self.assertEqual(sorted(d.name for d in dirs), ["haruto", "natsuki"])

    def test_dir_with_both_files_listed_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "haruto").mkdir()
            (root / "haruto" / "asset.json").write_text("{}")
            (root / "haruto" / "packages.json").write_text("{}")
            with mock.patch.object(fri, "REFERENCE_IMAGES_ROOT", root):
                dirs = fri.discover_character_dirs()
            self.assertEqual([d.name for d in dirs], ["haruto"])


# ---------------------------------------------------------------------------
# package/category 設定の読み込み(新機能)
# ---------------------------------------------------------------------------

def make_legacy_asset_json(**overrides):
    config = {
        "character": "haruto",
        "asset_version": "v2-clean",
        "release_tag": "haruto-expression-set-v2",
        "filename": "haruto_expression_set_v2_clean.zip",
        "download_url": "https://example.com/haruto_expression_set_v2_clean.zip",
        "sha256": "a" * 64,
        "size_bytes": 123,
        "expected_png_count": 31,
        "expected_image_size": [1254, 1254],
        "zip_internal_root": "haruto_expression_set",
    }
    config.update(overrides)
    return config


class NormalizeLegacyAssetJsonTest(unittest.TestCase):
    def test_normalizes_to_single_expressions_category_package(self):
        config = make_legacy_asset_json()
        package = fri._normalize_legacy_asset_json(config)

        self.assertEqual(package["release_tag"], config["release_tag"])
        self.assertEqual(package["download_url"], config["download_url"])
        self.assertEqual(package["sha256"], config["sha256"])
        self.assertEqual(package["size_bytes"], config["size_bytes"])
        self.assertEqual(package["zip_internal_root"], config["zip_internal_root"])
        self.assertEqual(len(package["categories"]), 1)
        category = package["categories"][0]
        self.assertEqual(category["name"], "expressions")
        self.assertEqual(category["zip_subdir"], "images")
        self.assertEqual(category["place_to"], "images")
        self.assertEqual(category["manifest"], "manifest.json")
        self.assertEqual(category["expected_png_count"], 31)
        self.assertEqual(category["expected_image_size"], [1254, 1254])

    def test_missing_required_field_raises(self):
        config = make_legacy_asset_json()
        del config["sha256"]
        with self.assertRaises(fri.FetchError):
            fri._normalize_legacy_asset_json(config)


class LoadCharacterPackagesTest(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.character_dir = pathlib.Path(self._tmpdir.name) / "haruto"
        self.character_dir.mkdir(parents=True)

    def write_json(self, relpath, data):
        path = self.character_dir / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f)

    def test_legacy_only_produces_one_package(self):
        self.write_json("asset.json", make_legacy_asset_json())
        packages = fri.load_character_packages(self.character_dir)
        self.assertEqual(len(packages), 1)
        self.assertEqual(packages[0]["categories"][0]["name"], "expressions")

    def test_packages_json_only(self):
        self.write_json(
            "packages.json",
            {
                "packages": [
                    {
                        "package_id": "turnaround-v1",
                        "release_tag": "haruto-turnaround-v1",
                        "filename": "haruto_turnaround.zip",
                        "download_url": "https://example.com/t.zip",
                        "sha256": "b" * 64,
                        "size_bytes": 456,
                        "zip_internal_root": "haruto_turnaround",
                        "categories": [
                            {
                                "name": "turnaround",
                                "zip_subdir": "images",
                                "place_to": "turnaround/images",
                                "manifest": "turnaround/manifest.json",
                                "expected_png_count": 4,
                                "expected_image_size": [1024, 1536],
                            }
                        ],
                    }
                ]
            },
        )
        packages = fri.load_character_packages(self.character_dir)
        self.assertEqual(len(packages), 1)
        self.assertEqual(packages[0]["package_id"], "turnaround-v1")

    def test_legacy_and_packages_json_combined(self):
        self.write_json("asset.json", make_legacy_asset_json())
        self.write_json(
            "packages.json",
            {
                "packages": [
                    {
                        "package_id": "turnaround-v1",
                        "release_tag": "haruto-turnaround-v1",
                        "filename": "haruto_turnaround.zip",
                        "download_url": "https://example.com/t.zip",
                        "sha256": "b" * 64,
                        "size_bytes": 456,
                        "zip_internal_root": "haruto_turnaround",
                        "categories": [
                            {
                                "name": "turnaround",
                                "zip_subdir": "images",
                                "place_to": "turnaround/images",
                                "manifest": "turnaround/manifest.json",
                                "expected_png_count": 4,
                                "expected_image_size": [1024, 1536],
                            }
                        ],
                    }
                ]
            },
        )
        packages = fri.load_character_packages(self.character_dir)
        self.assertEqual(len(packages), 2)
        names = sorted(c["name"] for p in packages for c in p["categories"])
        self.assertEqual(names, ["expressions", "turnaround"])

    def test_neither_file_present_raises(self):
        with self.assertRaises(fri.FetchError):
            fri.load_character_packages(self.character_dir)

    def test_unknown_category_name_rejected(self):
        self.write_json(
            "packages.json",
            {
                "packages": [
                    {
                        "package_id": "p1",
                        "release_tag": "r1",
                        "filename": "f.zip",
                        "download_url": "https://example.com/f.zip",
                        "sha256": "c" * 64,
                        "size_bytes": 1,
                        "zip_internal_root": "root",
                        "categories": [
                            {
                                "name": "unknown_category",
                                "zip_subdir": "images",
                                "place_to": "unknown_category/images",
                                "manifest": "unknown_category/manifest.json",
                                "expected_png_count": 1,
                                "expected_image_size": None,
                            }
                        ],
                    }
                ]
            },
        )
        with self.assertRaises(fri.FetchError):
            fri.load_character_packages(self.character_dir)

    def test_reserved_category_name_rejected(self):
        self.write_json(
            "packages.json",
            {
                "packages": [
                    {
                        "package_id": "p1",
                        "release_tag": "r1",
                        "filename": "f.zip",
                        "download_url": "https://example.com/f.zip",
                        "sha256": "c" * 64,
                        "size_bytes": 1,
                        "zip_internal_root": "root",
                        "categories": [
                            {
                                "name": "_private",
                                "zip_subdir": "images",
                                "place_to": "images",
                                "manifest": "manifest.json",
                                "expected_png_count": 1,
                                "expected_image_size": None,
                            }
                        ],
                    }
                ]
            },
        )
        with self.assertRaises(fri.FetchError):
            fri.load_character_packages(self.character_dir)

    def test_place_to_collision_between_packages_rejected(self):
        self.write_json("asset.json", make_legacy_asset_json())
        self.write_json(
            "packages.json",
            {
                "packages": [
                    {
                        "package_id": "duplicate",
                        "release_tag": "r1",
                        "filename": "f.zip",
                        "download_url": "https://example.com/f.zip",
                        "sha256": "c" * 64,
                        "size_bytes": 1,
                        "zip_internal_root": "root",
                        "categories": [
                            {
                                "name": "expressions",
                                "zip_subdir": "images",
                                "place_to": "images",  # 既存asset.json由来のexpressionsとplace_toが衝突
                                "manifest": "manifest.json",
                                "expected_png_count": 1,
                                "expected_image_size": None,
                            }
                        ],
                    }
                ]
            },
        )
        with self.assertRaises(fri.FetchError):
            fri.load_character_packages(self.character_dir)

    def test_place_to_collision_within_single_package_rejected(self):
        self.write_json(
            "packages.json",
            {
                "packages": [
                    {
                        "package_id": "p1",
                        "release_tag": "r1",
                        "filename": "f.zip",
                        "download_url": "https://example.com/f.zip",
                        "sha256": "c" * 64,
                        "size_bytes": 1,
                        "zip_internal_root": "root",
                        "categories": [
                            {
                                "name": "turnaround",
                                "zip_subdir": "a",
                                "place_to": "turnaround/images",
                                "manifest": "turnaround/manifest.json",
                                "expected_png_count": 1,
                                "expected_image_size": None,
                            },
                            {
                                "name": "equipment",
                                "zip_subdir": "b",
                                "place_to": "turnaround/images",
                                "manifest": "equipment/manifest.json",
                                "expected_png_count": 1,
                                "expected_image_size": None,
                            },
                        ],
                    }
                ]
            },
        )
        with self.assertRaises(fri.FetchError):
            fri.load_character_packages(self.character_dir)

    def test_package_with_no_categories_rejected(self):
        self.write_json(
            "packages.json",
            {
                "packages": [
                    {
                        "package_id": "p1",
                        "release_tag": "r1",
                        "filename": "f.zip",
                        "download_url": "https://example.com/f.zip",
                        "sha256": "c" * 64,
                        "size_bytes": 1,
                        "zip_internal_root": "root",
                        "categories": [],
                    }
                ]
            },
        )
        with self.assertRaises(fri.FetchError):
            fri.load_character_packages(self.character_dir)


# ---------------------------------------------------------------------------
# _verify_category
# ---------------------------------------------------------------------------

class VerifyCategoryTest(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.tmp = pathlib.Path(self._tmpdir.name)
        self.character_dir = self.tmp / "natsuki"
        self.character_dir.mkdir()
        self.staging_dir = self.tmp / "staging"
        self.staging_dir.mkdir()

    def write_manifest(self, relpath, data):
        path = self.character_dir / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f)

    def write_png(self, subdir, filename, size):
        d = self.staging_dir / subdir
        d.mkdir(parents=True, exist_ok=True)
        (d / filename).write_bytes(make_fake_png(*size))

    def test_uniform_size_category_passes(self):
        self.write_png("turnaround", "00-front.png", (1024, 1536))
        self.write_manifest("turnaround/manifest.json", {"front": "00-front.png"})
        category = {
            "name": "turnaround",
            "zip_subdir": "turnaround",
            "place_to": "turnaround/images",
            "manifest": "turnaround/manifest.json",
            "expected_png_count": 1,
            "expected_image_size": [1024, 1536],
        }
        fri._verify_category(self.character_dir, self.staging_dir, category)  # 例外なしでOK

    def test_uniform_size_mismatch_rejected(self):
        self.write_png("turnaround", "00-front.png", (999, 999))
        self.write_manifest("turnaround/manifest.json", {"front": "00-front.png"})
        category = {
            "name": "turnaround",
            "zip_subdir": "turnaround",
            "place_to": "turnaround/images",
            "manifest": "turnaround/manifest.json",
            "expected_png_count": 1,
            "expected_image_size": [1024, 1536],
        }
        with self.assertRaises(fri.FetchError):
            fri._verify_category(self.character_dir, self.staging_dir, category)

    def test_per_file_size_manifest_passes(self):
        self.write_png("turnaround", "00-front.png", (873, 1801))
        self.write_png("turnaround", "01-left-profile.png", (853, 1844))
        self.write_manifest(
            "turnaround/manifest.json",
            {
                "front": {"file": "00-front.png", "width": 873, "height": 1801},
                "left-profile": {"file": "01-left-profile.png", "width": 853, "height": 1844},
            },
        )
        category = {
            "name": "turnaround",
            "zip_subdir": "turnaround",
            "place_to": "turnaround/images",
            "manifest": "turnaround/manifest.json",
            "expected_png_count": 2,
            "expected_image_size": None,
        }
        fri._verify_category(self.character_dir, self.staging_dir, category)

    def test_per_file_size_mismatch_rejected(self):
        self.write_png("turnaround", "00-front.png", (100, 100))
        self.write_manifest(
            "turnaround/manifest.json",
            {"front": {"file": "00-front.png", "width": 873, "height": 1801}},
        )
        category = {
            "name": "turnaround",
            "zip_subdir": "turnaround",
            "place_to": "turnaround/images",
            "manifest": "turnaround/manifest.json",
            "expected_png_count": 1,
            "expected_image_size": None,
        }
        with self.assertRaises(fri.FetchError):
            fri._verify_category(self.character_dir, self.staging_dir, category)

    def test_wrong_png_count_rejected(self):
        self.write_png("turnaround", "00-front.png", (1024, 1536))
        self.write_manifest("turnaround/manifest.json", {"front": "00-front.png"})
        category = {
            "name": "turnaround",
            "zip_subdir": "turnaround",
            "place_to": "turnaround/images",
            "manifest": "turnaround/manifest.json",
            "expected_png_count": 4,
            "expected_image_size": [1024, 1536],
        }
        with self.assertRaises(fri.FetchError):
            fri._verify_category(self.character_dir, self.staging_dir, category)

    def test_manifest_referencing_missing_file_rejected(self):
        self.write_png("turnaround", "00-front.png", (1024, 1536))
        self.write_manifest(
            "turnaround/manifest.json", {"front": "00-front.png", "ghost": "99-ghost.png"}
        )
        category = {
            "name": "turnaround",
            "zip_subdir": "turnaround",
            "place_to": "turnaround/images",
            "manifest": "turnaround/manifest.json",
            "expected_png_count": 1,
            "expected_image_size": [1024, 1536],
        }
        with self.assertRaises(fri.FetchError):
            fri._verify_category(self.character_dir, self.staging_dir, category)

    def test_missing_manifest_file_raises(self):
        self.write_png("turnaround", "00-front.png", (1024, 1536))
        category = {
            "name": "turnaround",
            "zip_subdir": "turnaround",
            "place_to": "turnaround/images",
            "manifest": "turnaround/manifest.json",
            "expected_png_count": 1,
            "expected_image_size": [1024, 1536],
        }
        with self.assertRaises(fri.FetchError):
            fri._verify_category(self.character_dir, self.staging_dir, category)

    def test_missing_zip_subdir_raises(self):
        self.write_manifest("turnaround/manifest.json", {"front": "00-front.png"})
        category = {
            "name": "turnaround",
            "zip_subdir": "turnaround",
            "place_to": "turnaround/images",
            "manifest": "turnaround/manifest.json",
            "expected_png_count": 1,
            "expected_image_size": [1024, 1536],
        }
        with self.assertRaises(fri.FetchError):
            fri._verify_category(self.character_dir, self.staging_dir, category)


# ---------------------------------------------------------------------------
# fetch_character() 統合テスト
# ---------------------------------------------------------------------------

class FetchCharacterLegacyOnlyTest(unittest.TestCase):
    """旧形式asset.jsonのみを持つキャラクター(既存互換の挙動)。"""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.tmp = pathlib.Path(self._tmpdir.name)
        self.character_dir = self.tmp / "reference_images" / "testchar"
        self.character_dir.mkdir(parents=True)

        self.zip_path = self.tmp / "source.zip"
        self.png_specs = {v: (10, 10) for v in DEFAULT_EXPR_TAGS.values()}
        build_zip(self.zip_path, "testchar_set", {"images": self.png_specs})

        self.sha256 = hashlib.sha256(self.zip_path.read_bytes()).hexdigest()
        self.size_bytes = self.zip_path.stat().st_size

        self.write_asset_json()
        self.write_manifest_json(DEFAULT_EXPR_TAGS)

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
        for filename in DEFAULT_EXPR_TAGS.values():
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
            with self.assertRaises(fri.FetchError):
                fri.fetch_character(self.character_dir)
        self.assertFalse((self.character_dir / "images").exists())

    def test_existing_images_not_overwritten_without_force(self):
        images_dir = self.character_dir / "images"
        images_dir.mkdir()
        (images_dir / "sentinel.png").write_bytes(b"pre-existing")

        with mock.patch.object(fri, "download_file", side_effect=self._mock_download) as mocked_download:
            fri.fetch_character(self.character_dir, force=False)

        mocked_download.assert_not_called()
        self.assertTrue((images_dir / "sentinel.png").is_file())

    def test_force_replaces_existing_images(self):
        images_dir = self.character_dir / "images"
        images_dir.mkdir()
        (images_dir / "sentinel.png").write_bytes(b"stale")

        with mock.patch.object(fri, "download_file", side_effect=self._mock_download):
            fri.fetch_character(self.character_dir, force=True)

        self.assertFalse((images_dir / "sentinel.png").exists())
        for filename in DEFAULT_EXPR_TAGS.values():
            self.assertTrue((images_dir / filename).is_file())

    def test_failed_verification_does_not_touch_existing_valid_assets(self):
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

    def test_missing_manifest_json_raises(self):
        (self.character_dir / "manifest.json").unlink()
        with mock.patch.object(fri, "download_file", side_effect=self._mock_download):
            with self.assertRaises(fri.FetchError):
                fri.fetch_character(self.character_dir)

    def test_temp_dir_created_under_character_dir_parent(self):
        with mock.patch.object(
            fri.tempfile, "TemporaryDirectory", wraps=fri.tempfile.TemporaryDirectory
        ) as mocked_tmp:
            with mock.patch.object(fri, "download_file", side_effect=self._mock_download):
                fri.fetch_character(self.character_dir)

        mocked_tmp.assert_called_once()
        _, kwargs = mocked_tmp.call_args
        self.assertEqual(kwargs.get("dir"), self.character_dir.parent)


class FetchCharacterMultiPackageTest(unittest.TestCase):
    """複数package(ハルト方式: 旧asset.json + 新packages.json)を持つ
    キャラクターの取得を検証する。
    """

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.tmp = pathlib.Path(self._tmpdir.name)
        self.character_dir = self.tmp / "reference_images" / "haruto"
        self.character_dir.mkdir(parents=True)

        # expressions(旧asset.json)
        self.expr_zip = self.tmp / "expr.zip"
        build_zip(self.expr_zip, "expr_set", {"images": {"00-neutral.png": (10, 10)}})
        with (self.character_dir / "asset.json").open("w", encoding="utf-8") as f:
            json.dump(
                {
                    "release_tag": "expr-v1",
                    "filename": "expr.zip",
                    "download_url": "https://example.com/expr.zip",
                    "sha256": hashlib.sha256(self.expr_zip.read_bytes()).hexdigest(),
                    "size_bytes": self.expr_zip.stat().st_size,
                    "expected_png_count": 1,
                    "expected_image_size": [10, 10],
                    "zip_internal_root": "expr_set",
                },
                f,
            )
        with (self.character_dir / "manifest.json").open("w", encoding="utf-8") as f:
            json.dump({"neutral": "00-neutral.png"}, f)

        # turnaround(新packages.json)
        self.turnaround_zip = self.tmp / "turnaround.zip"
        build_zip(
            self.turnaround_zip,
            "turnaround_set",
            {"images": {"00-front.png": (20, 20)}},
            include_index_html=False,
        )
        with (self.character_dir / "packages.json").open("w", encoding="utf-8") as f:
            json.dump(
                {
                    "packages": [
                        {
                            "package_id": "turnaround-v1",
                            "release_tag": "turnaround-v1",
                            "filename": "turnaround.zip",
                            "download_url": "https://example.com/turnaround.zip",
                            "sha256": hashlib.sha256(self.turnaround_zip.read_bytes()).hexdigest(),
                            "size_bytes": self.turnaround_zip.stat().st_size,
                            "zip_internal_root": "turnaround_set",
                            "categories": [
                                {
                                    "name": "turnaround",
                                    "zip_subdir": "images",
                                    "place_to": "turnaround/images",
                                    "manifest": "turnaround/manifest.json",
                                    "expected_png_count": 1,
                                    "expected_image_size": [20, 20],
                                }
                            ],
                        }
                    ]
                },
                f,
            )
        (self.character_dir / "turnaround").mkdir()
        with (self.character_dir / "turnaround" / "manifest.json").open("w", encoding="utf-8") as f:
            json.dump({"front": "00-front.png"}, f)

    def _mock_download(self, url, dest_path):
        if "expr" in url:
            shutil.copy(self.expr_zip, dest_path)
        else:
            shutil.copy(self.turnaround_zip, dest_path)

    def test_both_packages_fetched(self):
        with mock.patch.object(fri, "download_file", side_effect=self._mock_download):
            fri.fetch_character(self.character_dir)

        self.assertTrue((self.character_dir / "images" / "00-neutral.png").is_file())
        self.assertTrue((self.character_dir / "turnaround" / "images" / "00-front.png").is_file())

    def test_already_fetched_package_is_skipped_other_still_fetched(self):
        # expressionsだけ事前に取得済みとする。turnaroundは未取得。
        images_dir = self.character_dir / "images"
        images_dir.mkdir()
        (images_dir / "00-neutral.png").write_bytes(b"already-here")

        with mock.patch.object(fri, "download_file", side_effect=self._mock_download) as mocked:
            fri.fetch_character(self.character_dir)

        # expressionsは変更されていない(再ダウンロードされていない)。
        self.assertEqual((images_dir / "00-neutral.png").read_bytes(), b"already-here")
        # turnaroundは新規に取得された。
        self.assertTrue((self.character_dir / "turnaround" / "images" / "00-front.png").is_file())
        # ダウンロードはturnaround分の1回だけ呼ばれた。
        self.assertEqual(mocked.call_count, 1)

    def test_one_package_failure_does_not_affect_other_already_placed_package(self):
        with mock.patch.object(fri, "download_file", side_effect=self._mock_download):
            fri.fetch_character(self.character_dir)

        # expressionsは既に配置済み。turnaroundだけforceで再取得し、
        # 今回は検証失敗させる。
        with (self.character_dir / "packages.json").open(encoding="utf-8") as f:
            packages_config = json.load(f)
        packages_config["packages"][0]["sha256"] = "0" * 64
        with (self.character_dir / "packages.json").open("w", encoding="utf-8") as f:
            json.dump(packages_config, f)

        expr_before = (self.character_dir / "images" / "00-neutral.png").read_bytes()

        with mock.patch.object(fri, "download_file", side_effect=self._mock_download):
            with self.assertRaises(fri.FetchError):
                fri.fetch_character(self.character_dir, force=True)

        # expressionsは無傷。
        self.assertEqual((self.character_dir / "images" / "00-neutral.png").read_bytes(), expr_before)


class FetchCharacterSingleZipMultiCategoryTest(unittest.TestCase):
    """1つのZIPから複数category(ナツキ方式)を取得する場合を検証する。"""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.tmp = pathlib.Path(self._tmpdir.name)
        self.character_dir = self.tmp / "reference_images" / "natsuki"
        self.character_dir.mkdir(parents=True)

        self.zip_path = self.tmp / "complete.zip"
        build_zip(
            self.zip_path,
            "natsuki_set",
            {
                "expressions": {"00-neutral.png": (10, 10)},
                "turnaround": {"00-front.png": (873, 1801)},
                "equipment": {"crest.png": (30, 30)},
            },
        )
        self.sha256 = hashlib.sha256(self.zip_path.read_bytes()).hexdigest()
        self.size_bytes = self.zip_path.stat().st_size

        self.write_packages_json()
        with (self.character_dir / "manifest.json").open("w", encoding="utf-8") as f:
            json.dump({"neutral": "00-neutral.png"}, f)
        (self.character_dir / "turnaround").mkdir()
        with (self.character_dir / "turnaround" / "manifest.json").open("w", encoding="utf-8") as f:
            json.dump({"front": {"file": "00-front.png", "width": 873, "height": 1801}}, f)
        (self.character_dir / "equipment").mkdir()
        with (self.character_dir / "equipment" / "manifest.json").open("w", encoding="utf-8") as f:
            json.dump({"crest-hariyumi-himawari": "crest.png"}, f)

    def write_packages_json(self, **package_overrides):
        package = {
            "package_id": "complete-set-v2",
            "release_tag": "natsuki-complete-set-v2",
            "filename": "complete.zip",
            "download_url": "https://example.com/complete.zip",
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
            "zip_internal_root": "natsuki_set",
            "categories": [
                {
                    "name": "expressions",
                    "zip_subdir": "expressions",
                    "place_to": "images",
                    "manifest": "manifest.json",
                    "expected_png_count": 1,
                    "expected_image_size": [10, 10],
                },
                {
                    "name": "turnaround",
                    "zip_subdir": "turnaround",
                    "place_to": "turnaround/images",
                    "manifest": "turnaround/manifest.json",
                    "expected_png_count": 1,
                    "expected_image_size": None,
                },
                {
                    "name": "equipment",
                    "zip_subdir": "equipment",
                    "place_to": "equipment/images",
                    "manifest": "equipment/manifest.json",
                    "expected_png_count": 1,
                    "expected_image_size": None,
                },
            ],
        }
        package.update(package_overrides)
        with (self.character_dir / "packages.json").open("w", encoding="utf-8") as f:
            json.dump({"packages": [package]}, f)

    def _mock_download(self, url, dest_path):
        shutil.copy(self.zip_path, dest_path)

    def test_single_download_places_all_three_categories(self):
        with mock.patch.object(fri, "download_file", side_effect=self._mock_download) as mocked:
            fri.fetch_character(self.character_dir)

        self.assertEqual(mocked.call_count, 1)
        self.assertTrue((self.character_dir / "images" / "00-neutral.png").is_file())
        self.assertTrue((self.character_dir / "turnaround" / "images" / "00-front.png").is_file())
        self.assertTrue((self.character_dir / "equipment" / "images" / "crest.png").is_file())

    def test_one_category_failure_places_no_category(self):
        # equipmentのexpected_png_countを誤らせ、equipmentカテゴリだけを
        # 検証失敗させる。expressions/turnaroundは検証OKでも、package
        # 全体としては何も配置されないこと(全カテゴリ検証後に原子的配置)。
        with (self.character_dir / "packages.json").open(encoding="utf-8") as f:
            config = json.load(f)
        config["packages"][0]["categories"][2]["expected_png_count"] = 99
        with (self.character_dir / "packages.json").open("w", encoding="utf-8") as f:
            json.dump(config, f)

        with mock.patch.object(fri, "download_file", side_effect=self._mock_download):
            with self.assertRaises(fri.FetchError):
                fri.fetch_character(self.character_dir)

        self.assertFalse((self.character_dir / "images").exists())
        self.assertFalse((self.character_dir / "turnaround" / "images").exists())
        self.assertFalse((self.character_dir / "equipment" / "images").exists())


class CompleteArchiveNotAutoFetchedTest(unittest.TestCase):
    """haruto_complete_archive_v1.zip(保存・退避用完全版)が、asset.json・
    packages.jsonのいずれからも参照されておらず、自動取得の対象になって
    いないことを確認する。
    """

    def test_archive_filename_not_referenced_in_any_character_config(self):
        config_paths = list(fri.REFERENCE_IMAGES_ROOT.glob("*/asset.json")) + list(
            fri.REFERENCE_IMAGES_ROOT.glob("*/packages.json")
        )
        self.assertTrue(config_paths, "検証対象のasset.json/packages.jsonが見つかりません")

        offenders = []
        for path in config_paths:
            with path.open(encoding="utf-8") as f:
                text = f.read()
            if "complete_archive" in text or "complete-archive" in text:
                offenders.append(str(path))
        self.assertEqual(offenders, [], f"完全版Archiveが取得設定に混入しています: {offenders}")


if __name__ == "__main__":
    unittest.main()
