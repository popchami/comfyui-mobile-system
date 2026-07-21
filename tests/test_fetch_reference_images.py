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

    def test_place_to_not_matching_canonical_value_rejected(self):
        # 既知category名("turnaround")でも、place_toが正本値
        # ("turnaround/images")と一致しなければ拒否する。設定ファイル経由
        # のpath traversal("../../outside"等)を、値そのものを信頼せず
        # 正本値との一致を要求する形で防ぐ(Codexレビュー指摘、Critical)。
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
                                "zip_subdir": "images",
                                "place_to": "../../outside",
                                "manifest": "turnaround/manifest.json",
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

    def test_manifest_not_matching_canonical_value_rejected(self):
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
                                "zip_subdir": "images",
                                "place_to": "turnaround/images",
                                "manifest": "../../outside/manifest.json",
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

    def test_null_uniform_size_requires_object_form_manifest_entries(self):
        # expected_image_size=nullなのにmanifestが文字列形式のエントリを
        # 持つ場合、寸法検証が一切行われないまま素通りしていた
        # (Codexレビュー指摘、Critical: 実際にnatsuki/equipmentがこの状態
        # だった)。厳格化後は明示的にFetchErrorとする。
        self.write_png("turnaround", "00-front.png", (873, 1801))
        self.write_manifest("turnaround/manifest.json", {"front": "00-front.png"})
        category = {
            "name": "turnaround",
            "zip_subdir": "turnaround",
            "place_to": "turnaround/images",
            "manifest": "turnaround/manifest.json",
            "expected_png_count": 1,
            "expected_image_size": None,
        }
        with self.assertRaises(fri.FetchError) as ctx:
            fri._verify_category(self.character_dir, self.staging_dir, category)
        self.assertIn("file/width/height", str(ctx.exception))

    def test_null_uniform_size_with_object_missing_width_rejected(self):
        self.write_png("turnaround", "00-front.png", (873, 1801))
        self.write_manifest("turnaround/manifest.json", {"front": {"file": "00-front.png"}})
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

    def test_manifest_filename_path_traversal_rejected(self):
        # manifest.json内のファイル名自体が"../"等でcategoryの画像
        # ディレクトリの外を指す場合を拒否する(Codexレビュー指摘、
        # Critical)。
        self.write_png("turnaround", "00-front.png", (1024, 1536))
        outside_dir = self.tmp / "outside"
        outside_dir.mkdir()
        (outside_dir / "secret.png").write_bytes(make_fake_png(1, 1))
        self.write_manifest(
            "turnaround/manifest.json", {"front": "../../outside/secret.png"}
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

    # -------------------------------------------------------------------
    # flatten対応category(アキラのequipment: hammer/talisman/nailの
    # 3サブフォルダに分かれたPNGを、manifestのsource_file/fileで対応づける)
    # -------------------------------------------------------------------

    def test_flatten_category_counts_nested_pngs_via_rglob(self):
        # zip_subdir直下ではなくさらにサブフォルダに分かれている場合、
        # 従来の非再帰globでは0枚と誤判定してしまう(rglobで正しく数える)。
        self.write_png("equipment/hammer", "00-a.png", (887, 1774))
        self.write_png("equipment/talisman", "00-b.png", (887, 1774))
        self.write_manifest(
            "equipment/manifest.json",
            {
                "hammer-a": {
                    "file": "hammer-00-a.png",
                    "source_file": "hammer/00-a.png",
                    "width": 887,
                    "height": 1774,
                },
                "talisman-b": {
                    "file": "talisman-00-b.png",
                    "source_file": "talisman/00-b.png",
                    "width": 887,
                    "height": 1774,
                },
            },
        )
        category = {
            "name": "equipment",
            "zip_subdir": "equipment",
            "place_to": "equipment/images",
            "manifest": "equipment/manifest.json",
            "expected_png_count": 2,
            "expected_image_size": None,
            "flatten": True,
        }
        fri._verify_category(self.character_dir, self.staging_dir, category)  # 例外なしでOK

    def test_flatten_category_missing_nested_source_file_rejected(self):
        self.write_png("equipment/hammer", "00-a.png", (887, 1774))
        self.write_manifest(
            "equipment/manifest.json",
            {
                "hammer-a": {
                    "file": "hammer-00-a.png",
                    "source_file": "hammer/00-a.png",
                    "width": 887,
                    "height": 1774,
                },
                "hammer-ghost": {
                    "file": "hammer-99-ghost.png",
                    "source_file": "hammer/99-ghost.png",
                    "width": 887,
                    "height": 1774,
                },
            },
        )
        category = {
            "name": "equipment",
            "zip_subdir": "equipment",
            "place_to": "equipment/images",
            "manifest": "equipment/manifest.json",
            "expected_png_count": 1,
            "expected_image_size": None,
            "flatten": True,
        }
        with self.assertRaises(fri.FetchError):
            fri._verify_category(self.character_dir, self.staging_dir, category)

    def test_flatten_category_source_file_path_traversal_rejected(self):
        # source_fileも通常のfileと同様、zip_subdirの外を指す値は拒否する。
        self.write_png("equipment/hammer", "00-a.png", (887, 1774))
        outside_dir = self.tmp / "outside"
        outside_dir.mkdir()
        (outside_dir / "secret.png").write_bytes(make_fake_png(1, 1))
        self.write_manifest(
            "equipment/manifest.json",
            {
                "hammer-a": {
                    "file": "hammer-00-a.png",
                    "source_file": "../../outside/secret.png",
                    "width": 887,
                    "height": 1774,
                }
            },
        )
        category = {
            "name": "equipment",
            "zip_subdir": "equipment",
            "place_to": "equipment/images",
            "manifest": "equipment/manifest.json",
            "expected_png_count": 1,
            "expected_image_size": None,
            "flatten": True,
        }
        with self.assertRaises(fri.FetchError):
            fri._verify_category(self.character_dir, self.staging_dir, category)

    def test_non_flatten_category_without_source_file_still_works(self):
        # flatten指定なしのcategory(既存のexpressions/turnaround)は、
        # source_fileが未指定でも従来通りfileと同じパスで解決される
        # (既存挙動の回帰確認)。
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


class PlaceCategoryFlattenTest(unittest.TestCase):
    """_place_category()のflatten対応(ネスト元→フラット配置先)を検証する。"""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.tmp = pathlib.Path(self._tmpdir.name)
        self.character_dir = self.tmp / "akira"
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

    def test_flatten_places_files_with_manifest_file_names(self):
        self.write_png("equipment/hammer", "00-a.png", (887, 1774))
        self.write_png("equipment/talisman", "00-b.png", (887, 1774))
        self.write_manifest(
            "equipment/manifest.json",
            {
                "hammer-a": {"file": "hammer-00-a.png", "source_file": "hammer/00-a.png", "width": 887, "height": 1774},
                "talisman-b": {"file": "talisman-00-b.png", "source_file": "talisman/00-b.png", "width": 887, "height": 1774},
            },
        )
        category = {
            "name": "equipment",
            "zip_subdir": "equipment",
            "place_to": "equipment/images",
            "manifest": "equipment/manifest.json",
            "expected_png_count": 2,
            "expected_image_size": None,
            "flatten": True,
        }
        fri._place_category(self.character_dir, self.staging_dir, category)

        dest = self.character_dir / "equipment" / "images"
        self.assertTrue((dest / "hammer-00-a.png").is_file())
        self.assertTrue((dest / "talisman-00-b.png").is_file())
        # ネスト構造(hammer/talisman サブフォルダ)は配置先には持ち込まれない。
        self.assertFalse((dest / "hammer").exists())
        self.assertFalse((dest / "talisman").exists())

    def test_non_flatten_moves_whole_directory_unchanged(self):
        # flatten指定なしのcategoryは、既存挙動(ディレクトリごと原子的に
        # 配置)のまま変わらないことを確認する(回帰確認)。
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
        fri._place_category(self.character_dir, self.staging_dir, category)

        dest = self.character_dir / "turnaround" / "images"
        self.assertTrue((dest / "00-front.png").is_file())


class ResolveContainedTest(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.base = pathlib.Path(self._tmpdir.name)

    def test_normal_relative_path_allowed(self):
        target = fri._resolve_contained(self.base, "sub/file.png", "test")
        self.assertEqual(target, (self.base / "sub" / "file.png").resolve())

    def test_parent_traversal_rejected(self):
        with self.assertRaises(fri.FetchError):
            fri._resolve_contained(self.base, "../outside.png", "test")

    def test_deep_parent_traversal_rejected(self):
        with self.assertRaises(fri.FetchError):
            fri._resolve_contained(self.base, "sub/../../outside.png", "test")

    def test_absolute_path_rejected(self):
        with tempfile.TemporaryDirectory() as other:
            with self.assertRaises(fri.FetchError):
                fri._resolve_contained(self.base, str(pathlib.Path(other) / "x.png"), "test")

    def test_base_dir_itself_allowed(self):
        target = fri._resolve_contained(self.base, ".", "test")
        self.assertEqual(target, self.base.resolve())


class SharedCategoryConstantsTest(unittest.TestCase):
    """fetch_reference_images.pyとresolve_reference_image.pyが、category
    定義をscripts/reference_image_categories.pyから共有していることを
    確認する(Codexレビュー指摘、Minor: 以前は2箇所に独立定義されており
    drift〔片方だけ更新して不整合になる〕のリスクがあった)。
    """

    def test_known_categories_shared_with_resolver(self):
        import resolve_reference_image as rri

        self.assertIs(fri.KNOWN_CATEGORIES, rri.KNOWN_CATEGORIES)

    def test_category_place_to_shared_with_resolver(self):
        import resolve_reference_image as rri

        self.assertIs(fri.CATEGORY_PLACE_TO, rri.CATEGORY_PLACE_TO)


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
            # expected_image_size=Noneのcategoryはfile/width/height形式が
            # 必須(uniform_size=None時の厳格化、Codexレビュー指摘の回帰確認)。
            json.dump({"crest-hariyumi-himawari": {"file": "crest.png", "width": 30, "height": 30}}, f)

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
    """haruto_complete_archive_v1.zip(ハルトの保存・退避用完全版)が、
    ハルトのasset.json・packages.jsonのいずれからも参照されておらず、
    自動取得の対象になっていないことを確認する。

    注意(スコープをハルトに限定する理由): 他キャラクターは、
    "_complete_archive"という命名のZIPそのものを唯一の正本ソースとして
    意図的にpackages.jsonへ登録する設計を採用する場合がある(例: アキラの
    akira_complete_archive_v1.zipは、チャミの明示的な決定によりexpressions/
    turnaround/equipmentの3カテゴリの正式な取得元として登録されている)。
    そのため「complete_archiveという文字列がどの設定ファイルにも一切
    存在しない」という全体チェックではなく、「ハルト自身の設定がハルト
    自身の保存用完全版アーカイブを参照していない」というハルト固有の
    検査に限定する。
    """

    def test_haruto_config_does_not_reference_its_own_archive(self):
        haruto_dir = fri.REFERENCE_IMAGES_ROOT / "haruto"
        config_paths = [
            p for p in (haruto_dir / "asset.json", haruto_dir / "packages.json") if p.is_file()
        ]
        self.assertTrue(config_paths, "ハルトのasset.json/packages.jsonが見つかりません")

        offenders = []
        for path in config_paths:
            text = path.read_text(encoding="utf-8")
            if "complete_archive" in text or "complete-archive" in text:
                offenders.append(str(path))
        self.assertEqual(offenders, [], f"ハルトの保存用完全版Archiveが取得設定に混入しています: {offenders}")


class RealCharacterConfigsLoadTest(unittest.TestCase):
    """実際にコミットされている全キャラクターの設定(asset.json/
    packages.json)が、load_character_packages()でエラーなく読み込める
    ことを確認する(ネットワークアクセスなし、既存ハルト・ナツキとの
    後方互換の回帰確認を兼ねる)。
    """

    def test_all_real_character_dirs_load_without_error(self):
        character_dirs = fri.discover_character_dirs()
        self.assertTrue(character_dirs, "reference_images配下にキャラクターが見つかりません")
        names = sorted(d.name for d in character_dirs)
        self.assertIn("haruto", names)
        self.assertIn("natsuki", names)
        self.assertIn("akira", names)

        for character_dir in character_dirs:
            with self.subTest(character=character_dir.name):
                packages = fri.load_character_packages(character_dir)
                self.assertTrue(packages)


class AkiraRealConfigTest(unittest.TestCase):
    """アキラの実際の設定ファイル(packages.json・各manifest.json)の
    内容を検証する。ネットワークアクセスは行わない。
    """

    def setUp(self):
        self.character_dir = fri.REFERENCE_IMAGES_ROOT / "akira"

    def test_three_categories_registered_with_expected_counts(self):
        packages = fri.load_character_packages(self.character_dir)
        self.assertEqual(len(packages), 1)
        categories = {c["name"]: c for c in packages[0]["categories"]}
        self.assertEqual(set(categories), {"expressions", "turnaround", "equipment"})
        self.assertEqual(categories["expressions"]["expected_png_count"], 31)
        self.assertEqual(categories["turnaround"]["expected_png_count"], 4)
        self.assertEqual(categories["equipment"]["expected_png_count"], 13)
        self.assertTrue(categories["equipment"].get("flatten"))
        self.assertFalse(categories["expressions"].get("flatten"))
        self.assertFalse(categories["turnaround"].get("flatten"))

    def test_expressions_manifest_has_31_tags_matching_haruto(self):
        with (self.character_dir / "manifest.json").open(encoding="utf-8") as f:
            akira_tags = {k for k in json.load(f) if not k.startswith("_")}
        with (fri.REFERENCE_IMAGES_ROOT / "haruto" / "manifest.json").open(encoding="utf-8") as f:
            haruto_tags = {k for k in json.load(f) if not k.startswith("_")}
        self.assertEqual(len(akira_tags), 31)
        self.assertEqual(akira_tags, haruto_tags)

    def test_equipment_manifest_has_13_entries_with_source_file_and_dimensions(self):
        with (self.character_dir / "equipment" / "manifest.json").open(encoding="utf-8") as f:
            manifest = json.load(f)
        entries = {k: v for k, v in manifest.items() if not k.startswith("_")}
        self.assertEqual(len(entries), 13)
        for tag, entry in entries.items():
            with self.subTest(tag=tag):
                self.assertIsInstance(entry, dict)
                self.assertIn("file", entry)
                self.assertIn("source_file", entry)
                self.assertIn("width", entry)
                self.assertIn("height", entry)
                # フラット化後のfileには"/"を含まない(サブフォルダ構造が
                # 持ち込まれていないこと)。source_fileはネストを含んでよい。
                self.assertNotIn("/", entry["file"])

    def test_equipment_nail_ranged_flight_keeps_original_1024x1536(self):
        # チャミの決定(7): 画像寸法は変更しない。02-ranged-flight-long.png
        # も1024x1536のまま使用する。
        with (self.character_dir / "equipment" / "manifest.json").open(encoding="utf-8") as f:
            manifest = json.load(f)
        entry = manifest["nail-ranged-flight-long"]
        self.assertEqual((entry["width"], entry["height"]), (1024, 1536))

    def test_archival_only_assets_not_registered_in_any_config(self):
        # character/reference・crest・previews・ZIP独自README/manifest/
        # SHA256SUMS.txtは保存用資料であり、packages.json・カテゴリ
        # manifestのいずれにも登録しない(チャミの決定5)。
        packages = fri.load_character_packages(self.character_dir)
        forbidden_zip_subdirs = {"character/reference", "crest", "previews"}
        for package in packages:
            for category in package["categories"]:
                self.assertNotIn(category["zip_subdir"], forbidden_zip_subdirs)

        manifest_paths = [
            self.character_dir / "manifest.json",
            self.character_dir / "turnaround" / "manifest.json",
            self.character_dir / "equipment" / "manifest.json",
        ]
        for path in manifest_paths:
            with path.open(encoding="utf-8") as f:
                manifest = json.load(f)
            for tag, entry in manifest.items():
                if tag.startswith("_"):
                    continue
                filename = entry["file"] if isinstance(entry, dict) else entry
                source_rel = fri._source_rel_for_entry(entry, filename)
                with self.subTest(path=str(path), tag=tag):
                    self.assertNotIn("crest", source_rel)
                    self.assertNotIn("reference", source_rel)
                    self.assertNotIn("preview", source_rel)


class FetchCharacterFlattenEquipmentTest(unittest.TestCase):
    """1つのZIP内でcategoryがさらにサブフォルダ(hammer/talisman等)に
    分かれている場合(アキラのequipment方式)を、fetch_character()経由の
    end-to-endで検証する。
    """

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.tmp = pathlib.Path(self._tmpdir.name)
        self.character_dir = self.tmp / "reference_images" / "akira"
        self.character_dir.mkdir(parents=True)

        self.zip_path = self.tmp / "akira.zip"
        with zipfile.ZipFile(self.zip_path, "w") as zf:
            zf.writestr("akira_set/expressions/", "")
            zf.writestr("akira_set/expressions/00-neutral.png", make_fake_png(10, 10))
            zf.writestr("akira_set/character/turnaround/", "")
            zf.writestr("akira_set/character/turnaround/00-front.png", make_fake_png(887, 1774))
            zf.writestr("akira_set/equipment/hammer/", "")
            zf.writestr("akira_set/equipment/hammer/00-a.png", make_fake_png(887, 1774))
            zf.writestr("akira_set/equipment/talisman/", "")
            zf.writestr("akira_set/equipment/talisman/00-b.png", make_fake_png(887, 1774))
            zf.writestr("akira_set/equipment/nail/", "")
            zf.writestr("akira_set/equipment/nail/00-c.png", make_fake_png(1024, 1536))
        self.sha256 = hashlib.sha256(self.zip_path.read_bytes()).hexdigest()
        self.size_bytes = self.zip_path.stat().st_size

        package = {
            "package_id": "complete-archive-v1",
            "release_tag": "akira-complete-archive-v1",
            "filename": "akira.zip",
            "download_url": "https://example.com/akira.zip",
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
            "zip_internal_root": "akira_set",
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
                    "zip_subdir": "character/turnaround",
                    "place_to": "turnaround/images",
                    "manifest": "turnaround/manifest.json",
                    "expected_png_count": 1,
                    "expected_image_size": [887, 1774],
                },
                {
                    "name": "equipment",
                    "zip_subdir": "equipment",
                    "place_to": "equipment/images",
                    "manifest": "equipment/manifest.json",
                    "expected_png_count": 3,
                    "expected_image_size": None,
                    "flatten": True,
                },
            ],
        }
        with (self.character_dir / "packages.json").open("w", encoding="utf-8") as f:
            json.dump({"packages": [package]}, f)
        with (self.character_dir / "manifest.json").open("w", encoding="utf-8") as f:
            json.dump({"neutral": "00-neutral.png"}, f)
        (self.character_dir / "turnaround").mkdir()
        with (self.character_dir / "turnaround" / "manifest.json").open("w", encoding="utf-8") as f:
            json.dump({"front": "00-front.png"}, f)
        (self.character_dir / "equipment").mkdir()
        with (self.character_dir / "equipment" / "manifest.json").open("w", encoding="utf-8") as f:
            json.dump(
                {
                    "hammer-a": {"file": "hammer-00-a.png", "source_file": "hammer/00-a.png", "width": 887, "height": 1774},
                    "talisman-b": {"file": "talisman-00-b.png", "source_file": "talisman/00-b.png", "width": 887, "height": 1774},
                    "nail-c": {"file": "nail-00-c.png", "source_file": "nail/00-c.png", "width": 1024, "height": 1536},
                },
                f,
            )

    def _mock_download(self, url, dest_path):
        shutil.copy(self.zip_path, dest_path)

    def test_fetch_character_flattens_nested_equipment(self):
        with mock.patch.object(fri, "download_file", side_effect=self._mock_download):
            fri.fetch_character(self.character_dir)

        self.assertTrue((self.character_dir / "images" / "00-neutral.png").is_file())
        self.assertTrue((self.character_dir / "turnaround" / "images" / "00-front.png").is_file())

        equipment_dir = self.character_dir / "equipment" / "images"
        self.assertTrue((equipment_dir / "hammer-00-a.png").is_file())
        self.assertTrue((equipment_dir / "talisman-00-b.png").is_file())
        self.assertTrue((equipment_dir / "nail-00-c.png").is_file())
        # ネストされたサブフォルダ自体は配置先に持ち込まれない。
        self.assertFalse((equipment_dir / "hammer").exists())
        self.assertFalse((equipment_dir / "talisman").exists())
        self.assertFalse((equipment_dir / "nail").exists())

    def test_equipment_dimension_mismatch_still_detected_after_flatten(self):
        # nail-cの期待寸法を誤らせ、flatten対応でも寸法検証が正しく
        # 機能していることを確認する(回帰確認)。
        with (self.character_dir / "equipment" / "manifest.json").open(encoding="utf-8") as f:
            manifest = json.load(f)
        manifest["nail-c"]["width"] = 1
        with (self.character_dir / "equipment" / "manifest.json").open("w", encoding="utf-8") as f:
            json.dump(manifest, f)

        with mock.patch.object(fri, "download_file", side_effect=self._mock_download):
            with self.assertRaises(fri.FetchError):
                fri.fetch_character(self.character_dir)

        self.assertFalse((self.character_dir / "images").exists())
        self.assertFalse((self.character_dir / "equipment" / "images").exists())


if __name__ == "__main__":
    unittest.main()
