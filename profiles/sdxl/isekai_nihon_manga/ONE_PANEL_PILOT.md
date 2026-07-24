# ハルト1人・1コマ生成試験(事前準備)

異世界ニホン5コマ漫画の次工程として、実際にRunPodを起動せず(課金なし)、
Manga News Packet v2の第1コマを入力に、正本画像取得→ComfyUI(SDXL+
IPAdapter)向けAPI形式Workflow構築→RunPodへ送る予定のリクエストJSON構築
までを**dry-runで検証する**ための実装(`scripts/one_panel_pilot.py`)。

**このスクリプト自体はRunPod APIへの実送信・GPU画像生成を一切行わない。**
ネットワーク送信コードを持たず、ローカルのファイル読み込み・JSON構築・
検証のみを行う。

**次工程として、以下2つの実装を追加した(下記11・12節参照)**:

- `scripts/comfyui_upload.py`: ComfyUIの`/upload/image`エンドポイントへ
  正本参照画像を送るための、安全なリクエスト構築・応答検証。**実送信関数
  自体は存在するが、このリポジトリの現時点のコード・テストのどこからも
  呼び出していない**(テストは`requests.post`相当をmockしてのみ検証する)
- `scripts/panel_pixel_convert.py`: Pillowを用いて、SDXL生成画像
  (1536×640)を実際に第1コマinner(1009×345)へリサイズ・クロップする
  ピクセル処理。**こちらは実際にローカルファイルへピクセル処理を行う**
  (ネットワーク通信は一切発生しない)

RunPodの実起動・実接続・実際のプロンプト送信・GPU画像生成は、
このどちらの実装でも行っていない。

## 1. データの流れ(Packet→Workflow)

```
Manga News Packet v2(JSON)
  └─ news-game-translator側 scripts/manga_schema.py で構造検証(正本、再利用)
       └─ panel_no=1 を選択
            └─ performers[0](試験入力ではハルト1人に限定)
                 ├─ expression タグ
                 └─ reference_image(論理ID、例: haruto/surprise-weak.png)
                      └─ このリポジトリの scripts/resolve_reference_image.py で
                         実ファイルパスへ解決(正本、再利用)
                              └─ 実在する正本PNG(GitHub Release資産取得済み)
  └─ panel.image_prompt(英語、scene/backgroundの日本語生テキストは
     SDXLへ直接渡さない)
       + panel.framing / camera_angle・performer.position / facing / gaze
         (既知enumから決定論的に英語句へ変換して追加、2回目のCodexレビュー
          指摘反映)
       └─ positive prompt 組み立て(固定のキャラクター/様式制約を付加)
  └─ negative prompt(既存 profiles/sdxl/chibi の正本を基礎に不足分を追加、
     さらにpanel.negative_prompt〔コマ固有の除外事項〕も重複排除しながら
     追加、2回目のCodexレビュー指摘反映)
       └─ ComfyUI API形式Workflow(class_type形式のノードグラフ)構築
            └─ RunPodへ送る予定のリクエストJSON(dry-run、実送信しない)
  └─ profiles/sdxl/isekai_nihon_manga/five_panel_template.json の
     panel_no=1 の inner(1009×345)へ収める変換仕様(寸法計算のみ)

  (次工程・今回追加分)
  └─ reference_image_path(正本参照画像) → scripts/comfyui_upload.py で
     `/upload/image`リクエストを構築(dry-run)・応答検証
       └─ 検証済みサーバー側画像名 → Workflowの`LoadImage.image`へ反映
            (apply_uploaded_image_to_workflow())
  └─ ComfyUIが返す予定の生成画像(1536×640) → scripts/panel_pixel_convert.py
     の convert_generation_to_panel() で実際にリサイズ・クロップ
       └─ 1009×345のPNG(第1コマinnerと一致)
```

## 2. 再利用した既存実装(重複実装していないもの)

