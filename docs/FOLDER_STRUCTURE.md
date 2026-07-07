# フォルダ構成

## 基本方針

このリポジトリは、ファイルを「種類別」ではなく、できるだけ「環境一式」単位で管理します。

理由:

- スマホだけで見たときに分かりやすい
- Claude Codeへ「このフォルダを見て」と渡しやすい
- ZIPごとの内容と相性が良い
- RunPodへ持っていく単位が明確になる

---

## 全体構成

```text
comfyui-mobile-system/
├── README.md
├── docs/
├── profiles/
├── specs/
└── scripts/
```

---

## profiles/

実際にRunPod / ComfyUIで使う環境一式を置きます。

```text
profiles/
├── flux1_dev/
│   ├── normal/
│   ├── nsfw/
│   └── pixelart/
│       └── 24gb/
├── flux2_klein/
│   ├── normal/
│   ├── nsfw/
│   └── pixelart/
├── flux_full/
├── sdxl/
│   ├── chibi/
│   └── pixelart/
└── kick_icon/
```

### 置くファイル例

```text
setup.ipynb
backup.ipynb
download_list.txt
workflow.json
comfyui_mobile.html
download_ui.ipynb
download_extra.ipynb
README.md
```

---

## specs/

仕様書や設計資料を置きます。

```text
specs/
├── icons/
├── prompts/
├── workflows/
└── templates/
```

例:

```text
specs/icons/ICON_SPEC_street.md
```

---

## docs/

プロジェクト全体の説明、方針、ロードマップ、優先順位を置きます。

例:

```text
docs/AUTOMATION_ROADMAP.md
docs/TOP10_PRIORITY.md
docs/FOLDER_STRUCTURE.md
```

---

## scripts/

TermuxやRunPod操作の自動化スクリプトを置きます。

将来的な例:

```text
scripts/runpod_start.sh
scripts/runpod_stop.sh
scripts/setup_comfyui.sh
scripts/backup_profile.sh
scripts/sync_github.sh
```

---

## GitHubに置かないもの

- モデル本体
- LoRA本体
- 生成画像本体
- APIキー
- PAT
- パスワード
- 個人情報

---

## 画像保存の方針

通常画像:

- ローカル保存
- Google Drive保存
- 両方

NSFW画像:

- 原則ローカル保存
- Google Drive固定は避ける

---

## 今後の運用

新しい環境を追加するときは、まず `profiles/` に環境フォルダを作ります。

例:

```text
profiles/hidream/icon/24gb/
```

その中に必要ファイルをまとめます。
