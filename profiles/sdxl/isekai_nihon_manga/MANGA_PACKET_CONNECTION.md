# Manga News Packet 接続契約(news-game-translator ⇔ comfyui-mobile-system)

このファイルは、news-game-translator側が生成するManga News Packet
(`scripts/manga_schema.py`、PACKET_VERSION 2)と、このリポジトリ側の
キャラクター参照画像・5コマテンプレートとの接続方法を、両リポジトリの
どちらか片方だけを見ても迷わないように記録する。データ構造そのものの
正本はnews-game-translator側、物理レイアウト(座標)の正本はこちら側。

## 1. キャラクター名の対応(日本語表示名 ⇔ ローマ字ID)

Manga News Packetの`characters`・`performers[].name`は日本語表示名を使う。
参照画像フォルダ名(`reference_images/<id>/`)はローマ字IDを使う。対応は
以下の固定表で、news-game-translator側`scripts/manga_schema.py`の
`CHARACTER_REFERENCE_ID`が正本(この表と食い違う場合はコード側を正とする)。

| Packetの表示名 | ローマ字ID(このリポジトリのフォルダ名) |
|---|---|
| ハルト | `haruto` |
| ナツキ | `natsuki` |
| アキラ | `akira` |
| フユミ | `fuyumi` |
| 書記官 | `scribe` |

## 2. reference_image(論理ID)の形式

Packetの`performers[].reference_image`・`scribe_panel.reference_image`は、
`<ローマ字ID>/<表情タグ>.png`形式(例: `haruto/surprise-medium.png`)。
`<表情タグ>`は同じperformer/scribe_panelの`expression`フィールドと
必ず一致させる(news-game-translator側で機械検証済み)。

`scribe_panel.emblem_reference`は固定値
`scribe/equipment/official-scribe-bureau-emblem.png`(書記局章、
アキラ・ナツキの装備〔equipment〕カテゴリと同じ仕組みで登録済み)。

論理IDから実ファイルへの解決ロジックは、このリポジトリの
`scripts/resolve_reference_image.py`を正とする(`category`省略時は
`expressions`扱い、`equipment/`等の明示的なcategoryセグメントも解決可能)。

## 3. 表情タグ(31種)

ハルト・ナツキ・アキラ・フユミ・書記官の5キャラクターとも同一の31種
タグ体系(`00-neutral`〜`30-speaking-forceful`相当)を使う。タグの一覧・
用途・避ける場面の対応表は、news-game-translator側
`prompts/manga_script.md`を正本とする(このリポジトリ側では重複記載
しない。各キャラクターの`reference_images/<id>/manifest.json`は
タグ→実ファイル名の対応のみを持つ)。

## 4. 5コマの物理レイアウト

完成画像(1080×1920px、5コマ)の座標・枠線・コマ間隔・基準文字サイズは
`five_panel_template.json`(数値の正本)・`five_panel_template.md`
(人間向け解説、JSONから自動生成)を参照。Packetの`panels`(第1〜4コマ)
はテンプレートの1〜4番目のコマ、`scribe_panel`(第5コマ)は5番目のコマに
対応する。

## 5. コマの構図・吹き出しenum(2026-07-24追加)

Packetの`panels[].camera_angle`・`panels[].framing`・
`dialogues[].bubble_position`は、いずれも固定enumであり自由記述ではない
(表記揺れによる検証回避を防ぐため)。正本は
news-game-translator側`scripts/manga_schema.py`の
`CAMERA_ANGLES`・`FRAMINGS`・`BUBBLE_POSITIONS`。このリポジトリ側で
SDXL Workflow・`image_prompt`生成を実装する際は、以下を参照する。

| フィールド | 値 | 用途 |
|---|---|---|
| `camera_angle` | `eye_level`/`high_angle`/`low_angle`/`over_shoulder`/`top_down` | カメラの高さ・角度。画像生成プロンプト構築で使用 |
| `framing` | `close_up`/`bust`/`waist`/`full`/`wide` | フレーミング(ショットサイズ)。画像生成プロンプト構築で使用 |
| `bubble_position` | `upper_left`/`upper_center`/`upper_right`/`lower_left`/`lower_center`/`lower_right` | 吹き出し本体の上下左右配置(後処理の機械合成でのみ使用、画像生成AIには吹き出しを描かせない) |

`bubble_position`は吹き出し**本体**の位置であり、話者
(`performers[].position`、`left`/`center`/`right`の別enum)の位置とは
一致しない。吹き出しの尾は`dialogues[].speaker`に対応するperformerへ
向ける(組版〔後処理〕側で実装する設計であり、Packet自体に尾の向きを
指定するフィールドはない)。

## 6. 現在の完成状況(2026-07-23時点)

| キャラクター | 表情31 | turnaround4 | equipment |
|---|---|---|---|
| ハルト | ✅ | ✅ | — |
| ナツキ | ✅ | ✅ | ✅(2種) |
| アキラ | ✅ | ✅ | ✅(13種、flatten配置) |
| フユミ | ✅ | ✅ | — |
| 書記官 | ✅ | ✅ | ✅(書記局章1種) |

各キャラクターの詳細(固定仕様・Release情報)は
`reference_images/<id>/README.md`を参照。
