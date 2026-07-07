# comfyui-mobile-system

Androidスマホ、Termux、Claude Code、RunPod、ComfyUI、GitHub、HTML UIを使って、画像生成環境をスマホだけで管理・自動化するためのリポジトリです。

## 目的

このリポジトリの目的は、ComfyUI環境を「ファイル一式」として整理し、将来的に以下を実現しやすくすることです。

- RunPodの起動・停止・状態確認
- ComfyUIのセットアップ・起動・更新
- Workflow / HTML UI / モデルリストの管理
- LoRAや追加モデルの管理
- 生成画像の保存先選択
- スマホだけでの運用
- Claude CodeなどAIへの引き継ぎ

## 基本方針

ユーザーはコードを書かない前提です。
そのため、構成は「初心者でも見て分かること」を優先します。

このリポジトリでは、ファイルを種類別ではなく、できるだけ「環境一式」単位で管理します。

例:

```text
profiles/flux1_dev/pixelart/24gb/
```

このフォルダを見れば、Flux.1 Dev PixelArt 24GB環境に必要なファイルが分かる状態を目指します。

## 主なフォルダ

```text
profiles/   実際にRunPod/ComfyUIで使う環境一式
specs/      アイコン仕様書、プロンプト仕様書など
scripts/    TermuxやRunPod操作用の自動化スクリプト
docs/       方針、設計、運用メモ
```

## 保存の考え方

生成画像はGitHubに保存しません。
通常画像はGoogle Drive保存も候補ですが、NSFW画像はプライバシーや同期リスクがあるため、ローカル保存を選べる設計にします。

## 最終目標

スマホから少ない操作で、以下の流れを実行できる状態を目指します。

```text
RunPod起動
↓
GPU状態確認
↓
ComfyUIセットアップ / 起動
↓
HTML UIまたはAPIから画像生成
↓
画像保存
↓
必要ならバックアップ
↓
RunPod停止
```
