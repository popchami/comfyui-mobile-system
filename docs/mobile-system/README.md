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
Smartphone-only implementation: 完了
Smartphone-only documentation: 完了
Cross-file static review fixes: 完了
Legacy HTML reuse notes: 完了
RunPod GPU validation: 未完了
Android real-device/emulator validation: 未完了
次の意味ある作業: RunPod + Android 実検証のみ
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
docs/mobile-system/LEGACY_HTML_REUSE_NOTES.md
```

## スマホ作業完了

スマホだけでできる準備・実装・文書整理は完了。

```text
docs/mobile-system/SMARTPHONE_ONLY_COMPLETION_REPORT.md
```

完了扱いの意味:

```text
- RunPod検証はまだ
- Android実機検証はまだ
- スマホ側の設計整理、手順書、引き継ぎ、将来準備は完了
- 横断静的レビューで見つけた小さい修正は完了
- 既存HTMLの実績コードから流用できる挙動は記録・反映済み
- Flutter MVPにスマホ側で準備できる主要機能は入れた
- 次の意味ある作業はRunPod/Androidの実検証
- 実検証前にスマホ側機能を増やさない
```

## スマホ側で実装済みの主な機能

```text
- ComfyUI URL保存・復元
- /system_stats 接続確認
- /object_info 能力確認
- /models/{folder} 読み取りhelper
- /queue helper + Check queue
- /interrupt helper + Interrupt
- friendly error handling
- profile warning display
- missing model / missing custom node warning
- Check environment
- ModelFolderResolver
- EnvironmentModelChecker
- profileごとの前回入力値保存・復元
- Reset to profile defaults
- Random seed
- Use last seed
- selected image preview
- /prompt + client_id
- /ws progress
- /history fallback
- /view image display
- session history
- generated image large preview
- generated image metadata
- collapsible generated UI sections
```

関連ドキュメント:

```text
docs/mobile-system/APP_INPUT_STATE_CONTROLS.md
docs/mobile-system/APP_QUEUE_AND_ERROR_CONTROLS.md
docs/mobile-system/APP_CAPABILITY_CHECKS.md
docs/mobile-system/APP_PROFILE_WARNING_DISPLAY.md
docs/mobile-system/APP_MODEL_FOLDER_RESOLVER.md
docs/mobile-system/APP_ENVIRONMENT_MODEL_CHECKER.md
docs/mobile-system/APP_GENERATED_IMAGE_METADATA.md
```

## 既存HTMLの扱い

既存の `profiles/` 配下HTMLは、動作確認済みの実績コードとして参照する。

```text
docs/mobile-system/LEGACY_HTML_REUSE_NOTES.md
```

扱い:

```text
- 挙動・接続フロー・fallbackロジックは参考にする
- 固定HTMLの構成そのものは最終アーキテクチャにしない
- プロンプト内容やモデル固定値は直接コピーしない
- 新方式は app_profile.json + patch_targets を中心にする
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

mobile-app/flutter_mvp/lib/screens/generate_screen.dart
- 既存HTMLの実績に合わせて、/history polling fallbackを強化

mobile-app/prototype/comfy-progress.js
- prototype側もWebSocket URL結合を修正

docs/mobile-system/PR_BODY_UPDATE_DRAFT.md
- Markdownの入れ子コードフェンス崩れを修正
```

詳細:

```text
docs/mobile-system/STATIC_REVIEW_NOTES.md
docs/mobile-system/LEGACY_HTML_REUSE_NOTES.md
```

## 次フェーズ

RunPodまたはAndroid検証ができる状態になったら以下へ進む。

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

## 参考にすべき内容

外部/公式の参考情報は、機能候補とは別に以下へ整理する。

```text
docs/mobile-system/REFERENCE_STUDY_BACKLOG.md
docs/mobile-system/REFERENCE_TO_FEATURE_MAP.md
docs/mobile-system/REFERENCE_STUDY_CHECKLIST.md
docs/mobile-system/EXTERNAL_REFERENCES.md
docs/mobile-system/COMFY_PORTAL_ENDPOINT_REFERENCE_REVIEW.md
```

## 検証・報告テンプレート

RunPod検証、Android検証、失敗報告、workflow互換性、重要判断の記録は以下を使う。

```text
docs/mobile-system/VALIDATION_RESULT_TEMPLATES.md
docs/mobile-system/DEBUG_REPORT_TEMPLATE.md
docs/mobile-system/WORKFLOW_COMPATIBILITY_REPORT_TEMPLATE.md
docs/mobile-system/DECISION_RECORD_TEMPLATE.md
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
- スマホだけの追加機能はここで止める
```
