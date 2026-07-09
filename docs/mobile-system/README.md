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

## 方向性ガードレール

外部リポジトリを参考にしても、このプロジェクトの方向性は変えない。

```text
docs/mobile-system/PROJECT_DIRECTION_GUARDRAILS.md
```

## 実装前の採用判断

棚卸し結果をそのままClaudeに渡すのではなく、実装前の判断として整理済み。

```text
docs/mobile-system/PRE_IMPLEMENTATION_ALIGNMENT_DECISIONS.md
```

現在の判断:

```text
- 現在のシステムは捨てない
- ただし実装方針は調整する
- ComfyUI公式APIを優先して使う
- Analyzerは公式APIの情報をスマホ用profileへ翻訳する役割に寄せる
- /object_info と /models は優先度を上げる
- UI workflow変換はMVP後のoptional扱い
- comfy-portal-endpointは参考のみ
```

## Claude最終確認

PCでの実行確認はClaudeに引き継ぐ。

ただし、Claudeに渡す内容は更新済み。

現在は単なる runtime validation ではなく、先に以下を行う。

```text
1. 実装前の採用判断を確認
2. 現在のシステムを棚卸し
3. comfy-portal-endpoint の参考範囲を確認
4. ComfyUI / RunPod 公式機能との重複を確認
5. 必要なら実装前に設計を調整
6. その後に runtime validation
```

渡す前の作業完了メモ:

```text
docs/mobile-system/PRE_CLAUDE_DONE.md
```

Claudeに渡すコピペ文:

```text
docs/mobile-system/CLAUDE_COPYPASTE_PROMPT.md
```

Claudeは最初にこの順番で見る:

```text
docs/mobile-system/PRE_CLAUDE_STATUS.md
docs/mobile-system/PROJECT_DIRECTION_GUARDRAILS.md
docs/mobile-system/PRE_IMPLEMENTATION_ALIGNMENT_DECISIONS.md
docs/mobile-system/SYSTEM_INVENTORY_BEFORE_CLAUDE.md
docs/mobile-system/EXISTING_PLATFORMS_REVIEW.md
docs/mobile-system/COMFY_PORTAL_ENDPOINT_REFERENCE_REVIEW.md
docs/mobile-system/PRIORITY_CONFLICT_REVIEW.md
docs/mobile-system/CLAUDE_FINAL_REVIEW_AND_INSTALL.md
docs/mobile-system/STATIC_REVIEW_NOTES.md
```

目的:

```text
- PR全体レビュー
- 実装前の採用判断の確認
- 公式ComfyUI APIと重複する自作部分の確認
- /object_info と /models を早めるべきか確認
- comfy-portal-endpoint を参考にする範囲の確認
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
  PROJECT_DIRECTION_GUARDRAILS.md
  PRE_IMPLEMENTATION_ALIGNMENT_DECISIONS.md
  SYSTEM_INVENTORY_BEFORE_CLAUDE.md
  EXISTING_PLATFORMS_REVIEW.md
  PRE_CLAUDE_DONE.md
  PRE_CLAUDE_STATUS.md
  PRIORITY_CONFLICT_REVIEW.md
  CLAUDE_COPYPASTE_PROMPT.md
  CLAUDE_FINAL_REVIEW_AND_INSTALL.md
  STATIC_REVIEW_NOTES.md
  OPEN_TODOS.md
  FUTURE_ISSUES_AND_IMPROVEMENTS.md
  EXTERNAL_REFERENCES.md
  COMFY_PORTAL_ENDPOINT_REFERENCE_REVIEW.md
```

## 未決定TODO / 改善記録

仕様検討が必要な項目は `OPEN_TODOS.md` に記録する。

今後の問題点、課題点、改善点は以下に記録する。

```text
docs/mobile-system/FUTURE_ISSUES_AND_IMPROVEMENTS.md
```

外部プロジェクトを参考にする場合の方針は以下に記録する。

```text
docs/mobile-system/EXTERNAL_REFERENCES.md
```

`comfy-portal-endpoint` の実用度レビューは以下に記録する。

```text
docs/mobile-system/COMFY_PORTAL_ENDPOINT_REFERENCE_REVIEW.md
```

現在のシステム、外部参考、公式参考の棚卸しは以下に記録する。

```text
docs/mobile-system/SYSTEM_INVENTORY_BEFORE_CLAUDE.md
docs/mobile-system/EXISTING_PLATFORMS_REVIEW.md
```

現在の主な未決定項目:

```text
- workflowノード色とアプリ側ノード色の同期
- 解析後workflowのアプリ側保存・読み込み
- 保存済みworkflowの再生成
- bypassノードの一時解除と復元
- subgraphの扱い
- /object_info を使ったfield detection改善
- /models を使ったmodel existence check
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
- 公式ComfyUI APIで解決できる部分は優先して使う
- 外部リポジトリを参考にしても方向性は変えない
```