| 項目 | 正本の場所 | 再利用方法 |
|---|---|---|
| Packet v2構造検証・enum・`CHARACTER_REFERENCE_ID` | news-game-translator `scripts/manga_schema.py` | `importlib.util.spec_from_file_location`でファイルパスから直接読み込み(`load_manga_schema()`)。`sys.modules`の名前キャッシュに依存しないため、`NEWS_GAME_TRANSLATOR_ROOT`を切り替えた再呼び出しでも古いスキーマを誤って使い回さない(Codexレビュー指摘反映、下記参照) |
| reference_image(論理ID)解決 | このリポジトリ `scripts/resolve_reference_image.py` | 直接import(`load_resolve_reference_image()`) |
| 5コマの物理座標(第1コマのouter/inner/safe_area) | `profiles/sdxl/isekai_nihon_manga/five_panel_template.json` | JSON読み込みのみ、座標の再定義はしない |
| ComfyUI Workflowのノード名・既定パラメータ | `profiles/sdxl/chibi/comfyui_sdxl_chibi.html`(実際にこのリポジトリで使用中) | 同じノード名・既定値を踏襲(下記3節) |
| Negative promptの基礎語彙 | 同上HTMLの`#negPrompt`初期値 | 基礎として維持し、不足分のみ追加(下記5節) |
| 生成解像度→対象コマinnerへの寸法・クロップ契約(整数ピクセル) | `scripts/one_panel_pilot.py`の`compute_panel_fit()`/`load_five_panel_template()`/`get_panel_geometry()` | `scripts/panel_pixel_convert.py`から直接import・再利用(寸法計算ロジックの重複実装はしない) |
| HTTP通信ライブラリ | `requests`(`scripts/runpod_status_check.py`が既にこのリポジトリで使用中の既存依存) | `scripts/comfyui_upload.py`が同じ`requests`を使用(新規依存の追加ではない) |

解決した参照画像は、`.is_file()`かつ拡張子`.png`であることを
`resolve_performer_reference_image()`が追加で検証する(Codexレビュー
指摘、Minor: manifest.jsonが画像でないファイルへ対応付けていても
`LoadImage`へそのまま渡ってしまっていた)。

`CHARACTER_REFERENCE_ID`やenum値をこのリポジトリ側へ複製した箇所はない。
`scripts/one_panel_pilot.py`の関数群はキャラクター名を引数として受け取る
設計だが、`build_positive_prompt()`の固定サフィックス(髪型・衣装・胸の
桜チャーム等)は現時点でハルトの外見を決め打ちしている。そのため
`run_dry_run()`・CLIの`--character`は`SUPPORTED_TEST_CHARACTERS = ("ハルト",)`
以外を指定すると明確なPilotErrorで拒否する(2回目のCodexレビュー指摘、
Minor: 以前は他キャラクターを指定してもscope検証自体は通ってしまい、
IPAdapter参照画像とテキストconditioningのキャラクターが食い違う恐れが
あった)。将来的に他キャラクターへ対応する場合は、外見の固定サフィックス
自体をキャラクターごとの正本(manifest等)から取得する設計へ拡張する
必要がある。

## 3. 採用したComfyUIノード(API形式Workflow)

すべて`profiles/sdxl/chibi/comfyui_sdxl_chibi.html`が実際に使用している
ノード名・接続パターンを踏襲(新規の当て推量ノード名は使っていない)。

| node_id | class_type | 役割 |
|---|---|---|
| 1 | `CheckpointLoaderSimple` | SDXLチェックポイント読み込み |
| 6 | `CLIPTextEncode` | positive prompt |
| 8 | `CLIPTextEncode` | negative prompt |
| 35 | `CLIPVisionLoader` | IPAdapter用CLIP Vision読み込み |
| 36 | `LoadImage` | 正本参照画像の読み込み。`image`フィールドには`scripts/comfyui_upload.py`が構築した`/upload/image`アップロード契約の検証済み応答(サーバー側ファイル名)を反映する(下記11節)。実行時は事前アップロードが必須 |
| 30 | `IPAdapterUnifiedLoader` | IPAdapterモデル読み込み |
| 31 | `IPAdapterAdvanced` | 参照画像の適用 |
| 9 | `EmptyLatentImage` | 生成解像度・生成枚数(batch_size)の指定 |
| 10 | `KSampler` | サンプリング(seed固定・steps・cfg等) |
| 11 | `VAEDecode` | 潜在空間→画像デコード |
| 12 | `SaveImage` | 出力保存 |

`CheckpointLoaderSimple`・`CLIPTextEncode`・`CLIPVisionLoader`・
`LoadImage`・`EmptyLatentImage`・`KSampler`・`VAEDecode`・`SaveImage`は
ComfyUI本体組み込みノード。`IPAdapterUnifiedLoader`・`IPAdapterAdvanced`
のみ、後述の必須Custom Nodeが必要。

## 4. 必須Custom Node

