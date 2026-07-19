#!/usr/bin/env python3
"""異世界ニホンマンガ用キャラクター参照画像を、GitHub Releaseから取得・
検証・配置するスクリプト。

1キャラクターは複数のRelease ZIP(package)を持つことができ、1つの
package(ZIP)は複数のカテゴリ(expressions/turnaround/equipment等)を
収録できる。

profiles/sdxl/isekai_nihon_manga/reference_images/<character>/ 配下の
設定ファイルからpackage定義を読み込む:

- asset.json(任意、旧形式・後方互換): 1キャラクター=1ZIP=表情のみを
  前提とした従来の形式。存在する場合、暗黙のcategory="expressions"を
  持つ1つのpackageとして扱う。フィールドは一切解釈を変えない
- packages.json(任意、新形式): 複数packageを明示的に列挙する形式。
  各packageは複数categoryを持てる

どちらも存在しない場合はエラーとする。両方存在する場合は両方を対象と
する(例: harutoはasset.json=表情〔既存〕+packages.json=4方向立ち絵)。

内部配置(character_dir配下):

  images/                    # category "expressions"(asset.json由来。既存互換)
  turnaround/images/         # category "turnaround"
  equipment/images/          # category "equipment"
  (将来 poses/images/ 等を追加可能)

各categoryは、自分専用のmanifest.json(category内での相対パス。例:
turnaround/manifest.json)を持つ。manifest.jsonの値は文字列
("ファイル名.png")または{"file": "...", "width": W, "height": H}
のいずれかを取り、後者は寸法がカテゴリ内で不揃いな場合(例: 4方向立ち絵の
構図差)の個別サイズ検証に使う。

安全条件(チャミ承認済み仕様):

- ZIP全体のダウンロード完了後にサイズ・SHA-256を照合する。不一致なら
  展開・利用しない
- 展開後、package内の全categoryについて、PNG枚数・manifest網羅・
  画像サイズ(カテゴリ一律またはmanifestごとの個別指定)を検証する
- ダウンロード・展開・検証はすべて一時ディレクトリ(character_dirと
  同じファイルシステム上)で行い、1つのpackageに属する全categoryの
  検証に合格した場合にのみ、そのpackageの全categoryをまとめて原子的に
  正式配置へ反映する。検証前に既存の正式配置を上書きしない
- 展開先ディレクトリの外へ書き込むZIPエントリ(zip slip)・重複パスの
  ZIPエントリは拒否する
- 同一キャラクターに対する複数の同時実行はflockで排他する
  (character_dir/.fetch.lock、Git管理外)
- 同一キャラクター内のcategory間で配置先(place_to)が衝突する場合は
  設定エラーとして拒否する
- 既存のFlux系プロファイル(profiles/flux1_dev等)には一切触れない
  (このスクリプトはprofiles/sdxl/isekai_nihon_manga/reference_images/
  配下のみを対象とする)

標準ライブラリのみを使用する(urllib, zipfile, hashlib, struct等)。
追加の依存導入は行わない。

使い方:
  python3 scripts/fetch_reference_images.py                # 全キャラクター
  python3 scripts/fetch_reference_images.py --character haruto
  python3 scripts/fetch_reference_images.py --character haruto --force
"""
import argparse
import contextlib
import fcntl
import hashlib
import json
import os
import shutil
import struct
import sys
import tempfile
import urllib.request
import uuid
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REFERENCE_IMAGES_ROOT = ROOT / "profiles" / "sdxl" / "isekai_nihon_manga" / "reference_images"

# 将来 poses / training 等を追加する際はここに列挙を追加する。
KNOWN_CATEGORIES = {"expressions", "turnaround", "equipment"}


class FetchError(Exception):
    """取得・検証・設定のいずれかの段階で失敗したことを表す。"""


def download_file(url, dest_path):
    """urlからdest_pathへダウンロードする(標準ライブラリのみ)。"""
    with urllib.request.urlopen(url, timeout=120) as response, dest_path.open("wb") as out:
        shutil.copyfileobj(response, out)


