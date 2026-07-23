# ハルト1人・1コマ生成試験(事前準備)

異世界ニホン5コマ漫画の次工程として、実際にRunPodを起動せず(課金なし)、
Manga News Packet v2の第1コマを入力に、正本画像取得→ComfyUI(SDXL+
IPAdapter)向けAPI形式Workflow構築→RunPodへ送る予定のリクエストJSON構築
までを**dry-runで検証する**ための実装(`scripts/one_panel_pilot.py`)。

**このスクリプト自体はRunPod APIへの実送信・GPU画像生成を一切行わない。**
ネットワーク送信コードを持たず、ローカルのファイル読み込み・JSON構築・
検証のみを行う。

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
```

## 2. 再利用した既存実装(重複実装していないもの)

| 項目 | 正本の場所 | 再利用方法 |
|---|---|---|
| Packet v2構造検証・enum・`CHARACTER_REFERENCE_ID` | news-game-translator `scripts/manga_schema.py` | `importlib.util.spec_from_file_location`でファイルパスから直接読み込み(`load_manga_schema()`)。`sys.modules`の名前キャッシュに依存しないため、`NEWS_GAME_TRANSLATOR_ROOT`を切り替えた再呼び出しでも古いスキーマを誤って使い回さない(Codexレビュー指摘反映、下記参照) |
| reference_image(論理ID)解決 | このリポジトリ `scripts/resolve_reference_image.py` | 直接import(`load_resolve_reference_image()`) |
| 5コマの物理座標(第1コマのouter/inner/safe_area) | `profiles/sdxl/isekai_nihon_manga/five_panel_template.json` | JSON読み込みのみ、座標の再定義はしない |
| ComfyUI Workflowのノード名・既定パラメータ | `profiles/sdxl/chibi/comfyui_sdxl_chibi.html`(実際にこのリポジトリで使用中) | 同じノード名・既定値を踏襲(下記3節) |
| Negative promptの基礎語彙 | 同上HTMLの`#negPrompt`初期値 | 基礎として維持し、不足分のみ追加(下記5節) |

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
| 36 | `LoadImage` | 正本参照画像の読み込み(実行時は事前アップロード必須) |
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
一切出力しない。

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
- **変換方法**(`scripts/one_panel_pilot.py`の`compute_panel_fit()`、
  寸法計算のみで実ピクセル処理はこの試験段階では行わない):
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
- [ ] 実際の送信コード(本試験には含まれない、別途実装が必要)が、
      `RUNPOD_API_KEY`をログ・例外メッセージへ一切出力しないことを確認済み
- [ ] RunPod Podを不要な時間起動したままにしない運用(既存の
      `scripts/runpod_status_check.py`等で確認)

## 10. 今回の試験範囲・未実装

今回実装したのはdry-run(準備・検証)までであり、以下は含まない。

- RunPodの起動・実際のプロンプト送信・GPU画像生成
- ComfyUIへの画像アップロード(`/upload/image`)の実装
- 生成画像を実際にリサイズ・クロップするピクセル処理の実装
  (`compute_panel_fit()`は寸法・クロップ座標の計算のみ)
- 吹き出し描画・日本語文字描画・5コマ全体の合成
- ハルト以外のキャラクター・他コマ(第2〜4コマ)向けの試験データ
