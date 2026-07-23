#!/usr/bin/env python3
"""profiles/sdxl/isekai_nihon_manga/five_panel_template.json(5コマテンプレート
座標の数値正本)から、人間向けMarkdown(five_panel_template.md)を生成する。

数値の正本はJSON側であり、Markdownは常にJSONから生成する(手書きしない)。
これにより、JSONとMarkdownの数値が食い違う事態を構造的に防止する
(tests/test_five_panel_template.py で、生成結果と実際にコミットされている
five_panel_template.mdが一致することを検証する)。
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_JSON_PATH = ROOT / "profiles" / "sdxl" / "isekai_nihon_manga" / "five_panel_template.json"
TEMPLATE_MD_PATH = ROOT / "profiles" / "sdxl" / "isekai_nihon_manga" / "five_panel_template.md"


def _rect_row(label, rect):
    return f"| {label} | {rect['x']} | {rect['y']} | {rect['width']} | {rect['height']} |"


def generate_markdown(data):
    canvas = data["canvas"]
    border = data["border"]
    lines = []
    lines.append("# 5コマ構成 正本テンプレート仕様")
    lines.append("")
    lines.append(
        "このファイルは `five_panel_template.json`(数値の正本)から "
        "`scripts/generate_five_panel_template_doc.py` により自動生成される。"
        "**このファイルを直接編集しないこと。** 数値を変更する場合は "
        "`five_panel_template.json` を編集し、生成スクリプトを再実行すること。"
    )
    lines.append("")
    lines.append("news-game-translator側のManga News Packet(`panels`、第1〜4コマ)は "
                  "このテンプレートの1〜4番目のコマに対応し、`scribe_panel`(第5コマ)は "
                  "5番目のコマに対応する。Packetのデータ構造自体はnews-game-translator側 "
                  "`prompts/manga_script.md`・`scripts/manga_schema.py`を正とし、本文書は "
                  "完成画像の物理レイアウト(座標・枠線・コマ間隔)のみを扱う。")
    lines.append("")
    lines.append("## 完成画像全体")
    lines.append("")
    lines.append(f"- 画像サイズ: {canvas['width']}×{canvas['height']}px")
    lines.append(f"- 背景色: {canvas['background']}")
    lines.append(f"- コマ数: {data['panel_count']}")
    lines.append(f"- 枠線: {border['color']} {border['width_px']}px")
    lines.append(f"- コマ間の間隔: {data['panel_gap_px']}px(白背景)")
    lines.append("")
    lines.append(
        "各コマの背景画像を配置した後、黒枠(枠線)を最前面へ重ねる"
        "(`compositing_order`: " + " → ".join(data["compositing_order"]) + ")。"
    )
    lines.append("")
    lines.append("## コマ役割")
    lines.append("")
    lines.append("| コマ | 役割 |")
    lines.append("|---|---|")
    lines.append("| 第1コマ | 起(出来事の発生・発見) |")
    lines.append("| 第2コマ | 承(疑問・影響の広がり) |")
    lines.append("| 第3コマ | 転(別角度、条件、未決定事項、誤解の修正) |")
    lines.append("| 第4コマ | 結(現在地と次の手続き。第5コマへつなぐ) |")
    lines.append("| 第5コマ | 書記官による現実ニュースの事実整理 |")
    lines.append("")
    lines.append("## 外枠(黒枠を含む領域)の座標")
    lines.append("")
    lines.append("| コマ | x | y | width | height |")
    lines.append("|---|---|---|---|---|")
    for panel in data["panels"]:
        lines.append(_rect_row(f"第{panel['panel_no']}コマ", panel["outer"]))
    lines.append("")
    lines.append("## 各コマ内側(枠線の内側)の座標")
    lines.append("")
    lines.append("| コマ | x | y | width | height |")
    lines.append("|---|---|---|---|---|")
    for panel in data["panels"]:
        lines.append(_rect_row(f"第{panel['panel_no']}コマ", panel["inner"]))
    lines.append("")
    lines.append("## 安全領域(内側からさらに内側の座標。人物の顔・手・必須装備・吹き出し・文字はここに収める)")
    lines.append("")
    lines.append("| コマ | x | y | width | height |")
    lines.append("|---|---|---|---|---|")
    for panel in data["panels"]:
        lines.append(_rect_row(f"第{panel['panel_no']}コマ", panel["safe_area"]))
    lines.append("")
    lines.append(
        "背景だけはコマ内側全体へ配置してよい(安全領域の制約を受けない)。"
        "人物の顔・手・必須装備・吹き出し・文字は安全領域内に収めること。"
    )
    lines.append("")
    lines.append("## 画像生成AIに描かせないもの")
    lines.append("")
    for item in data["ai_generation_exclusions"]:
        lines.append(f"- `{item}`")
    lines.append("")
    lines.append("## 第5コマ(書記官の解説)のレイアウト")
    lines.append("")
    scribe_layout = data["scribe_panel_layout"]
    lines.append(f"- レイアウトID: `{scribe_layout['layout_id']}`"
                  "(Manga News Packetの`scribe_panel.layout`固定値と一致させる)")
    lines.append(f"- 見出し(固定文言): 「{scribe_layout['heading_fixed_text']}」")
    lines.append(
        f"- 書記官領域: 安全領域の約{int(scribe_layout['scribe_area_fraction_of_safe_area'] * 100)}%"
        "(左側)"
    )
    lines.append(
        f"- 解説欄: 安全領域の約{int(scribe_layout['note_area_fraction_of_safe_area'] * 100)}%"
        "(右側)"
    )
    lines.append("- 書記官は左手にタブレット、右手にペンを持つ。書記局章を解説欄またはタブレット付近へ配置する")
    lines.append("")
    lines.append("## 基準文字サイズ(最小値)")
    lines.append("")
    font_sizes = data["font_size_px_min"]
    lines.append("| 用途 | 最小サイズ |")
    lines.append("|---|---|")
    lines.append(f"| セリフ | {font_sizes['dialogue']}px以上 |")
    lines.append(f"| 第5コマ見出し | {font_sizes['scribe_heading']}px以上 |")
    lines.append(f"| 第5コマ本文 | {font_sizes['scribe_body']}px以上 |")
    lines.append("")
    lines.append(
        "文字量が多い場合に文字を小さくして収める処理は禁止する。上限を超えた場合は "
        "検証エラーにする(文字数制限はnews-game-translator側`scripts/manga_schema.py`を参照)。"
    )

    return "\n".join(lines) + "\n"


def main():
    with TEMPLATE_JSON_PATH.open(encoding="utf-8") as f:
        data = json.load(f)
    markdown = generate_markdown(data)

    if "--check" in sys.argv:
        if not TEMPLATE_MD_PATH.is_file():
            print(f"[ERROR] {TEMPLATE_MD_PATH} が存在しません", file=sys.stderr)
            sys.exit(1)
        current = TEMPLATE_MD_PATH.read_text(encoding="utf-8")
        if current != markdown:
            print(
                f"[ERROR] {TEMPLATE_MD_PATH} が {TEMPLATE_JSON_PATH} と一致しません"
                "(このスクリプトを--checkなしで再実行して再生成してください)",
                file=sys.stderr,
            )
            sys.exit(1)
        print("OK: five_panel_template.md is up to date")
        return

    TEMPLATE_MD_PATH.write_text(markdown, encoding="utf-8")
    print(f"generated: {TEMPLATE_MD_PATH}")


if __name__ == "__main__":
    main()
