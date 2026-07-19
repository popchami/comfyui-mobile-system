# ハルト表情セット(参照画像)

異世界ニホン4コマ/5コマ構成マンガ用のキャラクター参照画像。正本はGitHub
Releaseにアセットとして保管し、Gitツリーには含めない(詳細はリポジトリ
ルートのCLAUDE.md/AGENTS.mdおよびPhase運用ルール参照)。

このディレクトリは複数のRelease ZIP(package)・複数の画像カテゴリ
(category)を持つ。カテゴリごとに`<category>/`配下へ配置し、`images/`
(カテゴリ省略時=`expressions`)のみ既存互換のためcharacter直下に置く。
詳細はリポジトリルートの`scripts/fetch_reference_images.py`docstring
参照。

## このディレクトリの構成

Git管理下(常に存在):

- `asset.json` — **表情(expressions)正本の取得情報(旧形式・後方互換)。
  内容は変更していない。** 正本ZIPの取得元・SHA-256・容量・期待する
  PNG枚数/画像サイズ・ZIP内部構成
- `manifest.json` — 表情タグ(`neutral`・`joy-weak`等、31種)から実ファイル名
  (`00-neutral.png`〜`30-speaking-forceful.png`)への対応表
- `packages.json` — **新規**。表情以外の追加package(現状: 4方向立ち絵)を
  列挙する
- `turnaround/manifest.json` — **新規**。4方向立ち絵の論理タグ
  (`front`/`left-profile`/`back`/`right-profile`)から実ファイル名への
  対応表
- `README.md` — このファイル

取得後にのみ生成される(Git管理外、`.gitignore`対象):

- `images/` — 展開されたPNG31枚(1254×1254、expressionsカテゴリ)
- `turnaround/images/` — **新規**。展開された4方向立ち絵PNG4枚
  (1024×1536)
- `index.html` — ZIP同梱の人間向けプレビューギャラリー(日本語ラベル付き、
  expressions正本ZIP由来)。**画像取得前にこのファイルを開くとimg参照が
  壊れる**ため、`images/`が揃うまでは存在しない状態が正しい(壊れた
  プレビューを防ぐため、Git側には一切コミットしない)

## 取得方法

RunPod上(または検証目的でTermux上)で以下を実行する。

```bash
python3 scripts/fetch_reference_images.py --character haruto
```

`asset.json`の`download_url`(GitHub Releaseの固定タグURL、`latest`は
使わない)からZIPを取得し、SHA-256・PNG枚数・全画像サイズを検証したうえで
`images/`・`index.html`を配置する。検証は一時ディレクトリで行い、失敗時は
既存の`images/`を一切変更しない。安全条件の詳細はスクリプト本体の
docstringを参照。

## 正本の情報

### expressions(表情、asset.json)

| 項目 | 値 |
|---|---|
| ファイル名 | `haruto_expression_set_v2_clean.zip` |
| SHA-256 | `76f8fdd2bd89060b9db5fb5f5f5dd740dd652d73c86944732367de3f1c423372` |
| 容量 | 61,727,275 bytes(約61.7MB) |
| PNG枚数 | 31枚 |
| 画像サイズ | 全て1254×1254 |
| Release タグ | `haruto-expression-set-v2` |

### turnaround(4方向立ち絵、packages.json)

| 項目 | 値 |
|---|---|
| ファイル名 | `haruto_turnaround_for_claude_code_v1.zip` |
| SHA-256 | `88ebe6095a830d410c4ad041460441bbe5932a4f66e83460b8e671514074aa30` |
| 容量 | 5,680,279 bytes(約5.5MB) |
| PNG枚数 | 4枚(正面/画面左向きの横顔/背面/画面右向きの横顔) |
| 画像サイズ | 全て1024×1536 |
| Release タグ | `haruto-turnaround-v1` |

固定事項(ZIP同梱README.md): 黄緑のジャケット、白い和装インナー、灰色の
袴風パンツ、茶色のブーツ、胸の桜チャーム、刀、背面の刀と若葉の紋。

### 保存・退避用完全版(自動取得対象外)

`haruto_complete_archive_v1.zip`(SHA-256:
`7f43840d46cbd6ba8512c1a6233a93aaa950e3100869c5b247c0b00616b2ecdf`)は、
上記expressions正本31枚とturnaround正本4枚を1つにまとめた**保存・退避用**
の完全版ZIP。GitHub Releaseタグ`haruto-complete-archive-v1`として保管
するが、`asset.json`・`packages.json`のいずれからも参照せず、
`scripts/fetch_reference_images.py`による自動取得・
`scripts/resolve_reference_image.py`による論理ID解決の対象にはしない
(内容はexpressions/turnaroundと重複しているため)。

## 表情タグの対応(manifest.json)

news-game-translatorリポジトリの`scripts/manga_schema.py::ALLOWED_EXPRESSION_TAGS`
と同一の31種の表情タグを使う。Manga News Packetの`reference_image`フィールド
(例: `haruto/surprise-medium.png`)は実ファイルへの直接パスではなく論理ID
であり、`manifest.json`を介して実ファイル(`05-surprise-medium.png`)へ
解決する。解決ロジックは`scripts/resolve_reference_image.py`参照。

- `00-neutral.png`(強度指定なし)
- `01`〜`27`: 9感情(joy/surprise/confusion/worry/anger/sadness/
  embarrassment/determination/tears) × weak/medium/strong
- `28`〜`30`: `speaking-small`/`speaking-normal`/`speaking-forceful`
  (speakingのみ専用の強度語。weak/medium/strongは使わない)

## turnaroundタグの対応(turnaround/manifest.json)

論理ID形式は`<character>/turnaround/<tag>.png`(categoryを明示する3
セグメント形式)。標準タグは`front`/`left-profile`/`back`/
`right-profile`の4種で、全キャラクター共通。実ファイル名の表記揺れ
(例: ハルトの実ファイルは`01-left-facing-profile.png`)は
`turnaround/manifest.json`で吸収する。

例: `haruto/turnaround/front.png` → `turnaround/images/00-front.png`
