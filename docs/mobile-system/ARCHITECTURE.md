# Architecture

## 全体像

```text
Civitai / GitHub / ローカル workflow
  ↓
ComfyUI側でworkflowを指定
  ↓
Mobile Profile Export Workflowを実行
  ↓
ComfyUI-Mobile-Analyzerが解析
  ↓
mobile_profile_export.zipを出力
  ↓
スマホアプリがComfyUIからダウンロード
  ↓
スマホアプリ内で展開・検証・登録
  ↓
生成画面として使う
```

## 役割分担

### ComfyUI-Mobile-Analyzer

ComfyUI側で動く専用カスタムノード。

役割:

```text
- workflow.jsonを読み込む
- workflow形式を判定する
- API形式 / UI形式を判定する
- ノード一覧を解析する
- ノード接続を解析する
- ComfyUI側に存在するノードと照合する
- 不足ノードを確認する
- 不足モデルを確認する
- UI表示分類を決める
- ui_visibilityを付ける
- app_profile.jsonを生成する
- workflow.jsonとapp_profile.jsonをzip化する
- ComfyUI/output/mobile_profiles/へ保存する
- スマホアプリ向けAPIを提供する
```

### スマホアプリ

Analyzerが出力したprofileを読み込み、スマホ用UIを生成してComfyUIに送信する。

役割:

```text
- ComfyUI URL登録
- /system_statsで接続確認
- Analyzer確認
- profile一覧取得
- profile zipダウンロード
- zip展開
- app_profile.json検証
- workflow.json読み込み
- 動的UI生成
- ユーザー入力受付
- workflow patch
- /prompt送信
- WebSocket進捗表示
- /history取得
- /view画像表示
- 生成履歴保存
```

## app_profile.jsonの位置づけ

`app_profile.json` は Analyzer とスマホアプリの共通契約書とする。

Analyzerはこの形式に合わせて出力し、スマホアプリはこの形式に従ってUIを作る。

## profile zip

```text
mobile_profile_export.zip
  workflow.json
  app_profile.json
  source_info.json
  README.txt
```

任意:

```text
preview.png
thumbnail.png
analysis_debug.json
```

## 保存先

ComfyUI側:

```text
ComfyUI/output/mobile_profiles/
```

スマホアプリ側:

```text
app_data/
  profiles/
    profile_id/
      workflow.json
      app_profile.json
      preview.png
      source_info.json
```

## API

```text
GET /mobile_analyzer/profiles
GET /mobile_analyzer/profiles/{id}/download
```

## 基本方針

```text
- 専用ワークフローはシンプルにする
- 解析ロジックはカスタムノード側に寄せる
- スマホアプリはapp_profile.jsonを読み込んでUIを生成する
- スマホに手動でファイル移動しない
```