| 名称 | 用途 | 取得元 | バージョン固定 |
|---|---|---|---|
| ComfyUI_IPAdapter_plus | `IPAdapterUnifiedLoader`/`IPAdapterAdvanced`ノードを提供 | `https://github.com/cubiq/ComfyUI_IPAdapter_plus`(このリポジトリの`profiles/sdxl/chibi/setup_sdxl.ipynb`で実際にcloneしている、実在確認済み) | **未実施**。現行のsetupノートブックはclone時点の最新を使うのみで、commit/タグ固定は行っていない。実際にRunPodへ接続する前に、動作確認が取れたcommit hashをこのファイルへ追記すること(推測でバージョン番号を記載しない) |

## 5. モデル名を設定する場所

コード(`scripts/one_panel_pilot.py`)側にモデル名・IPAdapterプリセット・
CLIP Vision名を決め打ちしていない。すべて設定ファイル経由で渡す。

- 既定の設定ファイル: `profiles/sdxl/isekai_nihon_manga/one_panel_pilot/config.example.json`
- 差し替え方法: `python3 scripts/one_panel_pilot.py <packet> --config <自分の設定ファイルパス>`
- 設定ファイル内の`checkpoint_name`・`clip_vision_name`・`ipadapter_preset`は、
  `profiles/sdxl/chibi/comfyui_sdxl_chibi.html`の既定値を踏襲しているが、
  **対象RunPod環境に実在するモデル名であることは未検証**。実行前に必ず
  ComfyUIの`/object_info`または実際のモデルフォルダで確認すること
- 設定ファイルに必須キー(`checkpoint_name`・`clip_vision_name`・
  `ipadapter_preset`・`ipadapter_weight`・`sampler_name`・`scheduler`・
  `steps`・`cfg`・`generation_width`・`generation_height`)が1つでも
  不足している場合、`load_config()`が欠落キー名を列挙した`PilotError`を
  送出する(Codexレビュー指摘、Minor: 以前は`build_comfyui_workflow()`側で
  素の`KeyError`が送出されていた)

## 6. RunPod接続用環境変数(値はどこにも保存しない)

| 環境変数 | 用途 |
|---|---|
| `RUNPOD_API_KEY` | RunPod API認証キー(実送信時のみ、その場でAuthorizationヘッダーへ設定。dry-run結果には含めない) |
| `RUNPOD_ENDPOINT_URL` | ComfyUIの`/prompt`エンドポイントURL(RunPod Pod起動後に決まる動的な値) |
| `NEWS_GAME_TRANSLATOR_ROOT`(任意) | news-game-translatorのローカルチェックアウトパス。既定値は`/root/news-game-translator` |

`.env`は`.gitignore`対象(既存)。`config.example.json`・このドキュメントの
どこにも実値は書いていない。dry-run結果(`runpod_env_vars_present`)は
各環境変数が**設定されているかどうかの真偽値のみ**を返し、値そのものは
一切出力しない。`scripts/comfyui_upload.py`・`scripts/panel_pixel_convert.py`
も同様に、APIキー・接続先の実値をログ・例外メッセージへ一切出力しない
(下記11節)。

**RunPod方式についての現時点の理解(未確定事項あり)**: このリポジトリの
既存実装(`profiles/sdxl/chibi/comfyui_sdxl_chibi.html`等のブラウザUI、
および本pilotの`RUNPOD_ENDPOINT_URL`の説明文)は、いずれもRunPodの
Serverless API(`https://api.runpod.ai/v2/{endpoint_id}/run(sync)`)では
なく、**RunPod Pod上で直接動くComfyUIサーバーへHTTPアクセスする方式**
(Podのプロキシ経由URL、例: `https://xxxxx-8188.proxy.runpod.net`)を
前提に設計されている。`scripts/runpod_status_check.py`が使う
`api.runpod.io`のGraphQL APIは、Pod起動状況・課金確認用の別物であり、
画像生成のプロンプト送信やアップロードには使われていない。

ただし、これは既存コード・文書からの読み取りに基づく理解であり、
**実際にRunPod Serverless API経由での接続が必要になる可能性を排除する
ものではない**。この環境だけでは確定できないため、一方の方式に推測で
固定していない。実接続前に、対象RunPod環境が実際にどちらの方式で
ComfyUIへ到達させる想定か(Pod直接プロキシURLか、Serverless APIの
入力エンベロープ〔`{"input": {...}}`等〕でラップする必要があるか)を
確認すること(下記9節のチェックリストに追加項目あり)。

## 7. 生成解像度と1009×345への変換方法

第1コマの内側(inner)は1009×345px(`five_panel_template.json`より)。
SDXLはこの極端に横長・低い高さの解像度を直接学習していないため、直接
1009×345で生成することはしない。

