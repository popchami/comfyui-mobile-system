# HANDOFF

## 最終更新
2026-07-24 / 更新者: Claude Code(「画像アップロード準備」と「実ピクセル変換」〔PR #11〕をmainへsquash-merge済み〔squash commit `4eceb7ae9616c87db5b600983ed6fd2397824469`〕。続けて次工程として、ハルト・panel_no=1・生成1枚に固定した単発実行経路(`scripts/comfyui_run_once.py`)をブランチ`one-panel-runtime-wire-v1`で実装完了。既定は常にdry-run、`execute=True`を明示した場合のみ実通信する設計。**commit前の最終Codexレビュー(Review A・Review Bとも各2ラウンドで完了)を実施し、Blocker 0件・Critical 4件・Major 19件・Minor 12件(actionableな指摘35件)をすべて個別に再現・最小修正済み、残件0件**(詳細は完了済みセクション参照)。修正後377件全合格、`git diff --check`もexit 0。今回もすべて`session`をmockして検証しており、RunPod・ComfyUIへの実通信・GPU生成は一度も行っていない。対象7ファイルをcommit(`a5d582d68e16f944821225b72e094925b9609edb`)・push済みで、main向けDraft PR #12
(https://github.com/popchami/comfyui-mobile-system/pull/12)を作成済み(state=OPEN, isDraft=true)。次は、Draft PRのレビュー・承認判断、その後の実RunPod接続検証待ち。**最新の状態はGitHub PR #12とgit履歴を正とする**)

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
    既存Release5件(haruto-expression-set-v2・haruto-turnaround-v1・
    natsuki-complete-set-v2・haruto-complete-archive-v1・
    akira-complete-archive-v1)は無変更
  - **PR #5としてmainへsquash-merge済み**(コミット`d654ae4`)。
    マージ後もブランチ`fuyumi-reference-images`は削除せず維持
- **書記官正本(表情/turnaround/equipment)の追加**。詳細:
  - 正本ZIP `scribe_complete_archive_v1.zip`(SHA-256:
    `e1674d69d81f6a72edf2156e7cf6e6d8854ac2ada19b5d4420564df9433ec476`、70,937,890 bytes)。
    表情31枚(`expression_set/images/`、1254×1254)+turnaround4枚
    (`turnaround/images/`、887×1774)+書記局章1枚(`emblem/`、1254×1254)の計36枚
  - 書記局章は新規`emblem` categoryを作らず、**既存の`equipment` category**として
    論理タグ`official-scribe-bureau-emblem`で登録(単一ファイルが`emblem/`直下に
    あり、ネスト構造がないためアキラのflatten機構は不要)
  - 固定仕様(README.md記載): 濃い中間紫のロングアウター(金縁・地紋)、赤いボブ
    +編み込み、丸眼鏡、鳩のかんざし、左手にタブレット・右手にペン。書記局章は
    円形枠+中央の筆+左右対称の巻物で構成し、腕章・タブレット・背面上部に同一の
    書記局章を使用
  - 初回転送分`scribe_complete_archive_v1.zip`・再転送分`scribe_complete_archive_v1-1.zip`
    (いずれもSHA-256`a38de4da...`で同一内容)は、EOCD(セントラルディレクトリ終端)
    レコード欠落により不正なZIPと判明(転送/保存段階での破損、ストレージ容量は
    問題なし)。新ファイル名で再構築された`scribe_complete_archive_v1_rebuilt.zip`
    (SHA-256`e1674d69...`)のみを正本として採用、旧2ファイルは不採用として
    README.mdに明記
  - 既存の複数package/複数category方式(ハルト・ナツキ・アキラ・フユミと同一
    パターン)をそのまま流用。新規category・独自構成の追加なし。
    `scripts/fetch_reference_images.py`・`scripts/resolve_reference_image.py`・
    `scripts/reference_image_categories.py`は無変更
  - 実データ(実ZIP)で36論理ID全解決を確認、テスト**110件全て合格**
    (既存の複数package/category機構をそのまま利用したため件数変化なし)
  - **GitHub Release作成済み・実URL検証完了**: タグ`scribe-complete-archive-v1`
    (https://github.com/popchami/comfyui-mobile-system/releases/tag/scribe-complete-archive-v1)、
    mainのコミット`407dda1da1b758c54b5a7329e99f875e96009e71`から作成。アップロード元は
    `_rebuilt.zip`を新規一時ディレクトリへコピー・改名した実体を、改名後に容量・
    SHA-256・`unzip -t`を再確認してから使用(破損した旧ファイルは未使用)。
    公開URLからHTTP 200で取得・容量/SHA-256一致・`unzip -t`正常・36論理ID全解決、
    既存Release6件(haruto-expression-set-v2・haruto-turnaround-v1・
    natsuki-complete-set-v2・haruto-complete-archive-v1・akira-complete-archive-v1・
    fuyumi-complete-archive-v1)は無変更(書記官分を加え合計7件)
  - **PR #7としてmainへsquash-merge済み**(コミット`407dda1`)。
    マージ後もブランチ`scribe-reference-images`は削除せず維持
- **5コマ正本テンプレート仕様の確定、Manga News Packet v2への対応
  (news-game-translator側との連携)**。詳細:
  - チャミが提示した5コマテンプレート仕様(完成画像1080×1920px、白背景、
    黒枠6px、コマ間隔19px、5コマの外枠・内側・安全領域座標)を、
    `profiles/sdxl/isekai_nihon_manga/five_panel_template.json`
    (数値の正本)として新規追加。実在するテンプレートPNG
    (`/sdcard/Download/manga_panel_template_v3.png`、1080×1920)を
    Pillow(この検証専用に一時venvへインストール、リポジトリへの依存追加
    ではない)で実測し、全5コマの座標・枠線6px・コマ間隔19pxが指定仕様と
    完全一致することを確認済み。PNG自体はGit管理へ追加していない
    (数値正本はJSON側のため)
  - `scripts/generate_five_panel_template_doc.py`(新規): JSONから人間向け
    Markdown(`five_panel_template.md`)を生成する。Markdownは手書きせず
    必ずこのスクリプトで生成し、`--check`モードでJSON⇔Markdownの数値
    不一致をドリフト検出できるようにした(チャミの指示「数値の正本はJSON、
    Markdownとの不一致を検出するテストを追加するか生成構造にする」に対応)
  - `profiles/sdxl/isekai_nihon_manga/MANGA_PACKET_CONNECTION.md`(新規):
    news-game-translator側Manga News Packet v2との接続契約書。Packetの
    日本語表示名(ハルト等)→このリポジトリのローマ字フォルダ名
    (`haruto`等)の対応表、`reference_image`論理ID形式、5人全員の
    完成状況一覧を記載
  - `tests/test_five_panel_template.py`(新規、15件): 完成画像サイズ・
    枠線・コマ間隔・5コマ全ての外枠/内側/安全領域座標・安全領域が内側へ
    完全に収まること・各コマがキャンバス外へ出ないこと・
    `five_panel_template.md`が`five_panel_template.json`からの生成結果と
    一致すること(ドリフト検出)を検証
  - 既存の`scripts/fetch_reference_images.py`・
    `scripts/resolve_reference_image.py`・
    `scripts/reference_image_categories.py`・既存キャラクターのmanifest・
    既存Flux系プロファイルは無変更。既存110件+新規15件、
    **計125件全て合格**(`python3 -m unittest discover -s tests`)
  - news-game-translator側では、Manga News PacketをPACKET_VERSION 1→2へ
    全面移行(実運用中のv1データなしを確認の上、後方互換コードなしで
    一括移行)。1コマ1人固定を`performers`(最大2人)・`dialogues`
    (最大2個)へ拡張、`role`をsetup/development/turn/resolutionの固定
    4値化、第1〜4コマの登場人物を「ハルト・ナツキ専任」から「ハルト・
    ナツキ・アキラ・フユミの4人から2〜3人選択」へ拡張、第5コマに
    `scribe_panel`(書記官の正本画像を初めて参照)を新設。詳細は
    news-game-translator側`docs/HANDOFF.md`参照
  - manga/characters.mdの装備欄(ナツキ・アキラ・フユミ・書記官)が、
    実際にこのリポジトリで完成させた正本画像と食い違っていたことが
    今回判明し、news-game-translator側で修正済み(このリポジトリ側の
    READMEの記載が常に実体の正本であることを再確認)
  - **分割Codexレビュー完了**(2026-07-24): C(comfyui-mobile-system側
    テンプレート仕様・接続契約文書)・D(news-game-translatorとの接続契約
    18項目)を実施。Blocker/Critical/Major/Minor**残件0**まで指摘を
    修正済み(HANDOFF.mdの最終更新日ずれ等の軽微な指摘含め、発見した指摘は
    全て妥当と確認の上で採用)
  - **実装ブランチ**: `five-panel-template-v2`(mainから分岐)
  - **実装commit**: `e0791f1b50760a5e5f31abad0e4fab1f5b1490d8`
  - **PR**: #9(https://github.com/popchami/comfyui-mobile-system/pull/9)
  - **最新のマージ状態はGitHub PR #9とgit履歴を正とする**(このファイルの
    記載は実装時点のスナップショットであり、マージ・Release状況を都度
    上書きする運用はしない)
- **「ハルト1人・1コマ生成試験」の事前実装(dry-runのみ、RunPod未起動・
  課金なし)**。詳細は
  `profiles/sdxl/isekai_nihon_manga/ONE_PANEL_PILOT.md`参照
  - **実装ブランチ**: `one-panel-pilot-v1`(mainから分岐)
  - Manga News Packet v2の第1コマ(panel_no=1、登場人物をハルト1人に
    限定した試験fixture)を入力に、正本画像取得→ComfyUI(SDXL+IPAdapter)
    向けAPI形式Workflow構築→RunPodへ送る予定のリクエストJSON構築までを
    dry-runで検証できる状態にした(`scripts/one_panel_pilot.py`)。
    RunPod API送信・GPU画像生成・モデルダウンロードは一切行っていない
  - Packet v2構造検証・enum・`CHARACTER_REFERENCE_ID`はnews-game-translator側
    `scripts/manga_schema.py`を正本としてそのままimportして再利用、
    reference_image解決はこのリポジトリの既存
    `scripts/resolve_reference_image.py`をそのまま再利用(重複実装なし)
  - ComfyUI Workflowのノード名・既定パラメータは、既存
    `profiles/sdxl/chibi/comfyui_sdxl_chibi.html`が実際に使用している
    構成(CheckpointLoaderSimple→CLIPTextEncode×2→CLIPVisionLoader+
    LoadImage→IPAdapterUnifiedLoader→IPAdapterAdvanced→
    EmptyLatentImage→KSampler→VAEDecode→SaveImage)を踏襲。モデル名・
    IPAdapterプリセットはコードへ決め打ちせず
    `profiles/sdxl/isekai_nihon_manga/one_panel_pilot/config.example.json`
    経由で差し替え可能にした
  - 必須Custom Node`ComfyUI_IPAdapter_plus`
    (`https://github.com/cubiq/ComfyUI_IPAdapter_plus`、既存
    `profiles/sdxl/chibi/setup_sdxl.ipynb`で実際にclone対象になっている
    ことを確認済み)を文書化。バージョン固定は現時点で未実施であることも
    明記(推測でcommit hashを記載していない)
  - Negative promptは既存`profiles/sdxl/chibi`の正本(textarea初期値)を
    基礎とし、今回必須の概念(letters/japanese characters/speech bubble/
    caption/onomatopoeia/manga panel border/logo/malformed hands/
    extra fingers/missing fingers/wrong costume/wrong accessories/
    chinese-style clothing/korean-style clothing/romance)のうち未収録の
    ものだけを追加
  - 生成解像度は1536×640(Stability AIがSDXL 1.0向けのoptimal inference
    resolutionとして公式文書に掲載する解像度のうち、対象コマ〔1009×345、
    縦横比約2.93:1〕に最も近いもの。対象checkpoint・対象RunPod環境での
    個別検証は未実施と明記)を採用し、対象コマ内側(1009×345)への
    リサイズ+中央クロップ(クロップ比率約17.9%)による変換仕様を実装
    (寸法計算のみ、実ピクセル処理はこの段階では未実装)。`compute_panel_fit()`
    は連続座標の参考値に加え、実ピクセル処理を将来実装する際に一意な
    結果を再現するための整数ピクセル契約(`resize_to_px`/`crop_box_px`/
    `resampling_method`、1536×640→1009×345の場合`resize_to_px=1009×421`・
    `crop_box_px=(0,38,1009,383)`・`LANCZOS`固定)も返す
  - RunPod接続先・APIキーは環境変数(`RUNPOD_API_KEY`・
    `RUNPOD_ENDPOINT_URL`)経由の設計とし、値はコード・設定ファイル・
    ログ・dry-run結果のいずれにも一切出力しない(存在確認〔真偽値〕のみ)
  - このpilotが現時点で正しく動作するキャラクターはハルトのみ
    (`SUPPORTED_TEST_CHARACTERS`)。positive promptの固定サフィックスが
    ハルトの外見を決め打ちしているため、`--character`でハルト以外を
    指定すると明確な`PilotError`で拒否される
  - `tests/test_one_panel_pilot.py`(新規、78件)を追加。既存テストは
    削除・弱体化していない。既存125件+新規分含め
    **comfyui-mobile-system側は203件全合格**
    (`python3 -m unittest discover -s tests`)。外部通信を伴うテストは
    一切なし(reference_image解決は既存tests/test_resolve_reference_image.py
    と同じ隔離手法〔tempdir+REFERENCE_IMAGES_ROOT差し替え〕を使用)
  - **Codexレビュー実施済み**(Review A: Python実装・テスト・安全性、
    Review B: 画像生成契約・寸法・既存CMSとの整合。各2ラウンドで打ち切り、
    直接ブロッキング実行・10分ハードタイムアウトの方針を厳守)。
    Review Aで5件(Major 2・Minor 3)、1回目修正後の2回目レビューで
    追加2件(Major 1・Minor 1)、Review Bで7件(Major 2・Minor 5)、
    1回目修正後の2回目レビューで追加2件(Major 1・Minor 1)を検出し、
    合計16件すべてを検証・修正・回帰テスト追加済み(Blocker/Critical
    0件)。**PR #10としてmainへsquash-merge済み**
    (https://github.com/popchami/comfyui-mobile-system/pull/10、
    squash commit `6b8c49cbbd47997beb3f6b3e687068dbc48d5438`)。
    マージ後もブランチ`one-panel-pilot-v1`は削除せず維持
- **「画像アップロード準備」と「実ピクセル変換」の実装(dry-run/mock検証・
  RunPod未起動)**。詳細は
  `profiles/sdxl/isekai_nihon_manga/ONE_PANEL_PILOT.md`11・12節参照
  - **実装ブランチ**: `one-panel-runtime-prep-v1`(main、commit
    `6b8c49cbbd47997beb3f6b3e687068dbc48d5438`〔PR #10マージ後〕から分岐)
  - `scripts/comfyui_upload.py`: ComfyUIの`/upload/image`へ正本参照画像を
    送るリクエスト構築・応答検証。実送信関数(`send_upload_request()`)は
    実装したが、このリポジトリのどこからも呼び出していない(テストは
    `requests.post`相当をmockしてのみ検証、実通信なし)。既存の
    `resolve_performer_reference_image()`が返す検証済みPathのみを受け付け、
    シンボリックリンク・正本ディレクトリ外・非PNG・PNGシグネチャ不一致・
    サイズ上限超過(16MB、既存正本PNG実測最大値の約7倍)を拒否。応答の
    `name`/`subfolder`/`type`を検証し、パストラバーサル・絶対パス・制御
    文字を拒否した上でWorkflowの`LoadImage.image`へ反映
  - `scripts/panel_pixel_convert.py`: Pillow(新規実行依存。Debian/Ubuntu系
    apt環境では`python3-pil`、venv/pip環境では`python -m pip install
    Pillow`等、環境に応じた導入方法がある)を用いて、PR #10で確定した
    整数ピクセル契約(`resize_to_px`/`crop_box_px`/`resampling_method`)を
    実際に適用し、1536×640→1009×345への実リサイズ・実クロップを実装
    (実際にローカルファイルへピクセル処理を行う、ネットワーク通信なし)。
    EXIF orientation正規化(寸法一致判定は正規化後の寸法に対して行う)・
    RGB/RGBA統一・decompression bomb対策(`DecompressionBombError`/
    `DecompressionBombWarning`の両方を変換)・入力寸法不一致の明示的拒否
    (黙って別計算しない)・複数フレーム画像(APNG等)拒否・
    置換/リンク前の一時ファイル検証・原子的書き込み(`overwrite=False`は
    `os.link()`のアトミックな存在チェック、`overwrite=True`は
    `os.replace()`)・保存後の寸法再検証を実装。対象コマinner座標は
    `one_panel_pilot.py`の既存関数(`compute_panel_fit()`/
    `load_five_panel_template()`/`get_panel_geometry()`)を再利用し、
    重複実装していない
  - **RunPod方式について判明した内容**: 既存実装(chibi HTML UI・本pilotの
    env var説明)はいずれもRunPod Serverless API
    (`api.runpod.ai/v2/...`)ではなく、RunPod Pod上のComfyUIサーバーへ
    直接HTTPアクセスする方式(Podのプロキシ経由URL)を前提にしていると
    読み取れた。ただしこれは既存コード・文書からの読み取りに基づく理解
    であり、実際にServerless API経由が必要になる可能性は排除していない
    (未確定事項として文書化、実接続前チェックリストに確認項目を追加)
  - **Codexレビュー実施済み**(Review A: Python実装・HTTP境界・安全性、
    Review B: ComfyUI契約・ピクセル幾何・統合・文書整合。各2ラウンドで
    打ち切り、直接ブロッキング実行・10分ハードタイムアウトの方針を厳守)。
    Review Aで14件(Critical 1・Major 9・Minor 4)検出、うち13件を修正・
    1件(生成解像度を1536×640固定にすべきという指摘)は既存設計
    〔`compute_panel_fit()`との一貫性〕を優先し不採用、1回目修正後の
    2回目レビューで追加5件(Major 3・Minor 2、resolverの
    manifest未登録ファイル拒否・`/proc/self/fd`経由の中間ディレクトリ
    symlink対策・`os.link()`によるoverwrite保護再設計等)を検出・修正。
    Review Bで6件(Major 1・Minor 5、アップロード`type=temp/output`時の
    LoadImage注釈欠落・subfolder区切り不整合・EXIF契約の文書明確化・
    Pillow導入方法の記載・テスト件数の記載更新)を検出・修正、1回目修正後の
    2回目レビューで追加3件(Major 1・Minor 2、name/subfolderへの
    ComfyUI予約末尾注釈`[input]`/`[temp]`/`[output]`埋め込みによる
    type検証迂回・テスト件数記載の再更新・EXIF寸法契約のONE_PANEL_PILOT.md
    本文への明記漏れ)を検出・修正。
    合計28件検出、27件を検証・修正・回帰テスト追加済み、1件は既存設計との
    一貫性を優先し理由を記録した上で不採用(Blocker/Critical残件0、
    Major/Minor残件0)
  - `tests/test_comfyui_upload.py`(新規72件)・
    `tests/test_panel_pixel_convert.py`(新規29件)・
    `tests/test_one_panel_runtime_prep_integration.py`(新規1件、
    resolver解決→upload mock→Workflow反映→実ピクセル変換までを外部通信
    なしでend-to-end再現)を追加。既存テストは削除・弱体化していない。
    **comfyui-mobile-system側は305件全合格**
    (`python3 -m unittest discover -s tests`)。外部通信を伴うテストは
    一切なし
  - **PR #11としてmainへsquash-merge済み**
    (https://github.com/popchami/comfyui-mobile-system/pull/11、
    squash commit `4eceb7ae9616c87db5b600983ed6fd2397824469`)。
    マージ後もブランチ`one-panel-runtime-prep-v1`は削除せず維持
- **単発実行経路の接続(dry-run既定・mock検証・RunPod未起動)**。詳細は
  `profiles/sdxl/isekai_nihon_manga/ONE_PANEL_PILOT.md`13節参照
  - **実装ブランチ**: `one-panel-runtime-wire-v1`(main、commit
    `4eceb7ae9616c87db5b600983ed6fd2397824469`〔PR #11マージ後〕から分岐)
  - `scripts/comfyui_run_once.py`: ハルト・panel_no=1・生成1枚に固定した
    単発実行オーケストレーター。Packet読み込み・Workflow構築・検証
    (`one_panel_pilot.run_dry_run()`を再利用)→`/upload/image`
    (`comfyui_upload.send_upload_request()`を再利用)→応答検証・
    LoadImage反映→`/prompt`送信(新規`submit_prompt()`)→prompt_id検証・
    node_errors拒否→`/history/{prompt_id}`ポーリング(新規
    `poll_history()`、有限回・有限時間、SaveImageノードの画像0枚/複数枚を
    拒否)→`/view`ダウンロード(新規`download_generated_image()`、
    Content-Type・サイズ上限・PNGシグネチャ検証、HTMLエラーページ等を
    画像として保存しない)→実ピクセル変換
    (`panel_pixel_convert.convert_generation_to_panel()`を再利用)までを
    1回の明示操作で実行する
  - **既定は常にdry-run**(通信なし)。`execute=True`(CLIでは`--execute`)
    を明示しない限りHTTPクライアントを一切呼ばない。このリポジトリの
    現時点のテスト・実行では、`execute=True`をmockなしで(実際の
    `requests`を使って)呼び出したことは一度もない
  - HTTP境界(upload/submit prompt/get history/download image)はそれぞれ
    独立し、有限timeout・HTTPステータス検証・Content-Type検証・応答
    サイズ上限・不正JSON拒否・**redirectは一律拒否**(別ホストへの
    意図しないredirectを、redirect自体を追従しないことで構造的に防ぐ)・
    `raise ... from None`による例外チェーン遮断(接続先URL・APIキーの
    非漏洩)・retryなし・session注入可能を共通実装する
  - 実行記録JSONは秘密情報を含まない(生のprompt_idの代わりにSHA-256先頭
    16桁のハッシュのみ、URL・APIキー・ローカル絶対パス・HTTP応答本文は
    一切含めない)。dry-runでは実際に完了していない項目を`true`にしない
  - `api_mode="pod-direct"`のみ実装。`api_mode="serverless"`を指定すると
    通信前に明確なエラーで拒否する(RunPod Serverless API方式は
    引き続き未確定・未実装)
  - CLIヘルプ文言に「実行するとRunPod料金が発生し得る」ことを明記
  - `tests/test_comfyui_run_once.py`(新規)を追加。既存テストは
    削除・弱体化していない。外部通信を伴うテストは一切なし
  - **commit前の最終Codexレビュー(Review A: Python実装・HTTP・安全性)を
    直接blocking方式(1回・10分上限)で実施、round 1で2件のCritical・
    9件のMajor・3件のMinor(計14件)を検出**。すべて個別に再現・検証した
    上で、妥当な指摘を最小修正した:
    - base_urlの検証(`_validate_base_url()`新規、userinfo・query・
      fragment・非httpsを拒否)を`submit_prompt()`・`poll_history()`・
      `download_generated_image()`に追加(Critical)
    - `execute`/`overwrite`の厳密なbool検証、`panel_no`のbool除外、
      出力先パス(`generation_dest_path`/`converted_dest_path`)の衝突・
      既存チェックをHTTP通信より前に実施するよう`run_once()`を修正
      (Critical)
    - `poll_history()`の総timeoutを`time.monotonic()`基準の締切時刻へ
      変更(Major、実時間ベースで確実に上限を守る)
    - `/prompt`応答の`node_errors`型検証を厳格化(`[]`等の非dict偽値を
      拒否、Major)、history `status`をホワイトリスト方式へ変更
      (`status_str=="success"`のみ許可、`cancelled`等を拒否、Major)
    - `submit_prompt()`/`poll_history()`/`comfyui_upload.send_upload_request()`
      に`stream=True`を追加(以前は応答全体を無条件でメモリへ読み切って
      からサイズ上限チェックしていた、Major)。`comfyui_upload.py`の
      アップロード応答にもredirect一律拒否・Content-Type検証・サイズ
      上限・timeout上限を追加
    - `session`省略時、`requests`モジュール自体ではなく
      `trust_env=False`の内部`requests.Session()`を使うよう変更
      (proxy環境変数・`~/.netrc`の意図しない継承を防ぐ、Major)
    - dry-runの`upload_validated`を`True`から`False`へ変更(サーバー
      応答を検証していないため、Minor)。Packet読み込み失敗時の
      `opp.PilotError`メッセージ(絶対パスを含み得る)をそのまま転記
      しないよう修正(Major)。upload応答検証失敗を`UNEXPECTED_ERROR`
      ではなく`UPLOAD_FAILED`として正しく段階付けするよう修正(Minor)
    - 回帰テストを追加(`tests/test_comfyui_run_once.py`・
      `tests/test_comfyui_upload.py`)し、テスト中の実socket通信を
      包括的に禁止・`RUNPOD_API_KEY`/`RUNPOD_ENDPOINT_URL`をテストごとに
      隔離する仕組みも追加(Minor)
    - 修正後、comfyui-mobile-system側は358件全合格、`git diff --check`も
      exit 0。外部通信を伴うテストは一切なし
    - **Review A round 2(修正差分のみを対象、直接blocking・10分上限)を
      実施し、Critical 2件・Major 4件・Minor 3件(計9件)を検出・個別
      再現・最小修正済み**:
      - `run_once()`が`base_url`検証前に`/upload/image`へPOSTしていた
        (Critical)→ 出力先パス検証より前に一度だけ`_validate_base_url()`
        を呼び、正規化済みURLを以降すべてへ渡すよう修正
      - 出力先パスの同一性判定が字句比較のみで`..`/symlinkによる別表記を
        見逃していた(Critical)→ `.resolve()`後の実体パスで比較するよう修正
      - `stream=True`化後の応答本文読み込み中の例外(Timeout等)が
        接続先URLを含んだまま漏れ得た(Major)→ 読み込みループを
        try/exceptで囲み、`response.close()`もfinallyで実行
      - monotonic締切が応答本文読み込み完了直後に再確認されていなかった
        (Major)→ 成功entry返却直前にも締切超過を確認するよう修正
      - history `status_str`のホワイトリストが実装バグで`status={}`等を
        通過させていた(Major、`status_str is not None and ...`という
        誤った条件式)→ `status.get("status_str") != "success"`への単純化で修正
      - `node_errors`のキー欠損と明示的な`null`が区別されていなかった
        (Major)→ `"node_errors" in body`判定で明示的なnullも型違反として拒否
      - 一部の回帰テストの検出力が弱かった(Minor)→ メッセージ内容の
        確認・stream例外テスト・default_session配線テスト等を追加強化
      - `opp.PilotError`のerror_codeが全件`DRY_RUN_FAILED`に潰れ、失敗
        段階を切り分けられなかった(Minor)→ 絶対パスを含まない固定
        メッセージ先頭パターンから`PACKET_NOT_FOUND`等へ分類する
        `_classify_pilot_error_code()`を追加
      - 文書に古い記述(`requests`モジュール自体を使うと誤記載)が残って
        いた(Minor)→ `ONE_PANEL_PILOT.md`を修正
      - 修正後、**comfyui-mobile-system側は369件全合格**
        (`python3 -m unittest discover -s tests`)、`git diff --check`も
        exit 0。2回目のCritical 2件のうち、base_url検証タイミングと
        dest-path同一性判定については、修正を一時的に無効化した状態で
        新規回帰テストが実際に失敗することを個別に確認した上で復元済み
      - **Review A round 2で打ち切り(2回上限)**
    - **Review B(ComfyUI契約・Workflow・統合・文書)round 1を実施し、
      Major 5件・Minor 5件(Blocker/Criticalなし)を検出・個別再現・
      最小修正済み**:
      - `validate_workflow_shape()`はnode-idの存在・型のみ確認し、
        `class_type`自体やSaveImageの一意性を検証していなかった(Major)
        → ComfyUI本体のnode-idグラフ(node 9=EmptyLatentImage、
        12=SaveImage等)に対する`_validate_fixed_workflow_contract()`を
        新規追加し、送信直前に固定契約を再検証
      - EmptyLatentImageのwidth/heightが1536×640に固定されていなかった
        (Major)→ 同関数内でwidth/height/batch_sizeを明示検証
      - history `status`欠損・非dictが成功条件を迂回できた(Major)→
        ComfyUI本体(execution.py `PromptQueue.task_done()`)のソースを
        確認し、`status`は常に`{status_str, completed, messages}`形の
        dictであることを確認した上で、欠損・非dict・
        `status_str!="success"`・`completed is not True`をすべて拒否
      - SaveImage出力のhistory画像記述が`type=input/temp`も受理していた
        (Major)→ ComfyUI本体(nodes.py `SaveImage.type="output"`固定)を
        確認し、SaveImage出力は`type=="output"`のみ許可するよう厳格化
      - 接続前文書(6節・13節)が実装と矛盾する`RUNPOD_ENDPOINT_URL`の
        説明・存在しない`--base-url`引数を案内していた(Major)→ 修正
      - `{prompt_id: null}`をキー欠損(待機継続)と区別できなかった
        (Minor)→ `prompt_id in body`判定で明示的なnullも拒否
      - 接続前チェックリストが`send_upload_request()`を「どこからも
        呼び出していない」と誤記載(Minor)→ 修正
      - 生成PNG原本の保持・失敗時ライフサイクルが未文書化(Minor)→
        13節へ追記(変換成功・失敗いずれでも原本は削除されない)
      - HANDOFF内でReview実施状況が自己矛盾していた(Minor)→ 修正
      - 対象外の未追跡`.codex/hooks.json`が存在(Minor、指摘のみ・
        レビュー対象外のため変更せず)
      - 修正後、comfyui-mobile-system側は376件全合格、`git diff --check`も
        exit 0。うち2件(node 12非SaveImage検知・EmptyLatentImage寸法
        不一致検知)は修正を一時的に無効化した状態で新規回帰テストが
        実際に失敗することを個別に確認した上で復元済み
      - **Review B round 2(修正差分のみ対象)を実施し、Major 1件・
        Minor 1件(Blocker/Criticalなし)を検出・個別再現・最小修正済み**:
        - `EXPECTED_NODE_CLASS_TYPES`がnode "1"(CheckpointLoaderSimple)・
          "6"/"8"(CLIPTextEncode×2)を網羅しておらず、これらのclass_type
          改変が送信直前検証をすり抜けていた(Major)→ 対応表へ追加、
          node "1"改変の回帰テストも追加
        - `ONE_PANEL_PILOT.md`のhistory `status`説明が厳格化前の記述の
          ままで、実装・HANDOFF記載と矛盾していた(Minor)→ ComfyUI本体
          ソースで確認したstatus形状と実装の4条件に合わせて記述を更新
        - 修正後、comfyui-mobile-system側は377件全合格、`git diff --check`
          もexit 0。node "1"改変の指摘は、修正を一時的に無効化した状態で
          新規回帰テストが実際に失敗することを個別に確認した上で復元済み
        - **Review B round 2で打ち切り(2回上限)。Review A・Review Bとも
          完了、残存Blocker/Critical/Major/Minorは0件**
      - Review A・Review Bともに完了(各2ラウンド、残存Blocker/Critical/
        Major/Minorは0件)。対象7ファイル(`docs/HANDOFF.md`・
        `profiles/sdxl/isekai_nihon_manga/ONE_PANEL_PILOT.md`・
        `scripts/comfyui_run_once.py`・`scripts/comfyui_upload.py`・
        `tests/test_comfyui_run_once.py`・`tests/test_comfyui_upload.py`・
        `tests/test_one_panel_runtime_prep_integration.py`)をcommit
        (`a5d582d68e16f944821225b72e094925b9609edb`)・
        `origin/one-panel-runtime-wire-v1`へpush済み。main向けDraft PR #12
        (https://github.com/popchami/comfyui-mobile-system/pull/12)を
        作成済み(state=OPEN, isDraft=true)。`.codex/`はスコープ外の
        既存未追跡物のままcommit対象に含めていない

## 進行中・次にやること(担当者を明記)
- **PR #9(https://github.com/popchami/comfyui-mobile-system/pull/9)の
  マージ判断**。最新状態はGitHub PRとgit履歴を参照すること
- ブランチ`one-panel-runtime-wire-v1`(単発実行経路の接続、上記完了済み
  参照)は**Review A・Review Bとも完了(各2ラウンド、残件0件)、
  commit・push・main向けDraft PR #12作成まで完了済み**(詳細は完了済み
  セクション参照)。次はDraft PR #12のレビュー・承認判断待ち。承認・
  マージ後、実際にRunPodを1回起動しての実接続検証(到達経路・認証方式の
  確定、モデル名の実在確認・組み合わせ互換性確認・Custom Nodeバージョン
  固定・実際に`comfyui_run_once.py --execute`を試験的に呼び出す)を行い、
  同一セッション内でハルト1枚だけの実生成を試みる想定
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
- [Phase 2・将来] `profiles/sdxl/isekai_nihon_manga/` 配下にSDXL+IPAdapterの
  マンガ用ComfyUI Workflowを本格構築する(データ層・取得基盤・5コマ
  テンプレート仕様・1コマ生成試験〔dry-runのみ、ハルト限定〕・画像
  アップロード契約(mock検証まで)・実ピクセルのリサイズ/クロップ処理
  (ローカルfixtureで実装・検証済み、実生成画像への適用は未検証)は
  確定・実装済み。RunPod実接続・実際の画像生成・全キャラクター/全コマ
  対応は未着手)。`scripts/one_panel_pilot.py`のWorkflow構築ロジックを
  土台に拡張する想定
- [将来] ハルト・ナツキ・アキラ・フユミ・書記官は表情/turnaround(+ナツキ・
  アキラ・書記官はequipmentも)まで登録・Release作成・実URL検証済み。
  書記官は表情31種+書記局章の正本画像が完成済みのため、旧計画にあった
  「解説カットストック(5〜10枚)の別途作成」は不要になった
  (news-game-translator側`docs/HANDOFF.md`参照)
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
  フユミ・書記官いずれもこの手順で運用、2026-07-19〜23)

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
