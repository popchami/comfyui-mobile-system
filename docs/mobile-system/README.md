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

## 現在の状態

```text
PR #1: Draft
Branch: docs/mobile-system-spec
Merge: しない
Architecture alignment: 完了
Claude limited runtime validation: 完了
RunPod GPU validation: 未完了
Android real-device/emulator validation: 未完了
```

現在の最新状況は以下を見る。

```text
docs/mobile-system/HANDOFF.md
docs/mobile-system/RUNTIME_VALIDATION_RESULT.md
docs/mobile-system/BLOCKERS_AFTER_CLAUDE.md
docs/mobile-system/NEXT_PHASE_PLAN.md
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

## Claude検証結果

Claudeは以下を完了済み。

```text
1. 実装前の採用判断を確認
2. 現在のシステムを棚卸し
3. comfy-portal-endpoint の参考範囲を確認
4. ComfyUI / RunPod 公式機能との重複を確認
5. アーキテクチャ方針が妥当であることを確認
6. CPU-only aarch64 sandboxで限定ランタイム検証
7. OUTPUT_NODE blockerを発見・修正
```

限定検証で通ったもの:

```text
- ComfyUI starts with ComfyUI-Mobile-Analyzer installed
- Mobile Profile Exporter appears via /object_info
- Mobile Profile Exporter creates a zip after OUTPUT_NODE fix
- Zip contains workflow.json and app_profile.json
- /mobile_analyzer/profiles returns metadata
- /mobile_analyzer/profiles/{id}/download downloads zip
- Flutter MVP passes flutter pub get
- Flutter MVP passes flutter analyze for PR lib/ source
```

まだ通っていないもの:

```text
- RunPod GPU上での実モデル画像生成
- Android実機/エミュレータでのFlutterアプリ起動
- AndroidアプリからRunPod ComfyUIへ接続
- Androidアプリでprofile download / save / open / patch / submit / display
```

## 重要修正

```text
analyzer/ComfyUI-Mobile-Analyzer/nodes.py
- MobileProfileExporter に OUTPUT_NODE = True を追加
- 理由: これがないと ComfyUI が prompt_no_outputs で拒否する

analyzer/ComfyUI-Mobile-Analyzer/__init__.py
- 未使用の WEB_DIRECTORY = "web" を削除
- 理由: web/ フォルダが存在せず、web assetsも未提供のため
```

## 次フェーズ

RunPodが使えるようになったら以下へ進む。

```text
docs/mobile-system/NEXT_PHASE_PLAN.md
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

## 将来機能の事前準備

RunPod + Android検証前に実装はしないが、将来機能の目的・リスク・必要データ・受け入れ条件は以下に整理する。

```text
docs/mobile-system/FUTURE_FEATURE_PREP.md
```

さらに、あとで実装に移す時に迷わないように、以下も準備済み。

```text
docs/mobile-system/APP_PROFILE_EVOLUTION_PLAN.md
docs/mobile-system/UX_FLOW_PREP.md
docs/mobile-system/POST_VALIDATION_ISSUE_DRAFTS.md
docs/mobile-system/ADDITIONAL_FEATURE_CANDIDATES.md
```

役割:

```text
FUTURE_FEATURE_PREP.md
  = 将来機能の目的・リスク・受け入れ条件

APP_PROFILE_EVOLUTION_PLAN.md
  = app_profile.json の将来拡張案

UX_FLOW_PREP.md
  = Androidアプリの将来画面・エラー文言・UX方針

POST_VALIDATION_ISSUE_DRAFTS.md
  = RunPod + Android検証後にIssue化するための下書き

ADDITIONAL_FEATURE_CANDIDATES.md
  = 運用・管理・便利機能など追加候補の一覧
```

## 参考にすべき内容

外部/公式の参考情報は、機能候補とは別に以下へ整理する。

```text
docs/mobile-system/REFERENCE_STUDY_BACKLOG.md
```

参考元がどの機能に効くかは以下に整理する。

```text
docs/mobile-system/REFERENCE_TO_FEATURE_MAP.md
```

実際に調査する時のチェック項目は以下に整理する。

```text
docs/mobile-system/REFERENCE_STUDY_CHECKLIST.md
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
  FUTURE_FEATURE_PREP.md
  APP_PROFILE_EVOLUTION_PLAN.md
  UX_FLOW_PREP.md
  POST_VALIDATION_ISSUE_DRAFTS.md
  ADDITIONAL_FEATURE_CANDIDATES.md
  REFERENCE_STUDY_BACKLOG.md
  REFERENCE_TO_FEATURE_MAP.md
  REFERENCE_STUDY_CHECKLIST.md
  EXTERNAL_REFERENCES.md
  COMFY_PORTAL_ENDPOINT_REFERENCE_REVIEW.md
  RUNTIME_VALIDATION_RESULT.md
  BLOCKERS_AFTER_CLAUDE.md
  NEXT_PHASE_PLAN.md
```

## 未決定TODO / 改善記録

仕様検討が必要な項目は `OPEN_TODOS.md` に記録する。

今後の問題点、課題点、改善点は以下に記録する。

```text
docs/mobile-system/FUTURE_ISSUES_AND_IMPROVEMENTS.md
```

将来機能の仕様準備は以下に記録する。

```text
docs/mobile-system/FUTURE_FEATURE_PREP.md
docs/mobile-system/APP_PROFILE_EVOLUTION_PLAN.md
docs/mobile-system/UX_FLOW_PREP.md
docs/mobile-system/POST_VALIDATION_ISSUE_DRAFTS.md
docs/mobile-system/ADDITIONAL_FEATURE_CANDIDATES.md
```

参考にすべき外部/公式情報は以下に記録する。

```text
docs/mobile-system/REFERENCE_STUDY_BACKLOG.md
docs/mobile-system/REFERENCE_TO_FEATURE_MAP.md
docs/mobile-system/REFERENCE_STUDY_CHECKLIST.md
docs/mobile-system/EXTERNAL_REFERENCES.md
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
- PR #1はRunPod + Android検証が終わるまでマージしない
```
