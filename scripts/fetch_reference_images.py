#!/usr/bin/env python3
"""異世界ニホンマンガ用キャラクター参照画像(表情セット)を、GitHub Release
から取得・検証・配置するスクリプト。

profiles/sdxl/isekai_nihon_manga/reference_images/<character>/asset.json
の内容に従い、正本ZIPをダウンロードし、SHA-256・PNG枚数・画像サイズを
検証したうえで、同ディレクトリ配下(images/・index.html)へ展開する。
ZIP本体・展開後のPNGはGit管理外(GitHub Release assetとして保管)。

安全条件(チャミ承認済み仕様):

- ダウンロード完了後にSHA-256を照合する。不一致なら展開・利用しない
- 展開後、PNG枚数と全画像サイズ(asset.jsonの期待値)を検証する
- ダウンロード・展開・検証はすべて一時ディレクトリで行い、全て合格した
  場合にのみ正式配置(<character>/images/, <character>/index.html)へ
  移動する。検証前に既存の正式配置を上書きしない
- 展開先ディレクトリの外へ書き込むZIPエントリ(zip slip)は拒否する
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
import hashlib
import json
import shutil
import struct
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REFERENCE_IMAGES_ROOT = ROOT / "profiles" / "sdxl" / "isekai_nihon_manga" / "reference_images"


class FetchError(Exception):
    """取得・検証のいずれかの段階で失敗したことを表す。"""


def load_asset_config(character_dir):
    asset_path = character_dir / "asset.json"
    if not asset_path.is_file():
        raise FetchError(f"asset.jsonが見つかりません: {asset_path}")
    with asset_path.open(encoding="utf-8") as f:
        return json.load(f)


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
    """zip slip対策つきの展開。

    ZIP内の各エントリ名から先頭の strip_prefix(ZIP内部のトップレベル
    フォルダ名)を取り除いたうえで、dest_dir配下にのみ書き込む。
    絶対パス・".."等でdest_dirの外を指すエントリは拒否する。
    """
    dest_dir = dest_dir.resolve()
    dest_dir.mkdir(parents=True, exist_ok=True)
    prefix = strip_prefix.rstrip("/") + "/"

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


def verify_extracted_images(staging_dir, config):
    images_dir = staging_dir / "images"
    if not images_dir.is_dir():
        raise FetchError("展開結果にimages/ディレクトリがありません")

    pngs = sorted(images_dir.glob("*.png"))
    expected_count = config["expected_png_count"]
    if len(pngs) != expected_count:
        raise FetchError(f"PNG枚数が不正です: {len(pngs)}枚(期待: {expected_count}枚)")

    expected_w, expected_h = config["expected_image_size"]
    for png in pngs:
        w, h = read_png_size(png)
        if (w, h) != (expected_w, expected_h):
            raise FetchError(
                f"画像サイズが不正です: {png.name} = {w}x{h}(期待: {expected_w}x{expected_h})"
            )


def _atomic_replace(new_path, final_path):
    """new_path(final_pathと同じファイルシステム上にあることが前提)を
    final_pathへ原子的に入れ替える。ファイル・ディレクトリのどちらにも
    使える。

    final_pathが既存の場合はまず退避してから入れ替え、成功後に退避先を
    削除する。入れ替え(os.rename)自体が失敗した場合は退避しておいた
    元の内容を復元してから例外を送出する。これにより、途中で失敗しても
    final_pathは常に「入れ替え前の内容」か「入れ替え後の内容」の
    いずれかであり、消失・部分破損した状態にはならない(Codexレビュー
    指摘: 旧shutil.rmtree→shutil.moveの2段階処理は、異なるファイル
    システム間の移動失敗や処理中断時に旧アセットを失う恐れがあった)。
    """
    backup_path = final_path.parent / (final_path.name + ".old-tmp")
    if backup_path.exists():
        if backup_path.is_dir():
            shutil.rmtree(backup_path)
        else:
            backup_path.unlink()

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


def verify_manifest_coverage(staging_dir, manifest_path):
    """manifest.jsonが参照する全ファイルが、展開結果に実在することを確認する。"""
    with manifest_path.open(encoding="utf-8") as f:
        manifest = json.load(f)
    images_dir = staging_dir / "images"
    missing = [
        (tag, filename)
        for tag, filename in manifest.items()
        if not tag.startswith("_") and not (images_dir / filename).is_file()
    ]
    if missing:
        raise FetchError(f"manifest.jsonが参照するファイルが展開結果にありません: {missing}")


def fetch_character(character_dir, force=False):
    name = character_dir.name
    final_images_dir = character_dir / "images"
    if final_images_dir.exists() and not force:
        print(f"[{name}] images/ は既に存在します(スキップ。再取得するには --force を指定)")
        return

    config = load_asset_config(character_dir)
    manifest_path = character_dir / "manifest.json"
    if not manifest_path.is_file():
        raise FetchError(f"manifest.jsonが見つかりません: {manifest_path}")

    print(f"[{name}] 設定読み込み完了: {config['filename']} (release={config['release_tag']})")

    # dir=character_dir.parent を指定し、一時ディレクトリを正式配置先と
    # 同じファイルシステム上に作る。これにより後続のos.rename(Path.rename)
    # による入れ替えが真に原子的になる(異なるファイルシステム間だと
    # renameできずcopy+削除にフォールバックし、部分失敗の余地が生まれる
    # ため。Codexレビュー指摘)。
    with tempfile.TemporaryDirectory(prefix=f".fetch_{name}_", dir=character_dir.parent) as tmp:
        tmp_path = Path(tmp)
        zip_path = tmp_path / config["filename"]

        print(f"[{name}] ダウンロード中: {config['download_url']}")
        download_file(config["download_url"], zip_path)

        actual_size = zip_path.stat().st_size
        if actual_size != config["size_bytes"]:
            raise FetchError(
                f"ファイルサイズが不正です(展開・利用しません): 実測={actual_size} 期待={config['size_bytes']}"
            )

        actual_sha256 = compute_sha256(zip_path)
        if actual_sha256 != config["sha256"]:
            raise FetchError(
                f"SHA-256が不一致です(展開・利用しません): 実測={actual_sha256} 期待={config['sha256']}"
            )
        print(f"[{name}] SHA-256検証OK: {actual_sha256}")

        staging_dir = tmp_path / "staging"
        safe_extract(zip_path, staging_dir, strip_prefix=config["zip_internal_root"])

        verify_extracted_images(staging_dir, config)
        verify_manifest_coverage(staging_dir, manifest_path)
        print(
            f"[{name}] 展開・検証OK(PNG {config['expected_png_count']}枚、"
            f"{tuple(config['expected_image_size'])})"
        )

        # ここまでの処理はすべて一時ディレクトリ内で完結しており、正式配置
        # (character_dir/images, character_dir/index.html)には一切触れて
        # いない。全検証に合格した場合にのみ、ここで初めて原子的に反映する。
        _atomic_replace(staging_dir / "images", final_images_dir)

        index_html_src = staging_dir / "index.html"
        if index_html_src.is_file():
            _atomic_replace(index_html_src, character_dir / "index.html")

        print(f"[{name}] 配置完了: {final_images_dir}")


def discover_character_dirs():
    if not REFERENCE_IMAGES_ROOT.is_dir():
        return []
    return sorted(p.parent for p in REFERENCE_IMAGES_ROOT.glob("*/asset.json"))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--character",
        action="append",
        help="取得するキャラクター名(reference_images/<name>/)。複数指定可。"
        "省略時はasset.jsonを持つ全キャラクターを対象にする",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="既存のimages/があっても再取得・再検証して置き換える",
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
