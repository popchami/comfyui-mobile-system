# HANDOFF

## 最終更新
2026-07-22 / 更新者: Claude Code(PR #3・#4・#5をmainへsquash-merge、アキラ・フユミのGitHub Release作成・実URL検証完了)

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
  - **PR #2としてmainへsquash-merge済み**(2026-07-20、コミット`48867f3`)。
    3commitのみを`haruto-expression-set-v2-pr`ブランチへcherry-pickして
    スコープを限定、マージ前最終Codexレビューで指摘された`_atomic_replace`の
    バックアップ命名方式のCriticalも修正済み。マージ後ブランチ削除済み
- **ハルト4方向立ち絵・ナツキ正本の複数package/複数category対応拡張**。詳細:
  - 新規ZIP3件をチャミが検証済みとして提供(SHA-256・容量とも実機で再照合し
    完全一致確認済み): `haruto_turnaround_for_claude_code_v1.zip`(実運用対象、
    PNG4枚・各1024×1536)、`natsuki_complete_set_v2.zip`(実運用対象、
    31表情+4方向+装備2枚の計37枚、1ZIPに3カテゴリ収録)、
    `haruto_complete_archive_v1.zip`(保存・復旧専用の完全版、既存31表情+
    新turnaround4枚の意図的重複、CMS自動取得の対象外)
  - **決定事項(チャミ)**: 疑似キャラクターフォルダ方式は不採用。1キャラクター
    配下にcategory(expressions/turnaround/equipment、将来poses/training等)を
    持たせる。論理IDは既存表情`<character>/<tag>.png`の後方互換を維持しつつ、
    新category向けに`<character>/<category>/<tag>.png`形式を追加。
    実ファイル名の表記揺れ(`left-facing-profile`と`left-profile`等)は
    category別manifestが吸収し、論理IDは統一済みタグへ集約する
  - `asset.json`(旧形式・単一package・単一category)は後方互換のため無変更。
    新形式`packages.json`で1キャラクターが複数Release ZIP(package)を持て、
    1package(1ZIP)が複数categoryを収録できるよう拡張。categoryごとに
    独立したmanifest.json(1つの巨大manifestへ混在させない)
  - `scripts/reference_image_categories.py`(共有モジュール)で
    `KNOWN_CATEGORIES`・`CATEGORY_PLACE_TO`・`CATEGORY_MANIFEST_REL`を
    一本化し、fetch/resolve両スクリプトの定義drift(片方だけcategory追加漏れ)
    を防止
  - `scripts/fetch_reference_images.py`: 旧形式asset.jsonを内部で新形式へ
    正規化してから処理。package全categoryの検証完了後にのみ原子的に配置
    (1categoryでも検証失敗した場合、そのpackageからは何も配置しない)。
    既存の`_character_lock()`(flock)・`_atomic_replace()`は無変更で継続利用
  - `scripts/resolve_reference_image.py`: 論理ID正規表現にcategoryセグメントを
    任意(省略可)で追加、省略時は`expressions`扱い(既存互換)
  - **Codexレビュー2ラウンド実施・Critical/Minorすべて修正済み**:
    (1) `place_to`/`zip_subdir`/`manifest`等、config供給値を検証なしで
    パス結合していたCritical3件 → `_resolve_contained()`によるベース
    ディレクトリ封じ込めチェックを追加、かつ`place_to`/`manifest`は
    canonicalな対応表と完全一致必須へ変更(config側の自由記述を廃止)。
    (2) `expected_image_size: null`のcategoryでオブジェクト形式manifest
    (`file`/`width`/`height`)が未強制で、サイレントに寸法検証がスキップ
    されていたCritical1件(実際にナツキのequipment categoryで発生していたのを
    確認・修正) → 必須化。(3) `KNOWN_CATEGORIES`の2ファイル間重複(Minor)
    → 共有モジュールへ統合
  - `tests/test_fetch_reference_images.py`・`tests/test_resolve_reference_image.py`
    を大幅拡張、計88件全て合格(`python3 -m unittest discover -s tests`)。
    既存haruto表情31件の後方互換・複数package取得・1ZIP3category取得・
    ナツキ31表情タグの互換性・ファイル別寸法検証・装備2論理ID解決・
    旧形式asset.json互換・不正category/予約語/パストラバーサル拒否・
    検証失敗時の既存アセット保持・flock排他・完全版archiveの自動取得対象外化
    などを個別カバー
  - 実データ(実ZIP)での再検証済み: ハルトturnaround4枚・ナツキ37枚
    (31表情+4方向+装備2)、いずれも全論理ID解決成功、equipmentのファイル別
    寸法検証も実データで正しく動作確認済み
  - **GitHub Release3件作成済み・実URL検証完了**(2026-07-20):
    全てmainのコミット`48867f3107bc2a4743ec387f2eee541708e5dc4a`から作成、
    公開・非Draft・非Prerelease。
    - `haruto-turnaround-v1`(https://github.com/popchami/comfyui-mobile-system/releases/tag/haruto-turnaround-v1)、
      SHA-256: `88ebe6095a830d410c4ad041460441bbe5932a4f66e83460b8e671514074aa30`、5,680,279 bytes
    - `natsuki-complete-set-v2`(https://github.com/popchami/comfyui-mobile-system/releases/tag/natsuki-complete-set-v2)、
      SHA-256: `62be11c467c5ec59752a9413ea74268655e391becac7fa4cecb6da760a1c90cb`、67,106,972 bytes
    - `haruto-complete-archive-v1`(https://github.com/popchami/comfyui-mobile-system/releases/tag/haruto-complete-archive-v1、
      保存・復旧専用・CMS自動取得対象外)、
      SHA-256: `7f43840d46cbd6ba8512c1a6233a93aaa950e3100869c5b247c0b00616b2ecdf`、67,409,393 bytes
  - **PR #3としてmainへsquash-merge済み**(コミット`3463860`)。
    マージ後もブランチ`multi-character-reference-images`は削除せず維持
- **アキラ正本(表情/turnaround/equipment)の追加、equipmentのflatten機能実装**。詳細:
  - 正本ZIP `akira_complete_archive_v1.zip`(SHA-256:
    `1c34b24d830902ff3f63aa748956deed9da0d687e5177ef4ebda209200d8ffd7`、119,070,569 bytes)。
    保存用正本として再構成せずそのまま使用。登録対象は表情31・turnaround4・
    equipment13(hammer/talisman/nailの3種を論理上1つのequipmentカテゴリとして
    扱う)の計48枚。character/reference・crest・previews・README・ZIP独自
    manifest.json・SHA256SUMS.txtは保存用資料でありcategory定義には未登録
  - **新機能`flatten`**: category定義にオプションのbool `flatten`を追加。ZIP内部の
    ネストされたサブディレクトリ(`equipment/hammer/`等)を、配置時に
    `hammer-`/`talisman-`/`nail-`のプレフィックス付きで単一ディレクトリへ
    フラット化する。manifest entryに任意の`source_file`(ZIP内の実相対パス、
    ネスト可)を追加し、`file`(配置後ファイル名、`resolve_reference_image.py`が
    参照する既存フィールド)とは分離。`source_file`省略時は`file`と同一値に
    フォールバック(既存の非ネストcategoryとの完全後方互換)
  - 既存の「全category検証完了後にのみ配置」という原子性は、flatten対応後も
    維持(検証を`_verify_category`側、配置を`_place_category`側で分離)
  - **Codexレビュー実施・Minor2件を修正**: (1) category manifest内の重複する
    配置後ファイル名(`file`)を拒否する検出を追加(サイレント上書き防止)。
    (2) 配置後ファイル名のパストラバーサルチェックを、配置時だけでなく検証時
    にも追加(複数category構成での原子性保証の徹底)
  - `tests/test_fetch_reference_images.py`・`tests/test_resolve_reference_image.py`
    を拡張、**計110件全て合格**(既存88件+今回22件、うち1件はHaruto専用への
    スコープ限定に伴う既存テストのリネーム)
  - 実データ(実ZIP)での再検証済み: 48論理ID全解決、equipmentのflatten配置
    (hammer/talisman/nailの3サブフォルダ→単一ディレクトリへの正しいプレフィックス
    付与)も実データで動作確認済み
  - **GitHub Release作成済み・実URL検証完了**: タグ`akira-complete-archive-v1`
    (https://github.com/popchami/comfyui-mobile-system/releases/tag/akira-complete-archive-v1)、
    mainのコミット`62fee0e0dfe4e6c83583cacd84d01b40f9094e6f`から作成。
    SHA-256・容量一致、`unzip -t`正常、48論理ID全解決、既存Release4件は無変更
  - **PR #4としてmainへsquash-merge済み**(コミット`62fee0e`)。
    マージ後もブランチ`akira-reference-images`は削除せず維持
- **フユミ正本(表情/turnaround)の追加**。詳細:
  - 正本ZIP `fuyumi_complete_archive_v1.zip`(SHA-256:
    `7711b6efe5535564a3f6c13c39d957685ea3390fb75d2dd197d2ad1d151c9eca`、72,783,398 bytes)。
    表情31枚(`expression_set/images/`、1254×1254)+turnaround4枚
    (`turnaround/`、887×1774)の計35枚。equipmentは今回未収録
  - 取込前にZIP外の旧候補2件(`fuyumi_expression_set_v1.zip`=表情のみの旧版、
    `fuyumi-right-profile-orange-clear-blue.png`=制作途中候補画像)を検出し、
    チャミの指示により正本には統合せず不採用と確認。両ファイルはREADME.mdに
    明記のみでcategory定義には未登録
  - 既存の複数package/複数category方式(ハルト・ナツキ・アキラと同一パターン)を
    そのまま流用。新規category・独自構成の追加なし。
    `scripts/fetch_reference_images.py`・`scripts/resolve_reference_image.py`・
    `scripts/reference_image_categories.py`は無変更
  - 実データ(実ZIP)で35論理ID全解決を確認、テスト**110件全て合格**
    (既存の複数package/category機構をそのまま利用したため件数変化なし)
  - **GitHub Release作成済み・実URL検証完了**: タグ`fuyumi-complete-archive-v1`
    (https://github.com/popchami/comfyui-mobile-system/releases/tag/fuyumi-complete-archive-v1)、
    mainのコミット`d654ae412d4213fc1b7f57075da716c2b7cd9d91`から作成。
    公開URLからHTTP 200で取得・SHA-256一致・`unzip -t`正常・35論理ID全解決、
    既存Release4件は無変更
  - **PR #5としてmainへsquash-merge済み**(コミット`d654ae4`)。
    マージ後もブランチ`fuyumi-reference-images`は削除せず維持

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
- [Phase 2・将来] `profiles/sdxl/isekai_nihon_manga/` 配下にSDXL+IPAdapterのマンガ用
  ComfyUI Workflowを構築する(今回はデータ層・取得基盤のみ実装、Workflow本体は未着手)。
  実装時は`scripts/resolve_reference_image.py`をノード/前処理から呼び出す形で
  reference_image(論理ID)→実ファイルの解決を行う想定
- [将来] ハルト・ナツキ・アキラ・フユミは表情/turnaround(+アキラのみequipment)まで
  登録・Release作成・実URL検証済み。書記官の表情セット・書記官解説カットストックが
  用意され次第、同じ`packages.json`/category別manifest.jsonパターンで
  `reference_images/<character>/`を追加する(`scripts/fetch_reference_images.py`は
  複数キャラクター・複数package・複数category・flattenの自動検出に対応済み)
- [将来] フユミのequipment(装備)が用意され次第、既存equipmentカテゴリパターン
  (アキラのflatten機構含む)で追加を検討する

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
- キャラクター参照画像の正本ZIPはGit管理へ一切commitしない(取得後生成の
  images/等は.gitignore対象)。マージ・Release作成・ブランチ削除等の外部影響
  操作は、チャミの明示的な指示があるまで実行しない(ハルト・ナツキ・アキラ・
  フユミいずれもこの手順で運用、2026-07-19〜22)

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
