# ハルト表情セット(参照画像)

異世界ニホン4コマ/5コマ構成マンガ用のキャラクター参照画像。正本はGitHub
Releaseにアセットとして保管し、Gitツリーには含めない(詳細はリポジトリ
ルートのCLAUDE.md/AGENTS.mdおよびPhase運用ルール参照)。

## このディレクトリの構成

Git管理下(常に存在):

- `asset.json` — 正本ZIPの取得元・SHA-256・容量・期待するPNG枚数/画像
  サイズ・ZIP内部構成
- `manifest.json` — 表情タグ(`neutral`・`joy-weak`等、31種)から実ファイル名
  (`00-neutral.png`〜`30-speaking-forceful.png`)への対応表
- `README.md` — このファイル

取得後にのみ生成される(Git管理外、`.gitignore`対象):

- `images/` — 展開されたPNG31枚(1254×1254)
- `index.html` — ZIP同梱の人間向けプレビューギャラリー(日本語ラベル付き)。
  **画像取得前にこのファイルを開くとimg参照が壊れる**ため、`images/`が
  揃うまでは存在しない状態が正しい(壊れたプレビューを防ぐため、Git側には
  一切コミットしない)

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

| 項目 | 値 |
|---|---|
| ファイル名 | `haruto_expression_set_v2_clean.zip` |
| SHA-256 | `76f8fdd2bd89060b9db5fb5f5f5dd740dd652d73c86944732367de3f1c423372` |
| 容量 | 61,727,275 bytes(約61.7MB) |
| PNG枚数 | 31枚 |
| 画像サイズ | 全て1254×1254 |
| Release タグ | `haruto-expression-set-v2` |

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
