#!/usr/bin/env python3
"""Manga News Packetのreference_image(論理ID)を実ファイルへ解決する。

news-game-translator側のPacketは、reference_imageを実ファイルへの直接
パスではなく論理IDとして持つ。2つの形式をサポートする:

- `<character>/<expression-tag>.png`(表情、既存互換。category省略時は
  暗黙に"expressions"として扱う。例: `haruto/surprise-medium.png`)
- `<character>/<category>/<tag>.png`(表情以外の新カテゴリ、または
  表情を明示的にcategory付きで指定する場合。例:
  `haruto/turnaround/front.png`、`natsuki/equipment/mitsugake-right.png`)

LLM(脚本生成プロンプト)には数字接頭辞を一切生成させない。

このモジュールは、論理IDを
profiles/sdxl/isekai_nihon_manga/reference_images/<character>/
配下の該当categoryのmanifest.jsonと突き合わせて、実ファイルへの
絶対パスを返す。実ファイル本体はscripts/fetch_reference_images.pyに
よる取得後にのみ存在する(Git管理外)。

標準ライブラリのみを使用する。
"""
import argparse
import json
import re
import sys
from pathlib import Path

from reference_image_categories import CATEGORY_MANIFEST_REL, CATEGORY_PLACE_TO, DEFAULT_CATEGORY, KNOWN_CATEGORIES

ROOT = Path(__file__).resolve().parent.parent
REFERENCE_IMAGES_ROOT = ROOT / "profiles" / "sdxl" / "isekai_nihon_manga" / "reference_images"

# <character>/[<category>/]<tag>.png 形式のみを受け付ける
# (ディレクトリトラバーサル対策。各セグメントはASCII英数字・._-のみ許可)。
REFERENCE_IMAGE_RE = re.compile(
    r"^(?P<character>[A-Za-z0-9._-]+)/"
    r"(?:(?P<category>[A-Za-z0-9._-]+)/)?"
    r"(?P<tag>[A-Za-z0-9._-]+)\.png$"
)

# "."・".."等、ドットのみで構成されるセグメントを拒否する
# (character/categoryはそのままファイルシステムパスへ使われるため、
# ".."単体がセグメントとして通ってしまうとディレクトリトラバーサルに
# つながる。文字クラス自体は"."を含む正当な名前も許可する必要があるため、
# ここで別途明示的に弾く)。
_DOT_ONLY_RE = re.compile(r"^\.+$")


class ResolveError(Exception):
    """reference_imageの解決に失敗したことを表す。"""


def _resolve_contained(base_dir, relative_path, description):
    """base_dir配下に厳密に収まる形でrelative_pathを解決する。

    manifest.json内のファイル名は、reference_image自体の形式検証
    (character/category/tagのセグメント制限)の対象外であり、
    "../../../outside.png"のような値を書けばcategoryの画像ディレクトリの
    外を指せてしまう(Codexレビュー指摘、Critical)。ここで別途検証する。
    """
    base_dir = base_dir.resolve()
    target = (base_dir / relative_path).resolve()
    if target != base_dir and base_dir not in target.parents:
        raise ResolveError(f"{description}がベースディレクトリの外を指しています(拒否): {relative_path!r}")
    return target


def parse_reference_image(reference_image):
    """reference_image文字列を (character, category, tag) に分解する。

    categoryが省略された場合はDEFAULT_CATEGORY("expressions")を返す。
    形式が不正、予約語("_"始まり)、ドットのみのセグメント、未知の
    categoryの場合はResolveErrorを送出する。
    """
    m = REFERENCE_IMAGE_RE.match(reference_image or "")
    if not m:
        raise ResolveError(f"reference_imageの形式が不正です: {reference_image!r}")

    character = m.group("character")
    category = m.group("category") or DEFAULT_CATEGORY
    tag = m.group("tag")

    # "_"始まりはmanifest.json内の予約キー(例: "_comment")であり、実在の
    # タグではない(Codexレビュー指摘: "haruto/_comment.png"が
    # manifest.get("_comment")の説明文字列へ解決されてしまっていた)。
    # ".."等ドットのみのセグメントは、character/categoryがそのまま
    # ファイルシステムパスへ使われるため、ディレクトリトラバーサル対策
    # として別途明示的に拒否する。
    for seg in (character, category, tag):
        if seg.startswith("_"):
            raise ResolveError(f"reference_imageに予約語(_始まり)は使用できません: {reference_image!r}")
        if _DOT_ONLY_RE.match(seg):
            raise ResolveError(f"reference_imageのセグメントに不正な値が含まれています: {seg!r}")

    if category not in KNOWN_CATEGORIES:
        raise ResolveError(
            f"未知のcategoryです: {category!r}(許可: {', '.join(sorted(KNOWN_CATEGORIES))})"
        )

    return character, category, tag


def load_manifest(character, category):
    manifest_path = REFERENCE_IMAGES_ROOT / character / CATEGORY_MANIFEST_REL[category]
    if not manifest_path.is_file():
        raise ResolveError(f"manifest.jsonが見つかりません: {manifest_path}")
    with manifest_path.open(encoding="utf-8") as f:
        return json.load(f)


def resolve_reference_image(reference_image, require_file_exists=True):
    """reference_image(論理ID)から実ファイルへの絶対パスを返す。

    require_file_exists=Trueの場合、実ファイル(取得後にのみ存在)が
    実在しなければResolveErrorを送出する。Falseの場合はパスの組み立て
    のみ行い、実在確認はしない。
    """
    character, category, tag = parse_reference_image(reference_image)
    manifest = load_manifest(character, category)

    entry = manifest.get(tag)
    if entry is None:
        raise ResolveError(
            f"manifest.jsonにタグ{tag!r}の対応がありません(character={character!r}, category={category!r})"
        )
    filename = entry["file"] if isinstance(entry, dict) else entry

    images_dir = REFERENCE_IMAGES_ROOT / character / CATEGORY_PLACE_TO[category]
    image_path = _resolve_contained(images_dir, filename, "manifestのファイル名")
    if require_file_exists and not image_path.is_file():
        raise ResolveError(
            f"解決した実ファイルが存在しません: {image_path}"
            "(scripts/fetch_reference_images.py で取得済みか確認してください)"
        )
    return image_path


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "reference_image",
        help="Packetのreference_image(例: haruto/surprise-medium.png、haruto/turnaround/front.png)",
    )
    parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="実ファイルがまだ取得されていなくてもパス組み立てのみ行う",
    )
    args = parser.parse_args()

    try:
        path = resolve_reference_image(args.reference_image, require_file_exists=not args.allow_missing)
    except ResolveError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)

    print(path)


if __name__ == "__main__":
    main()
