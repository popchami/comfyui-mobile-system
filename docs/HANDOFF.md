# HANDOFF

## 最終更新
2026-07-08 / 更新者: Claude Code

## 完了済み
- SSH認証統一(comfyui-mobile-system / kickxkick)
- ZIP6個(88ファイル)のprofiles/フラット配置・push
- RunPod APIキー設定(.env, .gitignore保護)
- scripts/runpod_status_check.py 作成・動作確認
- profiles/flux1_dev/icon/ 配置(既存normal/pixelart/との差分はSHA256照合済み、別バージョンと確認)

## 進行中・次にやること(担当者を明記)
- [ChatGPT分析済み・Claude Code実行待ち] flux1_dev_icon_24/32/48GB workflowの新規作成
  (normal/のTIER差分:weight_dtypeがflux1-dev-fp8.safetensors[16/24/32GB]→
  flux1-dev.safetensors[48GBのみ]、workflow内weight_dtypeはfp8_e4m3fn[16/24/32GB]→
  bf16[48GBのみ]という差分パターンを踏まえて作成する)
- [ChatGPT分析済み・Claude Code実行待ち] profiles/flux1_dev/icon/setup_flux1_dev.ipynb の
  target_workflow参照名を flux1_dev_16GB_workflow_v2ollama.json から
  flux1_dev_icon_16GB_workflow_v2ollama.json に修正
- [ChatGPT分析済み・Claude Code実行待ち] comfyui_icon_mobile.html のAPI生成部分に
  BRIA_RMBG → ConvertRasterToVector → SaveSVG を追加(workflow JSON内には実在確認済み、
  HTML側で未接続なことが判明。ImageUpscaleWithModelというノード名も提案されたが
  実在未確認、実装前にworkflow内で確認が必要)
- [Claude Code要実施] 上記実装後、RunPod実機で /object_info を見て
  SVG系3ノードのAPI入力名を確認
- [Claude Code要実施] mainブランチへの直接pushをGit hookでブロックする
  安全装置を作る(pre-push hook等)。ChatGPTがブランチを自動認識できない
  ため、人間の確認だけに頼らず機械的に事故を防ぐ目的。
  chatgpt-workブランチへのpushは許可、mainへの直接pushのみ拒否する設定。

## ブロック中・保留
- ICON_SPEC_street.md(specs/icons/)のSHA256照合:kickkick_icon_bundle_all_v1.zip由来の
  同名ファイルと重複の可能性があるが、ZIP本体削除済みのため再照合には
  元ZIPの再アップロードが必要。緊急度低、ComfyUI動作確認が優先

## 重要な注意事項(繰り返し確認が必要なルール)
- ChatGPTは分析・提案のみ。編集・commit・push は一切行わない
  (GitHubコネクタで読み取りは可能だが、書き込みはさせない)
  ※理由:ChatGPT側のGitHubコネクタはchatgpt-workのような
  非デフォルトブランチを検索・認識できない制約があることが
  2026-07-08に判明したため、実行役には向かない
- 実際のファイル編集・commit・push は全てClaude Code側で、
  chatgpt-workブランチ上で行う(mainには直接触れない)
- chatgpt-work → main のマージは、必ずClaude側が内容を
  確認してから行う(自動マージ禁止)
- ファイル名が同じでも中身が違う可能性があるため、
  同一判定にはSHA256ハッシュ比較を使う
- ノードの有無はworkflow JSON内を実際に確認してから判断する
  (ハルシネーション禁止)
- NSFW/通常は物理フォルダで分けず、1workflow内でwildcard切り替え
- 同じリポジトリに対し、Claude Code経由の作業と、ユーザーが
  ChatGPTの指示を直接実行する作業が並走すると、push衝突・
  方針の逆行が発生するリスクがある(2026-07-08に実際に発生)。
  ChatGPTから「このコマンドを実行してください」と言われても、
  ユーザーは直接実行せず、必ずClaude(claude.aiまたはClaude Code)
  経由で確認すること

## ChatGPTとの作業フロー(最終確定版・2026-07-08)
1. あなたがChatGPTに分析を依頼する
   (GitHubコネクタでmainブランチの内容を読ませてよい)
2. ChatGPTは提案(テキストの差分案)のみを返す。
   実行はしない
3. あなたがその提案をこのチャット(claude.ai)またはTermuxの
   Claude Codeに渡す
4. Claude Codeが chatgpt-work ブランチで実際に編集・commit・push
5. Claude(claude.aiチャット)が chatgpt-work の内容を確認し、
   問題なければ main にマージする
