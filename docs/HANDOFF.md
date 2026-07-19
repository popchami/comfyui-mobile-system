# HANDOFF

## 最終更新
2026-07-19 / 更新者: Claude Code(チャミの直接承認によるハルト表情セットv2 ZIP取込作業、
chatgpt-workブランチ、commit d0293ba時点)

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
- [2026-07-13] flux1_dev_icon_24/32/48GB workflow新規作成(下記「進行中」参照。実装は
  完了、チャミの最終確認は未了のため引き続き進行中扱い)
- [2026-07-19] **異世界ニホンマンガ用ハルト表情セットv2の取込基盤**(commit cdc9295,
  d0293ba)。詳細:
  - 正本ZIP `haruto_expression_set_v2_clean.zip`(SHA-256: `76f8fdd2bd89060b9db5fb5f5f5dd740dd652d73c86944732367de3f1c423372`、
    61,727,275 bytes、PNG31枚・全1254×1254)をチャミが検証済みとして提供。
    実物のZIP内容(index.html + images/00-neutral.png〜30-speaking-forceful.png)を
    Termux側で再検証し、SHA-256・容量・枚数・サイズすべて一致を確認済み
  - **決定事項(チャミ)**: (1) Manga News Packetのreference_image(論理ID、例:
    `haruto/surprise-medium.png`)は維持し、実ファイル名(`05-surprise-medium.png`等の
    数字接頭辞つき)への解決はキャラクターごとのmanifest.jsonを介して行う方式を採用。
    LLM(news-game-translator側の脚本生成プロンプト)には数字接頭辞を生成させない。
    (2) PNG・ZIP本体はGit管理へcommitしない。正本はGitHub Release asset(タグ固定URL、
    `latest`は使わない)として保管する方針。リポジトリにはasset.json(取得元URL・
    SHA-256・容量・期待PNG枚数/画像サイズ・ZIP内部構成)・manifest.json・READMEのみ保持
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
  - Codexレビュー1回実施(commit cdc9295時点、agmsg経由)。Critical1件(旧
    shutil.rmtree→shutil.move方式が異なるファイルシステム間の移動失敗時に旧アセットを
    失いうる)・Minor1件(`_comment`キーの誤解決)を修正しd0293baでcommit済み、Blocker/
    Critical/Minorとも解消
  - 実データ(実際のZIP)でのエンドツーエンド動作確認済み(初回取得・force再取得とも、
    ダウンロード部分のみモックし31枚すべて正しく配置・解決されることを確認。取得結果は
    テスト後に削除、gitignore対象で正しい)

## 進行中・次にやること(担当者を明記)
- [2026-07-13・実装完了、チャミの最終確認待ち] flux1_dev_icon_24/32/48GB workflowを
  新規作成した(flux1_dev_icon_24GB_workflow_v2ollama.json / _32GB_ / _48GB_)。
  当初想定(weight_dtypeのみがtier差分)は不十分と判明していた点(下記参照)を
  踏まえ、以下の方針で実装:
  - FaceDetailer(顔検出・顔ディテール強化)は**含めない**。根拠: (1)normal/tierの
    実ファイルをdiffした結果、32GB/48GBにのみUltralyticsDetectorProvider+
    FaceDetailerが追加されていることを確認したが、(2)specs/icons/
    kickkick_icon_bundle_all_v1/ICON_SPEC_street.mdを確認したところ、icon生成対象は
    『Kick×Kick』アプリのUIナビゲーションアイコン14種(nav_home/nav_settings/
    icon_trophy等、ストリートテーマの抽象グリフ)であり顔を含まない、(3)さらに
    profiles/flux1_dev/icon/download_list_flux1.txt内で
    `# face_yolov8m ...`の行が既にコメントアウトされており(=未ダウンロード設定)、
    FaceDetailer非搭載が元々の設計意図と一致することを確認した。
    ただし現時点で確認できたのはstreetテーマ1件のみで、将来的に顔を含む
    キャラクター/マスコット系アイコンテーマが追加された場合は再検討が必要。
  - icon_24GB/32GBはicon_16GBと構造的に同一(UNETLoaderのtitleラベルのみ
    normal/tierの命名慣習に合わせて変更、weight_dtypeはfp8_e4m3fnのまま)。
  - icon_48GBはUNETLoaderのweight_dtypeを bf16 に変更(normal/48GBと同じ差分パターン)。
  - setup_flux1_dev.ipynbの24/32/48GB tierのtarget_workflow参照名も
    icon付きファイル名に修正済み(16GBと同様の対応)。
  - 生成後、全ファイルJSON妥当性を検証済み(python3 json.loadで26ノード確認)。
  - **新たに判明した別ギャップ(今回は対応せず記録のみ)**: icon_48GB tierが
    参照するbf16版モデル(flux1-dev.safetensors、非量子化)は、
    download_list_flux1.txtに未記載。ただしこれはnormal/download_list.txtにも
    同様の記載漏れがある既存の問題で、今回のicon作業で新規に生じたものではない。
    別途対応要否をチャミに確認。
