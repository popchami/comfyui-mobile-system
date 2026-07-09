# ComfyUI Mobile System Docs

このフォルダは、ComfyUI Mobile System の新方針・検証結果・次作業・将来準備をまとめる専用ドキュメント置き場です。

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

## 現在の状態

```text
PR #1: Draft
Branch: docs/mobile-system-spec
Merge: しない
Architecture alignment: 完了
Claude limited runtime validation: 完了
Smartphone-only preparation: 完了
Cross-file static review fixes: 完了
RunPod GPU validation: 未完了
Android real-device/emulator validation: 未完了
```

最新状況は以下を見る。

```text
docs/mobile-system/HANDOFF.md
docs/mobile-system/SMARTPHONE_ONLY_COMPLETION_REPORT.md
docs/mobile-system/RUNTIME_VALIDATION_RESULT.md
docs/mobile-system/BLOCKERS_AFTER_CLAUDE.md
docs/mobile-system/NEXT_PHASE_PLAN.md
docs/mobile-system/NEXT_ACTION_QUEUE.md
docs/mobile-system/DOCS_AUDIT_RESULT.md
docs/mobile-system/STATIC_REVIEW_NOTES.md
```

## スマホ作業完了

スマホだけでできる準備は以下に完了報告として記録済み。

```text
docs/mobile-system/SMARTPHONE_ONLY_COMPLETION_REPORT.md
```

次の意味で完了扱いにする。

```text
- RunPod検証はまだ
- Android実機検証はまだ
- 文書整理、手順書、引き継ぎ、将来準備は完了
- 横断静的レビューで見つけた小さい修正は完了
- 次の意味ある作業はRunPod/Androidの実検証
```

## 重要修正済み

```text
analyzer/ComfyUI-Mobile-Analyzer/nodes.py
- MobileProfileExporter に OUTPUT_NODE = True を追加
- 理由: これがないと ComfyUI が prompt_no_outputs で拒否する

analyzer/ComfyUI-Mobile-Analyzer/__init__.py
- 未使用の WEB_DIRECTORY = "web" を削除
- 理由: web/ フォルダが存在せず、web assetsも未提供のため

mobile-app/flutter_mvp/lib/services/comfy_api_client.dart
- パス付きComfyUI URLを壊さないようにURL結合を修正

mobile-app/flutter_mvp/lib/services/comfy_progress_client.dart
- パス付きComfyUI URLを壊さないようにWebSocket URL結合を修正

mobile-app/prototype/comfy-progress.js
- prototype側もWebSocket URL結合を修正

docs/mobile-system/PR_BODY_UPDATE_DRAFT.md
- Markdownの入れ子コードフェンス崩れを修正
```

詳細:

```text
docs/mobile-system/STATIC_REVIEW_NOTES.md
```

## 次フェーズ

RunPodが使えるようになったら以下へ進む。

```text
docs/mobile-system/RUNPOD_VALIDATION_RUNBOOK.md
docs/mobile-system/ANDROID_VALIDATION_RUNBOOK.md
```

次フェーズ名:

```text
RunPod GPU + Android real-device validation
```

目的:

```text
RunPod ComfyUI
  ↓
ComfyUI-Mobile-Analyzer exports profile zip
  ↓
Android Flutter app downloads profile zip
  ↓
Android Flutter app opens profile
  ↓
Android Flutter app patches patch_targets only
  ↓
Android Flutter app submits workflow to ComfyUI
  ↓
ComfyUI generates an image with a real model
  ↓
Android Flutter app displays the result
```

## 最小引き継ぎ

毎回長い状況説明を貼らずにAIへ渡すための短いプロンプトは以下。

```text
docs/mobile-system/AI_MINIMAL_HANDOFF_PROMPTS.md
```

## PR本文更新案

PR本文を直接更新できない場合や、あとで手動更新する場合は以下を使う。

```text
docs/mobile-system/PR_BODY_UPDATE_DRAFT.md
```

## 将来機能の事前準備

実装はしないが、将来機能の目的・リスク・必要データ・受け入れ条件は以下に整理する。

