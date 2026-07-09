# ComfyUI Mobile System Docs

このフォルダは、ComfyUI Mobile System の新方針をまとめる専用ドキュメント置き場です。

## 目的

既存の固定HTML方式から、ComfyUI workflowを解析してスマホアプリ用UIに変換する方式へ移行する。

目標は、Civitai / GitHub / ローカルworkflowなどをComfyUI側で解析し、スマホアプリが `app_profile.json` と `workflow.json` を読み込んで、主要パラメータを編集・生成実行できる状態にすること。

## 基本方針

```text
ComfyUI-Mobile-Analyzer
  = ComfyUI側でworkflowを解析し、mobile_profile_export.zipを出力する

Smartphone App
  = zipをComfyUIから取得し、app_profile.jsonを読んでUI生成・workflow patch・生成実行を行う
```

## Claude最終確認

PCでの実行確認はClaudeに引き継ぐ。

Claudeに渡すコピペ文:

```text
docs/mobile-system/CLAUDE_COPYPASTE_PROMPT.md
```

Claudeは最初にこの順番で見る:

```text
docs/mobile-system/PRE_CLAUDE_STATUS.md
docs/mobile-system/PRIORITY_CONFLICT_REVIEW.md
docs/mobile-system/CLAUDE_FINAL_REVIEW_AND_INSTALL.md
docs/mobile-system/STATIC_REVIEW_NOTES.md
```

目的:

```text
- PR全体レビュー
- インストール前にやるべきこと/後回し/今やらないことの確認
- ComfyUI custom node install確認
- Flutter MVP install/run確認
- blocking error修正
- install-ready判定
```

## ドキュメント構成

```text
docs/mobile-system/
  README.md
  ARCHITECTURE.md
  APP_PROFILE_SCHEMA.md
  WORKFLOW_PATCH_RULES.md
  UI_VISIBILITY_RULES.md
  MVP_SCOPE.md
  ANALYZER_SPEC.md
  MOBILE_APP_SPEC.md
  HANDOFF.md
  PRE_CLAUDE_STATUS.md
  PRIORITY_CONFLICT_REVIEW.md
  CLAUDE_COPYPASTE_PROMPT.md
  CLAUDE_FINAL_REVIEW_AND_INSTALL.md
  STATIC_REVIEW_NOTES.md
  OPEN_TODOS.md
```

## 未決定TODO

仕様検討が必要な項目は `OPEN_TODOS.md` に記録する。

現在の主な未決定項目:

```text
- workflowノード色とアプリ側ノード色の同期
- 解析後workflowのアプリ側保存・読み込み
- 保存済みworkflowの再生成
- bypassノードの一時解除と復元
- subgraphの扱い
```

## 最重要ルール

```text
- workflowは壊さない
- ノードは消さない
- app_profile.jsonをAnalyzerとスマホアプリの共通契約書にする
- スマホアプリはpatch_targetsに書かれた項目だけ変更する
- hiddenノードもworkflowには保持する
- dangerousではなくneeds_attentionを使う
- スマホへ手動でファイル移動しない
- ComfyUI側からprofile zipを直接ダウンロードする
```
