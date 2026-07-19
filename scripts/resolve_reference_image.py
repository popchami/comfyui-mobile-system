#!/usr/bin/env python3
"""Manga News Packetのreference_image(論理ID)を実ファイルへ解決する。

news-game-translator側のPacketは、reference_imageを実ファイルへの直接
パスではなく `<character>/<expression>.png` 形式の論理ID(例:
`haruto/surprise-medium.png`)として持つ(数字接頭辞なし)。LLM(脚本生成
プロンプト)には数字接頭辞を一切生成させない。

このモジュールは、論理IDを
profiles/sdxl/isekai_nihon_manga/reference_images/<character>/manifest.json
と突き合わせて、実ファイル(例: `05-surprise-medium.png`)への絶対パスを
返す。実ファイル本体(images/配下)は scripts/fetch_reference_images.py に
よる取得後にのみ存在する(Git管理外)。

標準ライブラリのみを使用する。
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REFERENCE_IMAGES_ROOT = ROOT / "profiles" / "sdxl" / "isekai_nihon_manga" / "reference_images"

# <character>/<expression>.png 形式のみを受け付ける(ディレクトリトラバー
# サル対策。character・expressionはASCII英数字・._-のみ許可する)。
REFERENCE_IMAGE_RE = re.compile(
    r"^(?P<character>[A-Za-z0-9._-]+)/(?P<expression>[A-Za-z0-9._-]+)\.png$"
)


class ResolveError(Exception):
    """reference_imageの解決に失敗したことを表す。"""


def parse_reference_image(reference_image):
    """reference_image文字列を (character, expression) に分解する。

    形式が不正な場合はResolveErrorを送出する。
    """
    m = REFERENCE_IMAGE_RE.match(reference_image or "")
    if not m:
        raise ResolveError(f"reference_imageの形式が不正です: {reference_image!r}")
    return m.group("character"), m.group("expression")


def load_manifest(character):
    manifest_path = REFERENCE_IMAGES_ROOT / character / "manifest.json"
    if not manifest_path.is_file():
        raise ResolveError(f"manifest.jsonが見つかりません: {manifest_path}")
    with manifest_path.open(encoding="utf-8") as f:
        return json.load(f)


def resolve_reference_image(reference_image, require_file_exists=True):
    """reference_image(論理ID)から実ファイルへの絶対パスを返す。

    require_file_exists=Trueの場合、実ファイル(images/配下、
    scripts/fetch_reference_images.py取得後にのみ存在)が実在しなければ
    ResolveErrorを送出する。Falseの場合はパスの組み立てのみ行い、実在
    確認はしない(参照画像未取得の段階で解決ロジック自体を検証したい
    場合等に使う)。
    """
    character, expression = parse_reference_image(reference_image)
    manifest = load_manifest(character)

    filename = manifest.get(expression)
    if filename is None:
        raise ResolveError(
            f"manifest.jsonに表情タグ{expression!r}の対応がありません(character={character!r})"
        )

    image_path = REFERENCE_IMAGES_ROOT / character / "images" / filename
    if require_file_exists and not image_path.is_file():
        raise ResolveError(
            f"解決した実ファイルが存在しません: {image_path}"
            "(scripts/fetch_reference_images.py で取得済みか確認してください)"
        )
    return image_path


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("reference_image", help="Packetのreference_image(例: haruto/surprise-medium.png)")
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
