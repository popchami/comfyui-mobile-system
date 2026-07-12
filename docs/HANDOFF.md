# HANDOFF

## 最終更新
2026-07-13 / 更新者: Claude Code(チャミの直接承認による夜間自律作業、「もう寝るから自由にすすめといて」2026-07-13)

## 完了済み
- SSH認証統一(comfyui-mobile-system / kickxkick)
- ZIP6個(88ファイル)のprofiles/フラット配置・push
- RunPod APIキー設定(.env, .gitignore保護)
- scripts/runpod_status_check.py 作成・動作確認
- profiles/flux1_dev/icon/ 配置(既存normal/pixelart/との差分はSHA256照合済み、別バージョンと確認)
- [2026-07-13] profiles/flux1_dev/icon/setup_flux1_dev.ipynb の16GB tier
  target_workflow参照名を flux1_dev_16GB_workflow_v2ollama.json から
  flux1_dev_icon_16GB_workflow_v2ollama.json に修正(該当行はファイル内で一意な文字列と
  確認した上でsed置換、grep再確認済み)。24/32/48GB tierの参照名は元々icon付きファイル名
  (flux1_dev_icon_24/32/48GB_workflow_v2ollama.json)を指しているが、そのファイル自体が
  まだ存在しない(下記「新規作成」項目が未着手のため)。
- [2026-07-13] mainブランチへの直接pushをブロックするpre-pushフックを追加
  (.git/hooks/pre-push、chatgpt-workなど他ブランチへのpushは許可)。
  ローカルでrefs/heads/mainへのpushをシミュレートしexit 1を確認、
  refs/heads/chatgpt-workではexit 0を確認済み。
  **注意**: gitフックは.gitディレクトリ内にありcloneで共有されないため、
  この安全装置は「このローカルクローンのみ」で有効。他の環境(RunPod上のclone等)
  で同様に保護したい場合は同じフックを別途設置する必要がある。

## 進行中・次にやること(担当者を明記)
- [ChatGPT分析済み・Claude Code実行待ち・2026-07-13時点で保留] flux1_dev_icon_24/32/48GB
  workflowの新規作成。当初想定(weight_dtypeのみがtier差分)は不十分と判明:
  normal/tierの実ファイルをdiffした結果、32GB/48GBには16/24GBに無い
  UltralyticsDetectorProvider + FaceDetailer(顔検出・顔ディテール強化)ノードが
  追加されている。iconワークフロー(アイコン生成用途)にも同じFaceDetailer追加を
  適用すべきかは対象が顔写真ではなくアイコン画像であるため自明ではなく、
  ハルシネーション禁止ルールにより憶測で実装しない。チャミの判断待ち。
- [ChatGPT分析済み・Claude Code実行待ち・2026-07-13時点で保留] comfyui_icon_mobile.html
  のAPI生成部分にBRIA_RMBG → ConvertRasterToVector → SaveSVG を追加する件。
  workflow JSON内でのノード存在は確認済み(BRIA_RMBG/ConvertRasterToVector/SaveSVG/
  ImageUpscaleWithModel/UpscaleModelLoaderいずれも実在、配線もImageUpscaleWithModel→
  BRIA_RMBG→ConvertRasterToVector→SaveSVGの順で確認)。ただしHTML側コード自身に
  既存コメントがあり(「PNG保存(正方形、背景透過・SVG化は/object_info確認後に追加予定)」
  L699付近)、ConvertRasterToVectorのworkflow.json上の値は位置指定のwidgets_values
  (['color','spline',4,8,80,2,15,45,5,True])のみでAPI入力名(キー名)が不明なため、
  下記の/object_info確認が完了するまで実装しない。
- [Claude Code要実施・引き続きRunPod実機待ち] 上記実装前提として、RunPod実機で
  /object_info を見てBRIA_RMBG/ConvertRasterToVector/SaveSVGのAPI入力名を確認
- ~~mainブランチへの直接pushをGit hookでブロックする安全装置を作る~~ → 完了済みへ移動

## ブロック中・保留
- ICON_SPEC_street.md(specs/icons/)のSHA256照合:kickkick_icon_bundle_all_v1.zip由来の
  同名ファイルと重複の可能性があるが、ZIP本体削除済みのため再照合には
  元ZIPの再アップロードが必要。緊急度低、ComfyUI動作確認が優先
- flux1_dev_icon_24/32/48GB workflow新規作成: FaceDetailerをiconワークフローにも
  含めるか要判断(上記「進行中」参照)
- comfyui_icon_mobile.htmlのSVGノード配線: /object_info確認(RunPod実機)待ち

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
