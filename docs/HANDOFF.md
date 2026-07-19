# HANDOFF

## 最終更新
2026-07-20 / 更新者: Claude Code(ハルト表情セットv2 ZIP取込作業、mainへのPR作成)

## 完了済み
- SSH認証統一(comfyui-mobile-system / kickxkick)
- ZIP6個(88ファイル)のprofiles/フラット配置・push
- RunPod APIキー設定(.env, .gitignore保護)
- scripts/runpod_status_check.py 作成・動作確認
- profiles/flux1_dev/icon/ 配置(既存normal/pixelart/との差分はSHA256照合済み、別バージョンと確認)
- **異世界ニホンマンガ用ハルト表情セットv2の取込基盤**。詳細:
  - 正本ZIP `haruto_expression_set_v2_clean.zip`(SHA-256: `76f8fdd2bd89060b9db5fb5f5f5dd740dd652d73c86944732367de3f1c423372`、
    61,727,275 bytes、PNG31枚・全1254×1254)をチャミが検証済みとして提供。
    実物のZIP内容(index.html + images/00-neutral.png〜30-speaking-forceful.png)を
    Termux側で再検証し、SHA-256・容量・枚数・サイズすべて一致を確認済み
  - **決定事項(チャミ)**: (1) Manga News Packetのreference_image(論理ID、例:
    `haruto/surprise-medium.png`)は維持し、実ファイル名(`05-surprise-medium.png`等の
    数字接頭辞つき)への解決はキャラクターごとのmanifest.jsonを介して行う方式を採用。
    LLM(news-game-translator側の脚本生成プロンプト)には数字接頭辞を生成させない。
    (2) PNG・ZIP本体はGit管理へcommitしない。正本はGitHub Release asset(タグ固定URL、
    `latest`は使わない)として保管する。リポジトリにはasset.json(取得元URL・SHA-256・
    容量・期待PNG枚数/画像サイズ・ZIP内部構成)・manifest.json・READMEのみ保持
  - `profiles/sdxl/isekai_nihon_manga/reference_images/haruto/` に asset.json・
    manifest.json(31種の表情タグ→実ファイル名対応)・README.md を配置(Git管理下)。
    `images/`・`index.html`は取得後にのみ生成され、Git管理外(.gitignore追加済み)
  - `scripts/fetch_reference_images.py`: ダウンロード→サイズ/SHA-256照合→zip slip対策
    つき展開(一時ディレクトリ、character_dirと同じファイルシステム上)→PNG枚数/画像
    サイズ検証→manifest突き合わせ→全合格時のみ`_atomic_replace()`(os.renameベースの
    退避→置換→退避削除、失敗時は退避から復元)で正式配置へ反映。`--force`なしでは
    既存アセットを一切変更しない。既存Flux系プロファイルには一切触れない
  - `scripts/resolve_reference_image.py`: Packetのreference_image(論理ID)から実
    ファイルへの絶対パスを解決する小さなユーティリティ。manifest.json内の予約キー
    (`_comment`等、"_"始まり)は表情タグとして解決できないよう明示的に拒否
  - `tests/test_fetch_reference_images.py`・`tests/test_resolve_reference_image.py`
    (このリポジトリで初のtests/ディレクトリ)。SHA-256/サイズ不一致時の非展開、
    zip slip拒否、`--force`なしでの非上書き、置換失敗時の原状復帰、予約キー拒否等、
    計36件全て合格(`python3 -m unittest discover -s tests`)
  - Codexレビュー1回実施(agmsg経由)。Critical1件(旧shutil.rmtree→shutil.move方式が
    異なるファイルシステム間の移動失敗時に旧アセットを失いうる)・Minor1件(`_comment`
    キーの誤解決)を修正、Blocker/Critical/Minorとも解消
  - **GitHub Release作成済み**: タグ `haruto-expression-set-v2`(通常Release、
    Draft/Pre-releaseではない)。
    https://github.com/popchami/comfyui-mobile-system/releases/tag/haruto-expression-set-v2
    実URL・実ネットワーク経由で、認証なし取得・SHA-256一致・PNG31枚1254×1254・
    manifest31表情すべて解決・既存アセット非上書き・`--force`再取得・テスト36件、
    いずれも実機確認済み(2026-07-19〜20)

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
  **注意**: 上記の一連のicon workflow関連作業は、実際にはchatgpt-workブランチ上で
  2026-07-13時点までに実装・commit済み(pre-pushフック追加含む)。ただし今回の
  ハルト表情セットv2 PRとは別スコープのため、mainへは別途chatgpt-workブランチ全体の
  マージ(またはそれらのcommit単位でのPR)で反映する想定。詳細はchatgpt-workブランチの
  git logおよびそちらのHANDOFF.mdを参照。
- [2026-07-20・PR作成済み、マージ待ち] ハルト表情セットv2の取込基盤を、
  chatgpt-workから独立したブランチ`haruto-expression-set-v2-pr`(cdc9295・d0293ba・
  883a879の3commitのみをmainへcherry-pick)としてPR化した。マージはチャミの確認後に行う
- [Phase 2・将来] `profiles/sdxl/isekai_nihon_manga/` 配下にSDXL+IPAdapterのマンガ用
  ComfyUI Workflowを構築する(今回はデータ層・取得基盤のみ実装、Workflow本体は未着手)。
  実装時は`scripts/resolve_reference_image.py`をノード/前処理から呼び出す形で
  reference_image(論理ID)→実ファイルの解決を行う想定
- [将来] ハルト以外のキャラクター(ナツキ・アキラ・フユミ・書記官)の表情セット・
  書記官解説カットストックが用意され次第、同じ`asset.json`/`manifest.json`パターンで
  `reference_images/<character>/`を追加する(`scripts/fetch_reference_images.py`は
  複数キャラクターの自動検出に対応済み)

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
- GitHub Release asset等、外部への書き込みを伴う操作は、実行前に内容(タグ名・
  アセット名・説明文)をチャミへ提示して承認を得ること(2026-07-19、ハルト表情
  セットv2の取込作業で確認)

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
