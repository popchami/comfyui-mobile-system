"""scripts/fetch_reference_images.py と scripts/resolve_reference_image.py
で共有するカテゴリ定義。

以前はKNOWN_CATEGORIES等が2ファイルに独立して重複定義されており、片方
だけを更新すると「取得はできるが解決できない」「解決はできるが未実装の
KeyErrorになる」といった drift が起こりうる状態だった(Codexレビュー
指摘、Minor)。ここで一元管理する。

CATEGORY_PLACE_TO・CATEGORY_MANIFEST_REL は正本(コード側の固定値)であり、
packages.json/asset.json側の place_to・manifest フィールドは、対応する
categoryのこの正本値と一致することを要求する(値そのものを設定ファイル側
の自由入力として信頼しない)。これは、設定ファイル経由のpath traversal
(例: place_to: "../../outside")を構造的に防ぐための設計変更でもある
(Codexレビュー指摘、Critical)。将来 poses / training 等の新カテゴリを
追加する場合は、ここに1箇所追加するだけでよい。
"""

DEFAULT_CATEGORY = "expressions"

CATEGORY_PLACE_TO = {
    "expressions": "images",
    "turnaround": "turnaround/images",
    "equipment": "equipment/images",
}
CATEGORY_MANIFEST_REL = {
    "expressions": "manifest.json",
    "turnaround": "turnaround/manifest.json",
    "equipment": "equipment/manifest.json",
}

KNOWN_CATEGORIES = frozenset(CATEGORY_PLACE_TO)

assert set(CATEGORY_PLACE_TO) == set(CATEGORY_MANIFEST_REL)