def compute_sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_extract(zip_path, dest_dir, strip_prefix):
    """zip slip・重複パス対策つきの展開。

    ZIP内の各エントリ名から先頭の strip_prefix(ZIP内部のトップレベル
    フォルダ名)を取り除いたうえで、dest_dir配下にのみ書き込む。
    絶対パス・".."等でdest_dirの外を指すエントリ、および同一の展開先
    パスを複数回指すエントリ(重複パス)は拒否する。
    """
    dest_dir = dest_dir.resolve()
    dest_dir.mkdir(parents=True, exist_ok=True)
    prefix = strip_prefix.rstrip("/") + "/"
    written_targets = set()

    with zipfile.ZipFile(zip_path) as zf:
        for member in zf.infolist():
            name = member.filename
            if name in (strip_prefix, strip_prefix + "/"):
                continue
            if name.startswith(prefix):
                rel = name[len(prefix):]
            else:
                # トップレベルフォルダの外にあるエントリは想定外として拒否する。
                raise FetchError(f"ZIPエントリが想定外の場所にあります(拒否): {name!r}")
            if not rel:
                continue

            target = (dest_dir / rel).resolve()
            if target != dest_dir and dest_dir not in target.parents:
                raise FetchError(f"ZIPエントリが展開先の外を指しています(拒否): {name!r}")

            if member.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue

            if target in written_targets:
                raise FetchError(f"ZIPエントリの展開先パスが重複しています(拒否): {name!r}")
            written_targets.add(target)

            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(member) as src, target.open("wb") as dst:
                shutil.copyfileobj(src, dst)


def read_png_size(path):
    with path.open("rb") as f:
        header = f.read(33)
    if len(header) < 33 or header[:8] != b"\x89PNG\r\n\x1a\n":
        raise FetchError(f"PNGシグネチャが不正です: {path}")
    width, height = struct.unpack(">II", header[16:24])
    return width, height


def _atomic_replace(new_path, final_path):
    """new_path(final_pathと同じファイルシステム上にあることが前提)を
    final_pathへ原子的に入れ替える。ファイル・ディレクトリのどちらにも
    使える。

    final_pathが既存の場合はまず退避してから入れ替え、成功後に退避先を
    削除する。入れ替え(os.rename)自体が失敗した場合は退避しておいた
    元の内容を復元してから例外を送出する。これにより、途中で失敗しても
    final_pathは常に「入れ替え前の内容」か「入れ替え後の内容」の
    いずれかであり、消失・部分破損した状態にはならない。

    退避先のパスは呼び出しごとに一意な名前(pid+乱数)を使う。固定名だと
    (1)処理が中断した直後の再実行が復元前の唯一の旧アセットを削除する、
    (2)同時実行時に互いの退避内容を削除・混同する、という2種類の
    データ喪失経路がある。一意な名前にすることで、このメソッド自身が
    今回作った退避以外には一切触れない。
    """
    backup_path = final_path.parent / f"{final_path.name}.old-{os.getpid()}-{uuid.uuid4().hex[:8]}"

    had_existing = final_path.exists()
    if had_existing:
        final_path.rename(backup_path)

    try:
        new_path.rename(final_path)
    except OSError:
        if had_existing:
            if final_path.exists():
                if final_path.is_dir():
                    shutil.rmtree(final_path)
                else:
                    final_path.unlink()
            backup_path.rename(final_path)
        raise

    if had_existing and backup_path.exists():
        if backup_path.is_dir():
            shutil.rmtree(backup_path)
        else:
            backup_path.unlink()


@contextlib.contextmanager
def _character_lock(character_dir):
    """同一キャラクターに対するfetch_character()の同時実行を防ぐ。

    ロックファイルはcharacter_dir内(Git管理外、.gitignore対象)に作成
    する。flock(2)ベースのため、プロセスが異常終了してもOSが自動的に
    ロックを解放する(スタイルロックファイルの手動クリーンアップは
    不要)。
    """
    character_dir.mkdir(parents=True, exist_ok=True)
    lock_path = character_dir / ".fetch.lock"
    with lock_path.open("w") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file, fcntl.LOCK_UN)


# ---------------------------------------------------------------------------
# package/category 設定の読み込み
# ---------------------------------------------------------------------------

def _normalize_legacy_asset_json(config):
    """旧形式のasset.json(1キャラクター=1ZIP=表情のみ)を、新しい
    package表現へ変換する。フィールド値は一切変更しない(後方互換:
    同じdownload_url・sha256・zip_internal_root等をそのまま使う)。
    """
    required = (
        "release_tag",
        "filename",
        "download_url",
        "sha256",
        "size_bytes",
        "zip_internal_root",
        "expected_png_count",
        "expected_image_size",
    )
    missing = [k for k in required if k not in config]
    if missing:
        raise FetchError(f"asset.jsonに必須フィールドがありません: {missing}")

    return {
        "package_id": config.get("asset_version") or "expressions",
        "release_tag": config["release_tag"],
        "filename": config["filename"],
        "download_url": config["download_url"],
        "sha256": config["sha256"],
        "size_bytes": config["size_bytes"],
        "zip_internal_root": config["zip_internal_root"],
        "categories": [
            {
                "name": "expressions",
                "zip_subdir": "images",
                "place_to": "images",
                "manifest": "manifest.json",
                "expected_png_count": config["expected_png_count"],
                "expected_image_size": list(config["expected_image_size"]),
            }
        ],
    }


