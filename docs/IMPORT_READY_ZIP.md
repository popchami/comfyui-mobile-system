# 整理済みZIPの取り込み手順

このドキュメントは、アップロード済みZIP群を整理した `comfyui_mobile_system_ready.zip` をGitHubへ取り込むための手順です。

## 目的

ZIP内の実ファイルを、決定済みのフォルダ構成へ安全に配置します。

## 整理済みZIPの内容

```text
comfyui-mobile-system-files/
├── profiles/
│   ├── flux1_dev/
│   ├── flux2_klein/
│   ├── flux_full/
│   └── sdxl/
├── specs/
│   └── icons/
└── docs/
    └── FILE_MANIFEST.json
```

## 取り込み手順

GitHubリポジトリのルートで実行します。

```bash
unzip comfyui_mobile_system_ready.zip
cp -R comfyui-mobile-system-files/* .
git status
git add .
git commit -m "Import ComfyUI profile files"
git push
```

## 重要

既存ファイルがある場合は、すぐにcommitせず、先に確認します。

```bash
git status
git diff --stat
```

## 完了後に確認すること

```bash
find profiles -type f | sort
find specs -type f | sort
```

## 含まれるファイル数

整理済みZIPには、実ファイル93個が含まれます。

## ハッシュ確認

`docs/FILE_MANIFEST.json` に各ファイルのSHA-256を記録しています。

## 注意

- モデル本体は含めていません
- LoRA本体は含めていません
- 生成画像は含めていません
- APIキー、PAT、パスワードは含めていません