```text
docs/mobile-system/FUTURE_FEATURE_PREP.md
docs/mobile-system/ADDITIONAL_FEATURE_CANDIDATES.md
docs/mobile-system/APP_PROFILE_EVOLUTION_PLAN.md
docs/mobile-system/UX_FLOW_PREP.md
docs/mobile-system/POST_VALIDATION_ISSUE_DRAFTS.md
```

役割:

```text
FUTURE_FEATURE_PREP.md
  = 将来機能の目的・リスク・受け入れ条件

ADDITIONAL_FEATURE_CANDIDATES.md
  = 運用・管理・便利機能など追加候補の一覧

APP_PROFILE_EVOLUTION_PLAN.md
  = app_profile.json の将来拡張案

UX_FLOW_PREP.md
  = Androidアプリの将来画面・エラー文言・UX方針

POST_VALIDATION_ISSUE_DRAFTS.md
  = RunPod + Android検証後にIssue化するための下書き
```

## 参考にすべき内容

外部/公式の参考情報は、機能候補とは別に以下へ整理する。

```text
docs/mobile-system/REFERENCE_STUDY_BACKLOG.md
docs/mobile-system/REFERENCE_TO_FEATURE_MAP.md
docs/mobile-system/REFERENCE_STUDY_CHECKLIST.md
docs/mobile-system/EXTERNAL_REFERENCES.md
docs/mobile-system/COMFY_PORTAL_ENDPOINT_REFERENCE_REVIEW.md
```

主な参考対象:

```text
- Official ComfyUI server/API behavior
- Official ComfyUI API workflow examples
- comfy-portal-endpoint
- RunPod Pods behavior
- RunPod Serverless
- ComfyUI Manager / custom node management patterns
- Civitai workflow/model sharing behavior
- GitHub workflow/profile storage patterns
- Android local storage and backup patterns
- Prompt/style preset patterns
```

## 検証・報告テンプレート

RunPod検証、Android検証、失敗報告、workflow互換性、重要判断の記録は以下を使う。

```text
docs/mobile-system/VALIDATION_RESULT_TEMPLATES.md
docs/mobile-system/DEBUG_REPORT_TEMPLATE.md
docs/mobile-system/WORKFLOW_COMPATIBILITY_REPORT_TEMPLATE.md
docs/mobile-system/DECISION_RECORD_TEMPLATE.md
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
  SMARTPHONE_ONLY_COMPLETION_REPORT.md
  NEXT_ACTION_QUEUE.md
  DOCS_AUDIT_RESULT.md
  PR_BODY_UPDATE_DRAFT.md
  RUNPOD_VALIDATION_RUNBOOK.md
  ANDROID_VALIDATION_RUNBOOK.md
  AI_MINIMAL_HANDOFF_PROMPTS.md
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
  FUTURE_FEATURE_PREP.md
  ADDITIONAL_FEATURE_CANDIDATES.md
  APP_PROFILE_EVOLUTION_PLAN.md
  UX_FLOW_PREP.md
  POST_VALIDATION_ISSUE_DRAFTS.md
  REFERENCE_STUDY_BACKLOG.md
  REFERENCE_TO_FEATURE_MAP.md
  REFERENCE_STUDY_CHECKLIST.md
  EXTERNAL_REFERENCES.md
  COMFY_PORTAL_ENDPOINT_REFERENCE_REVIEW.md
  VALIDATION_RESULT_TEMPLATES.md
  DEBUG_REPORT_TEMPLATE.md
  WORKFLOW_COMPATIBILITY_REPORT_TEMPLATE.md
  DECISION_RECORD_TEMPLATE.md
  RUNTIME_VALIDATION_RESULT.md
  BLOCKERS_AFTER_CLAUDE.md
  NEXT_PHASE_PLAN.md
  TEST_PLAN.md
  REVIEW_CHECKLIST.md
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
- PR #1はRunPod + Android検証が終わるまでマージしない
- 自動model downloadしない
- 自動custom node installしない
- Androidアプリをfull workflow editorにしない
```