def _validate_category_shape(package_id, category):
    required = ("name", "zip_subdir", "place_to", "manifest", "expected_png_count")
    missing = [k for k in required if k not in category]
    if missing:
        raise FetchError(f"package {package_id!r} のcategory定義に必須フィールドがありません: {missing}")

    name = category["name"]
    if name.startswith("_") or name not in KNOWN_CATEGORIES:
        raise FetchError(
            f"package {package_id!r} のcategory名が不正です: {name!r}"
            f"(許可: {', '.join(sorted(KNOWN_CATEGORIES))})"
        )


def load_character_packages(character_dir):
    """character_dir配下のasset.json(旧形式・任意)とpackages.json
    (新形式・任意)を読み込み、統一されたpackage定義のリストを返す。

    package定義の形式(いずれも同じ形へ正規化される):
      {
        "package_id": str, "release_tag": str, "filename": str,
        "download_url": str, "sha256": str, "size_bytes": int,
        "zip_internal_root": str,
        "categories": [
          {"name": str, "zip_subdir": str, "place_to": str,
           "manifest": str, "expected_png_count": int,
           "expected_image_size": [int, int] または None},
          ...
        ],
      }
    """
    packages = []

    legacy_path = character_dir / "asset.json"
    if legacy_path.is_file():
        with legacy_path.open(encoding="utf-8") as f:
            legacy_config = json.load(f)
        packages.append(_normalize_legacy_asset_json(legacy_config))

    packages_path = character_dir / "packages.json"
    if packages_path.is_file():
        with packages_path.open(encoding="utf-8") as f:
            packages_config = json.load(f)
        for package in packages_config.get("packages", []):
            required = (
                "package_id",
                "release_tag",
                "filename",
                "download_url",
                "sha256",
                "size_bytes",
                "zip_internal_root",
                "categories",
            )
            missing = [k for k in required if k not in package]
            if missing:
                raise FetchError(f"packages.jsonのpackage定義に必須フィールドがありません: {missing}")
            packages.append(package)

    if not packages:
        raise FetchError(f"asset.jsonまたはpackages.jsonが見つかりません: {character_dir}")

    for package in packages:
        if not package["categories"]:
            raise FetchError(f"package {package['package_id']!r} にcategoryが1つもありません")
        for category in package["categories"]:
            _validate_category_shape(package["package_id"], category)

    _validate_no_place_to_collisions(packages)
    return packages


def _validate_no_place_to_collisions(packages):
    """同一キャラクター内で、複数のcategoryが同じ配置先(place_to)を
    指していないことを確認する。
    """
    seen = {}
    for package in packages:
        for category in package["categories"]:
            place_to = category["place_to"]
            owner = f"{package['package_id']}/{category['name']}"
            if place_to in seen:
                raise FetchError(
                    f"カテゴリ間の配置先が衝突しています: {place_to!r}"
                    f"({seen[place_to]!r} と {owner!r})"
                )
            seen[place_to] = owner


# ---------------------------------------------------------------------------
# 取得・検証・配置
# ---------------------------------------------------------------------------

def _load_category_manifest(character_dir, category):
    manifest_path = character_dir / category["manifest"]
    if not manifest_path.is_file():
        raise FetchError(f"manifest.jsonが見つかりません: {manifest_path}")
    with manifest_path.open(encoding="utf-8") as f:
        return json.load(f)


def _verify_category(character_dir, staging_dir, category):
    """1つのcategoryについて、PNG枚数・manifest網羅・画像サイズを検証する。"""
    zip_subdir_path = staging_dir / category["zip_subdir"]
    if not zip_subdir_path.is_dir():
        raise FetchError(
            f"展開結果に{category['zip_subdir']}/ディレクトリがありません(category={category['name']})"
        )

    pngs = sorted(zip_subdir_path.glob("*.png"))
    expected_count = category["expected_png_count"]
    if len(pngs) != expected_count:
        raise FetchError(
            f"PNG枚数が不正です(category={category['name']}): {len(pngs)}枚(期待: {expected_count}枚)"
        )

    manifest = _load_category_manifest(character_dir, category)
    uniform_size = category.get("expected_image_size")

    missing = []
    for tag, entry in manifest.items():
        if tag.startswith("_"):
            continue
        filename = entry["file"] if isinstance(entry, dict) else entry
        file_path = zip_subdir_path / filename
        if not file_path.is_file():
            missing.append((tag, filename))
            continue
        if isinstance(entry, dict) and "width" in entry and "height" in entry:
            w, h = read_png_size(file_path)
            if (w, h) != (entry["width"], entry["height"]):
                raise FetchError(
                    f"画像サイズが不正です(category={category['name']}): {filename} = {w}x{h}"
                    f"(期待: {entry['width']}x{entry['height']})"
                )
    if missing:
        raise FetchError(
            f"manifest.jsonが参照するファイルが展開結果にありません(category={category['name']}): {missing}"
        )

    if uniform_size is not None:
        expected_w, expected_h = uniform_size
        for png in pngs:
            w, h = read_png_size(png)
            if (w, h) != (expected_w, expected_h):
                raise FetchError(
                    f"画像サイズが不正です(category={category['name']}): {png.name} = {w}x{h}"
                    f"(期待: {expected_w}x{expected_h})"
                )