- **採用した生成解像度: 1536×640px**
  Stability AIがSDXL 1.0向けのoptimal inference resolution(21:9
  ultrawide)の一つとして公式文書に掲載している解像度([Stability AI SDXL
  documentation](https://stability.ai/sdxl-aws-documentation)、参考:
  [SDXL technical report](https://arxiv.org/abs/2307.01952)は複数アスペクト
  比での学習を説明している)。対象コマの縦横比(1009:345 ≈ 2.93:1)に
  最も近い、公式に掲載された解像度として選定した(2回目のCodexレビュー
  指摘、Minor: 以前は「SDXL公式の学習済み解像度バケット表」と断定していたが、
  「学習時に使われた正確なbucket」であることまでは一次資料で確認できて
  いないため、「公式のoptimal inference resolutionとして掲載」という
  表現へ和らげた)。対象checkpoint(`animagine_xl4_opt.safetensors`)や
  対象RunPod環境で個別に検証したものではない
- **変換方法**(寸法計算は`scripts/one_panel_pilot.py`の
  `compute_panel_fit()`、**実ピクセル処理は`scripts/panel_pixel_convert.py`
  の`convert_generation_to_panel()`で実装済み**〔Pillow使用、下記12節〕):
  1. 生成画像(1536×640)を、幅が対象コマの内側幅(1009px)に一致するよう
     等比縮小する → 縮小後の高さは約420.42px
  2. 縮小後の高さ(約420.42px)から、対象コマの内側高さ(345px)を
     縦方向中央基準でクロップする(クロップ量は上下合計約75.42px、
     縮小後高さに対する比率は約17.9%)
  3. 最終出力は1009×345(内側〔inner〕と完全一致)

人物の顔・手・必須装備(桜チャーム等)を切らないため、Packetの`framing`
(waist/bust等)により被写体が縦方向中央付近へ収まる構図をプロンプト側で
維持することを前提とする。ただしこれは**プロンプトによる努力目標であり、
ハード保証ではない**(SDXLの生成結果がプロンプト通りの構図に必ずなる
保証はない)。クロップ比率が大きい場合(目安: 30%超)は、生成解像度の
見直し(より横長寄りの解像度の検討)を推奨する(`compute_panel_fit()`は、
縮小後高さが対象高さに届かない場合は明確なエラーを送出する。届く場合でも
クロップ比率が大きいことまでは自動判定していない点は今後の課題)。

`compute_panel_fit()`の戻り値には、連続座標の参考値(`resize_to`・
`crop_box`・`crop_ratio`、小数第2位までの表示用丸め)に加えて、実際に
ピクセル処理を実装する際に一意な結果を再現するための**整数ピクセル契約**
(`resize_to_px`・`crop_box_px`・`resampling_method`)を含める(2回目の
Codexレビュー指摘、Major: 連続座標の丸め値だけでは、縮小後の高さを420px
にするか421pxにするか、余り1pxを上下どちらに配分するかが実装者・使用
ライブラリ次第でばらつき、「同じ変換仕様」という契約が成立しなかった)。

4引数(`generation_width`・`generation_height`・`target_width`・
`target_height`)はいずれも正の整数(bool不可)に限定し、整数演算のみで
計算する(さらに2回目のCodexレビュー指摘、Major: 以前はfloatも許可して
いたため`resize_to_px`等へfloatが混入しうる上、`math.ceil(浮動小数点)`
という切り上げ方式が極端に大きい入力で以下の式とずれる場合があった)。

- `resized_height_px = (generation_height × target_width + generation_width - 1)
  // generation_width`(整数演算のみによる切り上げ除算。1536×640→1009×345
  の場合: `421`px)
- `crop_total_px = resized_height_px - target_height`(同: `76`px)
- `crop_top_px = crop_total_px // 2`(余り1pxは下側へ配分。同: 上下とも`38`px)
- `crop_box_px`は半開区間`(left, upper, right, lower)`(Pillowの
  `Image.crop()`と同じ規約。同: `(0, 38, 1009, 383)`)
- リサンプリングフィルタは`PANEL_FIT_RESAMPLING_METHOD`(`LANCZOS`)固定

**safe_area保証の扱い(実ピクセル変換を実装した後も変わらず)**:
`convert_generation_to_panel()`は寸法通りに正確なリサイズ・クロップを
行うが、クロップ後の画像に人物が実際にsafe_area相当の位置へ収まって
いるかどうかまでは検証しない(戻り値に含まれる
`safe_area_containment_verified: False`はこれを明示する固定値)。
これはプロンプト側の構図制御(`framing`等)による努力目標のままであり、
実際に人物が意図通りの位置に写っているかは、生成画像そのものを見る
画像内容検査(次工程)が別途必要である。

## 8. 実行手順(RunPod未起動・課金なしで完結)

```bash
cd /root/comfyui-mobile-system
python3 scripts/one_panel_pilot.py \
  profiles/sdxl/isekai_nihon_manga/one_panel_pilot/haruto_panel1.example.json
```

- 既定では`config.example.json`を使用する(`--config`で差し替え可能)
- 既定では`panel_no=1`・キャラクター`ハルト`を対象とする(`--panel-no`は
  変更可能。`--character`は現時点で`ハルト`以外を指定すると`PilotError`に
  なる。2節参照)
- 標準出力へdry-run結果(Workflow・panel_fit・RunPod送信予定リクエスト等)
  をJSONで出力する。**この時点でRunPodへの通信は一切発生しない**

事前にハルトの正本画像が未取得の場合は、以下を実行してから試験すること
(このコマンド自体はGitHub Releaseへの通信を伴うため、必要な場合のみ
実行する。既に取得済みなら不要):

```bash
python3 scripts/fetch_reference_images.py --character haruto
```

## 9. RunPod接続前チェックリスト(実際にRunPodを起動する段になったら)

- [ ] `.env`または環境変数に`RUNPOD_API_KEY`・`RUNPOD_ENDPOINT_URL`を設定済み
      (このリポジトリへcommitしないこと)
- [ ] 対象RunPod環境のComfyUIで、`config.json`内の`checkpoint_name`・
      `clip_vision_name`が実在することを`/object_info`または
      モデルフォルダで確認済み
- [ ] `ComfyUI_IPAdapter_plus`custom nodeが導入済みで、動作確認が取れた
      commit hashを本ドキュメント4節へ追記済み
- [ ] 上記は各モデル・custom nodeが「個別に実在する」ことの確認に過ぎない。
      `checkpoint_name`内蔵VAE・CLIP Vision・`ipadapter_preset`から
      解決される実IPAdapterファイル・固定したcustom node commitの
      **組み合わせ全体でWorkflowが実際にロード・推論可能であること**は
      未検証(2回目のCodexレビュー指摘、Minor)。実際にRunPodへ接続する
      前に、この組み合わせでの動作確認を別途行うこと
- [ ] `python3 scripts/one_panel_pilot.py <packet>`のdry-run結果を確認し、
      `runpod_request_dry_run.prompt`の内容(モデル名・プロンプト・
      パラメータ)が意図通りであることを目視確認済み
- [ ] 生成枚数(`batch_size`)が1であることを確認済み(コスト最小化)
- [ ] 実際の送信コード(`scripts/comfyui_upload.py`の
      `send_upload_request()`をこのリポジトリのどこからも呼び出して
      いない。実際に使う前に、下記項目を確認すること)が、
      `RUNPOD_API_KEY`をログ・例外メッセージへ一切出力しないことを確認済み
- [ ] RunPod Podを不要な時間起動したままにしない運用(既存の
      `scripts/runpod_status_check.py`等で確認)
- [ ] **対象RunPod環境の実際のComfyUI到達経路を確認済み**: RunPod Pod
      直接のプロキシURL(`https://xxxxx-8188.proxy.runpod.net`)へ
      `/prompt`・`/upload/image`をそのまま送ってよいのか、RunPod
      Serverless API(`https://api.runpod.ai/v2/{endpoint_id}/run(sync)`)
      経由でラップする必要があるのか未確定(6節参照)。対象環境の
      ドキュメント・実際のPod起動時の案内URLで確認すること
- [ ] 認証方式を確認済み: `RUNPOD_API_KEY`をAuthorizationヘッダーへ
      設定する方式(Serverless API想定)か、Pod直接プロキシURLで
      認証自体が不要な方式か(既存`comfyui_sdxl_chibi.html`のブラウザ
      UIはAPIキー入力欄自体を持たない)
- [ ] `scripts/comfyui_upload.py`の`send_upload_request()`を、実際の
      `base_url`に対して一度だけ試験的に呼び出し、応答の`name`・
      `subfolder`・`type`が想定通りであることを確認済み(この時点では
      まだ実画像生成は行わない)
- [ ] `scripts/panel_pixel_convert.py`の`convert_generation_to_panel()`
      を、実際にComfyUIが生成した1536×640画像に対して一度試験的に
      実行し、出力1009×345を目視確認済み(人物の頭・手・桜チャームが
      切れていないか、safe_area相当の位置に収まっているかを含む。
      これは自動検証されない、7節参照)

## 10. 今回の試験範囲・未実装

今回実装したのは、dry-run(準備・検証)に加えて、画像アップロードの
リクエスト構築・応答検証(`scripts/comfyui_upload.py`)と実ピクセル変換
(`scripts/panel_pixel_convert.py`)までであり、以下は含まない。

- RunPodの起動・実際のプロンプト送信・GPU画像生成
- ComfyUIへの画像アップロードの**実送信**(`send_upload_request()`は
  実装済みだが、このリポジトリのどこからも呼び出していない。実送信には
  実際の`base_url`と、6節記載のRunPod方式〔Pod直接 or Serverless API〕の
  確定が必要)
- RunPod Serverless API(`api.runpod.ai/v2/...`)を経由する場合の
  リクエスト形式(`{"input": {...}}`等でのラップ)への対応
  (現時点でPod直接プロキシURL方式のみを前提に実装している)
- 吹き出し描画・日本語文字描画・5コマ全体の合成
- ハルト以外のキャラクター・他コマ(第2〜4コマ)向けの試験データ
- 生成画像内に人物が実際にsafe_area相当の位置へ収まっているかどうかの
  自動検査(`convert_generation_to_panel()`は寸法・クロップのみを保証し、
  画像内容そのものは検査しない)

**次工程**: 実環境(対象RunPod・ComfyUI)の読み取り確認(到達経路・認証
方式・モデル実在・組み合わせ互換性)を行った上で、ハルト1枚だけを実際に
生成する試験を行うこと。全キャラクター・全コマの本番生成は、その後の
別工程とする。

## 11. 画像アップロード契約(`scripts/comfyui_upload.py`)

ComfyUIの`/upload/image`エンドポイントへ、正本参照画像PNGを送るための
リクエスト構築・応答検証。**実際にRunPod・ComfyUIへ送信する処理
(`send_upload_request()`)は実装したが、このリポジトリのどこからも
呼び出していない。**テストは`requests.post`相当をmockしてのみ検証する。

- **アップロード対象の検証**(`validate_upload_source_path()`): 既存
  `resolve_performer_reference_image()`が返した検証済みPathのみを受け付ける
  (basename文字列を直接渡さない)。その上で独自に再検証する:
  シンボリックリンク拒否・正本ディレクトリ
  (`resolve_reference_image.REFERENCE_IMAGES_ROOT`)内であることの再確認・
  `<character>/<既知categoryの配置先>/<filename>`という既知の構造への
  一致、かつそのcharacter/categoryの`manifest.json`に実際に登録された
  ファイル名であることの確認(`_is_registered_in_manifest()`。1回目の
  Codexレビュー指摘で構造チェックのみ導入、2回目のレビューで
  「構造は正しいがmanifestに未登録のファイル」も拒否できていない点を
  指摘され、manifest.jsonの値との突き合わせまで強化した。
  `reference_image_categories.CATEGORY_PLACE_TO`/`CATEGORY_MANIFEST_REL`を
  再利用し、resolve_reference_image.py側のトラバーサル対策自体は
  重複実装しない)・拡張子`.png`限定・ファイルサイズ上限・PNGシグネチャ
  (先頭8バイト)一致
- **TOCTOU対策**(`send_upload_request()`内部の`_read_and_verify_source_bytes()`):
  実送信時は、パス検証・PNGシグネチャ確認・ハッシュ計算・送信を、
  `os.O_NOFOLLOW`で開いた同一のファイル内容から一度だけ行う(1回目の
  Codexレビュー指摘、Major対応: 以前は検証・ハッシュ計算・送信で別々に
  ファイルをopenしており、検証後から送信までの間にファイルが差し替え
  られても検出できない窓があった)。`O_NOFOLLOW`は最終pathコンポーネント
  のシンボリックリンクのみを防ぐため、Linux環境では`/proc/self/fd`経由で
  実際にopenされた実体の経路を読み直し、依然として正本root配下にあるかを
  openの直後に再確認する(2回目のCodexレビュー指摘、Major対応: 検証から
  openまでの間に中間ディレクトリ自体がシンボリックリンクへ差し替えられる
  レースは、最終コンポーネント保護だけでは防げない。`/proc`が利用できない
  環境ではこの追加チェックのみ静かにスキップされる)
- **ファイルサイズ上限**: `MAX_UPLOAD_FILE_SIZE_BYTES = 16MB`。既存の
  正本PNGの実測最大サイズ(約2.28MB、akira/equipment配下)の約7倍、
  ハルト表情PNG(1254×1254)のRGBA非圧縮換算(約6.0MB)の約2.6倍の余裕を
  持たせた、実測値に基づく根拠のある値
- **同名衝突を避ける命名規則**(`build_upload_filename()`): 元ファイル
  内容のSHA-256先頭12桁を付与した決定論的なファイル名
  (`{stem}_{12桁hex}{拡張子}`)。同一内容なら常に同一名、内容が異なれば
  別名になる(乱数を使わないため再現可能)
- **overwriteの扱い**: リクエストの`form_fields.overwrite`は既定`"false"`。
  同名衝突自体は上記の内容ハッシュ命名で避ける設計とし、overwriteは
  それでも衝突した場合の明示的な意思表示として扱う
- **応答検証**(`validate_upload_response()`): `name`・`subfolder`・`type`が
  すべて文字列であること、`type`が`input`/`temp`/`output`のいずれかで
  あること、絶対パス・`..`・制御文字が含まれていないことを検証する。
  `name`は単一のファイル名(basename相当)のみを許可し、パス区切りを
  1文字でも含めば拒否する(2回目のCodexレビュー指摘、Minor対応:
  以前は`nested/a.png`のような複数segmentのnameも誤って受理していた)。
  複数segmentは`subfolder`のみ許可する。1つでも不正ならエラーにし、
  `LoadImage.image`へは反映しない
- **Workflowへの反映**(`apply_uploaded_image_to_workflow()`):
  `build_load_image_value()`/`apply_uploaded_image_to_workflow()`自身が
  内部で改めて`validate_upload_response()`を通す(2回目のCodexレビュー
  指摘、Major対応: 以前は引数名が`validated_response`であるだけで、
  実際には未検証の応答をそのままWorkflowへ反映できてしまっていた)。
  検証済みの`name`/`subfolder`から、ComfyUI本体の実仕様通り`subfolder`が
  空でなければ`subfolder/name`形式の値を組み立て、node_id="36"
  (`LoadImage`、`class_type`もここで検証)の`image`フィールドへ設定した
  **workflowのコピー**を返す(元のworkflowは変更しない)
- **HTTPクライアント境界**(`send_upload_request()`): `base_url`・
  `session`(省略時は`requests`モジュール自体)を引数に取り、実接続時に
  `requests.Session()`を再利用できるようにする。timeout(bool・非有限・
  非正の値は事前に拒否)・HTTPエラー・不正JSON・欠損応答をそれぞれ明確な
  エラーへ変換する。`image_type`もdry-run構築時と同じ検証を通す
  (2回目のCodexレビュー指摘、Major対応: 以前は実送信関数側でこの検証が
  抜けていた)。**retryは行わない**(1回のリクエストのみ。無制限の
  自動リトライはしない)
- **秘密情報の非出力**: タイムアウト・接続エラー時は`raise ... from None`で
  元のrequests例外を連鎖させず、例外メッセージだけでなく`__cause__`・
  traceback経由でも接続先URL・APIキーの値を一切含めない(2回目の
  Codexレビュー指摘、Critical対応: 以前は`from e`で連鎖させていたため、
  `str(exception)`自体は安全でも、`logger.exception()`等が出す
  traceback経由でrequests例外本文〔接続先URLを含み得る〕が漏れ得た)

## 12. 実ピクセル変換の実装(`scripts/panel_pixel_convert.py`)

`scripts/one_panel_pilot.py`の`compute_panel_fit()`が確定した整数ピクセル
契約(`resize_to_px`/`crop_box_px`/`resampling_method`)を、Pillowで実際に
適用する(`convert_generation_to_panel()`)。対象コマのinner座標は
`five_panel_template.json`から読み込み、ハードコードしない。

安全対策:

- **EXIF orientation正規化**: `PIL.ImageOps.exif_transpose()`で安全に適用
  (EXIF情報がない画像は無変更)。**寸法契約(Review B 2回目の指摘、Minor
  対応で明記)**: decompression bomb対策のピクセル数・辺の長さ上限は
  EXIF正規化「前」の保存寸法に対して適用し、`generation_width`×
  `generation_height`との一致判定はEXIF正規化「後」の寸法に対して行う。
  そのため、保存上は縦横が入れ替わっていてもEXIF orientationにより
  正規化後の寸法が期待値と一致する画像は受理される
- **RGB/RGBA統一**: 透過情報を持つ場合(`RGBA`/`LA`/透過付き`P`)は
  `RGBA`、それ以外は`RGB`へ変換する
- **破損・非対応形式の拒否**: `Image.open()`後に`.load()`で強制的に
  全体をデコードし、`UnidentifiedImageError`/`OSError`/`ValueError`を
  明確な`PanelPixelConvertError`へ変換する
- **複数フレーム画像の拒否**: デコード前に`n_frames`を確認し、アニメーション
  PNG等の複数フレーム画像は明確に拒否する(2回目のCodexレビュー指摘、
  Minor対応: 以前は最初のフレームだけを黙って静止画として変換していた)
- **decompression bomb対策**: ヘッダー読み取り直後(全体デコード前)に
  ピクセル数上限(`MAX_INPUT_PIXELS = 20,000,000`px、既定生成解像度
  1536×640=983,040pxの約20倍の余裕)・辺の長さ上限
  (`MAX_INPUT_DIMENSION_PX = 10,000`px)を確認し、超過する画像は
  デコードする前に拒否する。Pillow自体の`DecompressionBombWarning`も
  エラーへ昇格させる
- **入力寸法の不一致を明示的に拒否**: 実際の入力画像の寸法が
  `generation_width`×`generation_height`(既定1536×640)と異なる場合、
  **黙って別の縮小率で計算し直さず**、明確な`PanelPixelConvertError`を
  送出する。`panel_no`・`generation_width`・`generation_height`は
  bool不可の正の整数、`overwrite`はbool型であることを関数入口で検証し、
  `one_panel_pilot.compute_panel_fit()`側の`OverflowError`等が素のまま
  漏れないようにする(2回目のCodexレビュー指摘、Minor対応)
- **出力形式・上書き防止**: 出力は常にPNG。出力先(`dest_path`)が既に
  存在する場合は`overwrite=True`を明示しない限り拒否する。`overwrite=False`
  時は、検証済み一時ファイルを`os.link()`でdest_pathへアトミックに
  「存在しなければ作成」する(`FileExistsError`を検知)。1回目のCodex
  レビューでは`os.O_CREAT|os.O_EXCL`で空のプレースホルダーを事前確保
  してから最終的に`os.replace()`する2段階方式を採用したが、2回目の
  レビューで「検証失敗時のプレースホルダー削除処理が、その間に別プロセスが
  正当に書き込んだ内容まで誤って削除しうる」新たなバグを指摘され、
  `os.link()`方式へ変更した(dest_pathを一切unlinkしないため、その種の
  バグの発生条件自体がなくなる)。`overwrite=True`時は従来通り
  `os.replace()`を使う。入力画像と出力先が同一パスの場合も拒否する
  (元画像を上書きしない)
- **原子的な書き込みと置換・リンク前検証**: 出力先と同じディレクトリに
  一時ファイルを作成し、`os.replace()`/`os.link()`で確定させる前に、
  一時ファイル自体を開き直して形式(PNG)・寸法を検証する(1回目のCodex
  レビュー指摘、Major対応: 以前は置換後に検証していたため、検証失敗時に
  `overwrite=True`時の既存の正常な出力を回復できなかった)。この検証で
  発生するPillow由来の例外も`PanelPixelConvertError`へ統一する
  (2回目のCodexレビュー指摘、Minor対応)。失敗時は一時ファイルを削除し、
  最終パスには不完全な内容を残さない
- **保存後の再検証**: 置換・リンク後も改めて`Image.open()`で開き直し、
  形式・寸法が対象コマのinnerと一致することを再確認する(置換前検証と
  合わせた二重確認。ここでのPillow由来の例外も統一する)
- **five_panel_template.jsonとの整合性**: 変換に使うinner座標は
  `load_five_panel_template()`/`get_panel_geometry()`経由でJSONから
  読み込む(座標のハードコード・重複定義はしない)

戻り値には、実際に適用した`resize_to_px`/`crop_box_px`/
`resampling_method`・最終寸法・保存先パスに加えて、
`safe_area_containment_verified: False`(常に固定値)を含める。これは
「人物が実際にsafe_area相当の位置に収まっているか」はこの変換処理では
検証できないことを明示するためのフィールドであり、次工程の画像内容検査が
別途必要であることを示す(7節参照)。