- [訂正・2026-07-13] comfyui_icon_mobile.htmlのSVG追加は**実装済み**(commit 71da543、
  2026-07-08 22:07、このセッションより前)。前回のこの節の記述(「実装しない」)は誤り。
  誤りの原因: 今回の調査をdocs/mobile-system-specブランチ上のファイルで行ってしまい、
  chatgpt-work側で既に加わっていた変更を見落とした(ブランチを跨いだ調査ミス。以後は
  対象ブランチのHEADを確認してから記述する)。71da543の実装内容は、BRIA_RMBG→
  ConvertRasterToVector→SaveSVGの接続(image/svg_strings)のみを追加し、各ノードの
  ウィジェットパラメータ(BRIA_RMBGのバージョン値、ConvertRasterToVectorの
  color/spline等の閾値、SaveSVGのfilename_prefix等)はAPI入力キー名が/object_info
  未確認のため意図的に指定しておらず、ComfyUI側のノード既定値に委ねる設計(コメントで
  明記済み)。ノード名・接続順はworkflow JSON実体と一致、ハルシネーションではない。
  **残っている未検証事項**: (1)実際にComfyUI(RunPod等)で/promptに投げて実行が
  通るか未検証(ウィジェット省略時の既定値解決を含め、実機での動作確認なし)、
  (2)既定値のままで意図した見た目(閾値・解像度等)になるかは未確認。
- [Claude Code要実施・引き続きRunPod実機待ち] 上記の未検証事項(1)(2)を、RunPod実機で
  実際に生成を実行して確認する。合わせて/object_infoでBRIA_RMBG/ConvertRasterToVector/
  SaveSVGの正式なAPI入力キー名を確認し、意図した閾値等を明示指定できるようにする。
- ~~mainブランチへの直接pushをGit hookでブロックする安全装置を作る~~ → 完了済みへ移動
- [2026-07-19・チャミの承認待ち] **ハルト表情セットv2のGitHub Release作成**。
  提案タグ: `haruto-expression-set-v2`。アセット: `haruto_expression_set_v2_clean.zip`
  (61.7MB)。asset.jsonの`download_url`はこのタグの固定URLを既に指しているが、
  Release自体はまだ作成していない(外部への書き込みのため実行前に内容・Release名を
  チャミへ提示して承認を得ること、と申し送りされている)。Release作成後は
  `python3 scripts/fetch_reference_images.py --character haruto` で実際のダウンロード
  経路(SHA-256照合含む)を実機確認すること
- [2026-07-19] chatgpt-work → main のマージはまだ行っていない(commit d0293baまで
  chatgpt-workブランチ上)。マージ前にチャミの確認が必要(既存ルール通り)
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
- flux1_dev_icon_24/32/48GB workflow新規作成: FaceDetailerをiconワークフローにも
  含めるか要判断(上記「進行中」参照)
- comfyui_icon_mobile.htmlのSVGノード配線: 接続自体は実装済み(commit 71da543)。
  RunPod実機での実行検証と、/object_infoによるウィジェット入力キー名確認が未了
- ハルト表情セットv2のGitHub Release作成: チャミの承認待ち(上記「進行中」参照)

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