def _place_category(character_dir, staging_dir, category):
    src = staging_dir / category["zip_subdir"]
    dest = character_dir / category["place_to"]
    dest.parent.mkdir(parents=True, exist_ok=True)
    _atomic_replace(src, dest)


def _package_already_fetched(character_dir, package):
    return all((character_dir / category["place_to"]).exists() for category in package["categories"])


def _fetch_package(character_dir, package, force=False):
    name = character_dir.name
    package_id = package["package_id"]

    if _package_already_fetched(character_dir, package) and not force:
        print(f"[{name}/{package_id}] 既に取得済みです(スキップ。再取得するには --force を指定)")
        return

    print(f"[{name}/{package_id}] 設定読み込み完了: {package['filename']} (release={package['release_tag']})")

    # dir=character_dir.parent を指定し、一時ディレクトリを正式配置先と
    # 同じファイルシステム上に作る。これにより後続のos.rename
    # (Path.rename)による入れ替えが真に原子的になる。
    with tempfile.TemporaryDirectory(prefix=f".fetch_{name}_{package_id}_", dir=character_dir.parent) as tmp:
        tmp_path = Path(tmp)
        zip_path = tmp_path / package["filename"]

        print(f"[{name}/{package_id}] ダウンロード中: {package['download_url']}")
        download_file(package["download_url"], zip_path)

        actual_size = zip_path.stat().st_size
        if actual_size != package["size_bytes"]:
            raise FetchError(
                f"ファイルサイズが不正です(展開・利用しません): 実測={actual_size} 期待={package['size_bytes']}"
            )

        actual_sha256 = compute_sha256(zip_path)
        if actual_sha256 != package["sha256"]:
            raise FetchError(
                f"SHA-256が不一致です(展開・利用しません): 実測={actual_sha256} 期待={package['sha256']}"
            )
        print(f"[{name}/{package_id}] SHA-256検証OK: {actual_sha256}")

        staging_dir = tmp_path / "staging"
        safe_extract(zip_path, staging_dir, strip_prefix=package["zip_internal_root"])

        # packageに属する全categoryの検証を先にすべて済ませ、1つでも
        # 失敗すれば正式配置には一切触れない(全カテゴリの検証完了後
        # のみ原子的に正式配置する)。
        for category in package["categories"]:
            _verify_category(character_dir, staging_dir, category)
        print(f"[{name}/{package_id}] 全カテゴリ検証OK({len(package['categories'])}カテゴリ)")

        for category in package["categories"]:
            _place_category(character_dir, staging_dir, category)

        index_html_src = staging_dir / "index.html"
        if index_html_src.is_file():
            _atomic_replace(index_html_src, character_dir / "index.html")

        print(f"[{name}/{package_id}] 配置完了")


def fetch_character(character_dir, force=False):
    with _character_lock(character_dir):
        packages = load_character_packages(character_dir)
        for package in packages:
            _fetch_package(character_dir, package, force=force)


def discover_character_dirs():
    if not REFERENCE_IMAGES_ROOT.is_dir():
        return []
    dirs = set()
    for p in REFERENCE_IMAGES_ROOT.glob("*/asset.json"):
        dirs.add(p.parent)
    for p in REFERENCE_IMAGES_ROOT.glob("*/packages.json"):
        dirs.add(p.parent)
    return sorted(dirs)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--character",
        action="append",
        help="取得するキャラクター名(reference_images/<name>/)。複数指定可。"
        "省略時はasset.jsonまたはpackages.jsonを持つ全キャラクターを対象にする",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="既に取得済みのpackageがあっても再取得・再検証して置き換える",
    )
    args = parser.parse_args()

    if args.character:
        character_dirs = [REFERENCE_IMAGES_ROOT / name for name in args.character]
    else:
        character_dirs = discover_character_dirs()

    if not character_dirs:
        print("[ERROR] 取得対象のキャラクターが見つかりません", file=sys.stderr)
        sys.exit(1)

    failures = []
    for character_dir in character_dirs:
        try:
            fetch_character(character_dir, force=args.force)
        except FetchError as e:
            print(f"[ERROR] {character_dir.name}: {e}", file=sys.stderr)
            failures.append(character_dir.name)
        except OSError as e:
            print(f"[ERROR] {character_dir.name}: 入出力エラー: {e}", file=sys.stderr)
            failures.append(character_dir.name)

    if failures:
        print(f"[ERROR] 失敗: {', '.join(failures)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
