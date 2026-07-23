#!/usr/bin/env python3
"""異世界ニホン5コマ漫画「ハルト1人・1コマ生成試験」の事前準備スクリプト。

Manga News Packet v2の第1コマ(panel_no=1)を入力に、正本画像取得から
ComfyUI(SDXL+IPAdapter)向けAPI形式Workflow構築、RunPodへ送る予定の
リクエストJSON構築までを**dry-runでのみ**実行する。RunPod APIへの実送信・
GPU画像生成は一切行わない(このモジュール自体がネットワーク送信コードを
持たない)。

正本・再利用方針:

- Manga News Packetの構造検証・enum・キャラクター名↔ローマ字ID対応
  (`CHARACTER_REFERENCE_ID`)は、news-game-translator側
  `scripts/manga_schema.py`を唯一の正本とし、本モジュールでは重複実装
  しない(`importlib.util.spec_from_file_location`でファイルパスから
  直接読み込んで再利用する。`sys.modules`の名前キャッシュには依存しない)
- reference_image(論理ID)から実ファイルへの解決は、このリポジトリの
  `scripts/resolve_reference_image.py`をそのまま再利用する
- 5コマテンプレートの座標(第1コマのouter/inner/safe_area)は
  `profiles/sdxl/isekai_nihon_manga/five_panel_template.json`を正本とする

ComfyUI Workflow(API送信用)のノード構成・パラメータ名は、このリポジトリの
既存SDXLプロファイル(`profiles/sdxl/chibi/comfyui_sdxl_chibi.html`)が
実際に使用しているノード名・既定値を踏襲する(未検証のノード名・モデル名を
新規に創作しない)。ただしモデル名・IPAdapterプリセット等の実環境依存値は
`config.example.json`(このディレクトリ)またはこのモジュールの設定引数で
差し替え可能にする。

標準ライブラリのみを使用する(json, os, re, sys, pathlib, unicodedata)。
"""
import copy
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIVE_PANEL_TEMPLATE_PATH = ROOT / "profiles" / "sdxl" / "isekai_nihon_manga" / "five_panel_template.json"
DEFAULT_CONFIG_PATH = (
    ROOT / "profiles" / "sdxl" / "isekai_nihon_manga" / "one_panel_pilot" / "config.example.json"
)

# news-game-translator(別リポジトリ)のデフォルトパス。scripts/
# collect_manga_reference_images.py(news-game-translator側)の
# DEFAULT_COMFYUI_MOBILE_SYSTEM_PATHと対称の設計(絶対パスの既定値+
# 環境変数での上書き)。
DEFAULT_NEWS_GAME_TRANSLATOR_ROOT = Path("/root/news-game-translator")

# ComfyUIの実プロンプト送信先・RunPod APIキーは、値をコード/設定/ログへ
# 保存せず、実行時に環境変数から読むだけにする(dry-runでは値を一切
# 参照・出力しない。存在確認のみ行う)。
RUNPOD_ENV_VARS = [
    "RUNPOD_API_KEY",
    "RUNPOD_ENDPOINT_URL",
]
# news-game-translatorリポジトリの場所を上書きしたい場合に使う(任意)。
NEWS_GAME_TRANSLATOR_ROOT_ENV_VAR = "NEWS_GAME_TRANSLATOR_ROOT"

# 既存 profiles/sdxl/chibi/comfyui_sdxl_chibi.html のネガティブプロンプト
# 正本(textarea初期値)。これを基礎とし、今回の試験で必須の概念だけを追加する
# (「既存プロファイルのnegative prompt正本がある場合は、それを基礎として
# 不足分だけ追加する」というチャミの指示に従う)。
BASE_NEGATIVE_PROMPT = (
    "lowres, bad anatomy, bad hands, text, error, missing finger, extra digits, "
    "fewer digits, cropped, worst quality, low quality, low score, bad score, "
    "average score, signature, watermark, username, blurry"
)

# 今回の試験で追加必須の概念(チャミ指定)。既存正本に無い語のみを追記する。
REQUIRED_ADDITIONAL_NEGATIVE_CONCEPTS = [
    "letters",
    "japanese characters",
    "speech bubble",
    "caption",
    "onomatopoeia",
    "manga panel border",
    "logo",
    "malformed hands",
    "extra fingers",
    "missing fingers",
    "wrong costume",
    "wrong accessories",
    "chinese-style clothing",
    "korean-style clothing",
    "romance",
]


class PilotError(Exception):
    """1コマ生成試験の準備・検証における失敗を表す。"""


def load_manga_schema():
    """news-game-translator側scripts/manga_schema.pyを正本としてimportする。

    Packetのenum・CHARACTER_REFERENCE_ID等をこちらへ重複実装しないための
    唯一の入口。`sys.path`+`import manga_schema`ではなく
    `importlib.util.spec_from_file_location`でファイルパスから直接読み込む
    (Codexレビュー指摘、Major: `sys.modules`はモジュール名でキャッシュ
    されるため、1プロセス内で`NEWS_GAME_TRANSLATOR_ROOT`を切り替えて
    再呼び出しした場合、2回目以降は古いrootで読み込んだモジュールが
    サイレントに返ってしまい、想定と異なるスキーマ〔または存在しない
    ファイル〕に対して検証したことに気づけない)。

    manga_schema.py自体のsys.path登録は行わない(2回目のCodexレビュー
    指摘、Major: 以前はmanga_schema.pyが同じscripts/内の他モジュールを
    importする可能性に備えてsys.pathへ追加していたが、その追加importは
    モジュール名ベースのsys.modulesキャッシュに乗るため、root切替後も
    古い依存モジュールがサイレントに使われ得た)。現在の正本
    manga_schema.pyは標準ライブラリ(re, unicodedata)しかimportしておらず、
    このsys.path登録は不要なため削除する。将来manga_schema.pyが同じ
    scripts/内の他モジュールをimportするようになった場合は、そちらも
    root毎に隔離されたモジュール名でimportlib経由で読み込む必要がある。
    """
    import importlib.util

    override = os.environ.get(NEWS_GAME_TRANSLATOR_ROOT_ENV_VAR)
    ngt_root = Path(override) if override else DEFAULT_NEWS_GAME_TRANSLATOR_ROOT
    ngt_scripts = ngt_root / "scripts"
    schema_path = ngt_scripts / "manga_schema.py"

    # 環境変数由来のパス値を例外メッセージへそのまま出さない
    # (Codexレビュー指摘、Minor)。overrideが未設定の場合はコード上固定の
    # デフォルトパスであり、値の漏えいにはあたらないためそのまま表示する。
    if override:
        path_display = f"(環境変数{NEWS_GAME_TRANSLATOR_ROOT_ENV_VAR}で指定されたパス、値は表示しません)"
    else:
        path_display = str(schema_path)

    if not schema_path.is_file():
        raise PilotError(
            f"news-game-translatorのscripts/manga_schema.pyが見つかりません: {path_display}"
            f"(環境変数{NEWS_GAME_TRANSLATOR_ROOT_ENV_VAR}でnews-game-translatorの"
            "ローカルチェックアウトパスを指定できます)"
        )

    spec = importlib.util.spec_from_file_location("one_panel_pilot._manga_schema", schema_path)
    if spec is None or spec.loader is None:
        raise PilotError(f"manga_schema.pyの読み込みに失敗しました: {path_display}")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as e:  # noqa: BLE001
        # overrideの場合は実行時例外の本文(__file__を含み得る)を
        # そのままPilotErrorへ埋め込まない(2回目のCodexレビュー指摘、
        # Minor: raise RuntimeError(__file__)のような実行時例外経由で
        # 環境変数由来のパス値が再露出していた)。
        if override:
            raise PilotError(
                f"manga_schema.pyの実行に失敗しました: {path_display}"
                "(詳細はデフォルトパス使用時のみ表示します)"
            ) from None
        raise PilotError(f"manga_schema.pyの実行に失敗しました: {path_display}({e})") from e

    return module


def load_resolve_reference_image():
    """このリポジトリのscripts/resolve_reference_image.pyをimportする。"""
    this_scripts = str(Path(__file__).resolve().parent)
    if this_scripts not in sys.path:
        sys.path.insert(0, this_scripts)
    import resolve_reference_image as rri  # noqa: E402

    return rri


def load_packet(packet_path):
    path = Path(packet_path)
    if not path.is_file():
        raise PilotError(f"Packetファイルが見つかりません: {path}")
    with path.open(encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            raise PilotError(f"PacketのJSONが不正です: {path}({e})") from e


# build_comfyui_workflow()が参照する必須キー。欠落時にbuild_comfyui_workflow
# 呼び出し時点で素のKeyErrorが送出されるのを防ぐため、load_config()の時点で
# まとめて検証する(Codexレビュー指摘、Minor)。
REQUIRED_CONFIG_KEYS = (
    "checkpoint_name",
    "clip_vision_name",
    "ipadapter_preset",
    "ipadapter_weight",
    "sampler_name",
    "scheduler",
    "steps",
    "cfg",
    "generation_width",
    "generation_height",
)


def load_config(config_path=None):
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    if not path.is_file():
        raise PilotError(f"設定ファイルが見つかりません: {path}")
    with path.open(encoding="utf-8") as f:
        try:
            raw_config = json.load(f)
        except json.JSONDecodeError as e:
            raise PilotError(f"設定ファイルのJSONが不正です: {path}({e})") from e
    if not isinstance(raw_config, dict):
        raise PilotError(f"設定ファイルのルートはオブジェクトである必要があります: {path}")

    config = {k: v for k, v in raw_config.items() if not k.startswith("_")}

    missing = [key for key in REQUIRED_CONFIG_KEYS if key not in config]
    if missing:
        raise PilotError(f"設定ファイルに必須キーが不足しています: {', '.join(missing)}({path})")

    return config


def load_five_panel_template():
    if not FIVE_PANEL_TEMPLATE_PATH.is_file():
        raise PilotError(f"five_panel_template.jsonが見つかりません: {FIVE_PANEL_TEMPLATE_PATH}")
    with FIVE_PANEL_TEMPLATE_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def get_panel_geometry(template, panel_no):
    for panel in template.get("panels", []):
        if panel.get("panel_no") == panel_no:
            return panel
    raise PilotError(f"five_panel_template.jsonにpanel_no={panel_no}が見つかりません")


# build_positive_prompt()の固定サフィックスはハルトの外見(髪型・衣装・
# 胸の桜チャーム等)を決め打ちで記述しており、他キャラクターへ一般化されて
# いない。関数群自体はキャラクター名を引数として受け取れる設計だが、
# 現時点でこのpilotが実際に正しく動作するのはハルトのみである
# (Codexレビュー指摘、Minor: --characterでハルト以外を指定しても
# scope検証は通り得るが、positive promptにハルトの外見記述が残ってしまい、
# IPAdapter参照画像とテキストconditioningのキャラクターが食い違う)。
SUPPORTED_TEST_CHARACTERS = ("ハルト",)


def validate_pilot_scope(packet, manga_schema_module, panel_no, expected_character):
    """Packet全体の構造検証(news-game-translator正本)に加え、今回の試験
    固有の制約(対象panel_noのperformersが`expected_character`1人だけ)を
    検証する。構造検証で不合格の場合は、試験固有の検証は行わず即座に返す
    (構造が壊れたPacketに対して試験固有チェックを重ねても無意味なため)。
    """
    reasons = list(manga_schema_module.validate_packet(packet))
    if reasons:
        return reasons

    panels = packet.get("panels")
    panel = None
    if isinstance(panels, list):
        for candidate in panels:
            if isinstance(candidate, dict) and candidate.get("panel_no") == panel_no:
                panel = candidate
                break
    if panel is None:
        return [f"panel_no={panel_no}が見つかりません"]

    performers = panel.get("performers")
    if not isinstance(performers, list) or len(performers) != 1:
        count = len(performers) if isinstance(performers, list) else "不明"
        return [
            f"panel_no={panel_no}のperformersは試験入力として1人限定である必要があります"
            f"(現在{count}人)"
        ]

    performer = performers[0]
    if not isinstance(performer, dict) or performer.get("name") != expected_character:
        actual = performer.get("name") if isinstance(performer, dict) else performer
        return [
            f"panel_no={panel_no}のperformerが{expected_character!r}ではありません: {actual!r}"
        ]

    return []


def get_panel(packet, panel_no):
    for panel in packet.get("panels", []):
        if isinstance(panel, dict) and panel.get("panel_no") == panel_no:
            return panel
    raise PilotError(f"panel_no={panel_no}が見つかりません")


# resolve_reference_image.pyはmanifest.jsonの値をそのまま実ファイル名として
# 使うため、manifest.json自体が誤って画像以外のファイル名を指していても
# 検出しない(Codexレビュー指摘、Minor)。ComfyUIのLoadImageへ渡す前提として、
# ここで許可拡張子を明示的に絞る(防御的多重化。manifest.jsonはリポジトリ
# 管理下だが、破損・誤記に対する追加の安全策として)。
ALLOWED_REFERENCE_IMAGE_SUFFIXES = (".png",)


def resolve_performer_reference_image(performer, resolve_module):
    """performerのreference_image(論理ID)を、既存resolve_reference_image.py
    を通じて実ファイルパスへ解決する。取得未実行の場合はScriptの案内文つき
    エラーをそのまま伝える(推測でファイルを補わない)。

    解決した実ファイルが通常ファイルであること(resolve_module側で確認済み)
    に加え、拡張子が許可された画像形式であることをここで追加確認する。
    """
    reference_image = performer.get("reference_image")
    try:
        path = resolve_module.resolve_reference_image(reference_image, require_file_exists=True)
    except resolve_module.ResolveError as e:
        raise PilotError(f"参照画像の解決に失敗しました: {e}") from e

    if not path.is_file():
        raise PilotError(f"解決した参照画像が通常ファイルではありません: {path}")
    if path.suffix.lower() not in ALLOWED_REFERENCE_IMAGE_SUFFIXES:
        raise PilotError(
            f"解決した参照画像の拡張子が許可されていません(許可: "
            f"{', '.join(ALLOWED_REFERENCE_IMAGE_SUFFIXES)}): {path}"
        )
    return path


# 実ピクセル処理を後日実装する際に用いるべきリサンプリング方式
# (Codexレビュー指摘、Major対応: compute_panel_fit()の出力が連続座標の
# 丸め値のみで、整数ラスターへ変換する規則が未定義だった。Pillowでの
# 実装を前提に、縮小時のリサンプリングフィルタ名をここで固定する)。
PANEL_FIT_RESAMPLING_METHOD = "LANCZOS"


def compute_panel_fit(generation_width, generation_height, target_width, target_height):
    """SDXL生成解像度(generation_width×generation_height)から、5コマ
    テンプレートの対象コマ内側(target_width×target_height、通常は
    five_panel_template.jsonのinner)へ収めるための、リサイズ後寸法と
    中央基準の縦クロップ範囲を計算する(実際のピクセル処理は行わない、
    寸法計算のみ)。

    方針: 生成画像を幅がtarget_widthに一致するよう等比縮小し、縮小後の
    高さがtarget_height以上であることを確認した上で、縦方向を中央基準で
    target_heightへクロップする。顔・手等の必須要素は、Packet側の
    framing(waist/bust等)により縦方向中央付近へ収まる構図を前提とする
    (本関数は寸法計算のみを担い、実際に必須要素が収まるかはプロンプト・
    構図側の責務)。

    生成後の高さがtarget_heightに届かない場合は、対象コマへ収まらない
    生成解像度の選択ミスとして明確にエラーにする(推測で引き伸ばさない)。

    戻り値には、連続座標の参考値(`resize_to`/`crop_box`/`crop_ratio`、
    小数第2位までの丸め表示)に加え、実際にピクセル処理を実装する際に
    一意な結果を再現するための整数ピクセル契約(`resize_to_px`/
    `crop_box_px`/`resampling_method`)を含める(Codexレビュー指摘、
    Major: 連続座標の丸め値だけでは、縮小後の高さを420pxにするか421pxに
    するか、余り1pxを上下どちらに配分するかが実装者・使用ライブラリ次第で
    ばらつき、「同じ変換仕様」という契約が成立しなかった)。

    整数ピクセル契約(4引数はいずれも正の整数〔bool不可〕に限定し、浮動
    小数点誤差を避けるため整数演算のみで計算する。2回目のCodexレビュー
    指摘、Major: 以前は4引数にfloatも許可していたため`resize_to_px`等へ
    floatが混入し、また`math.ceil(resized_height - 1e-9)`という浮動小数点
    経由の切り上げが極端に大きい入力で文書記載の式とずれる場合があった):
    - `resized_height_px = ceil(generation_height * target_width / generation_width)`
      を`(generation_height * target_width + generation_width - 1) //
      generation_width`という整数演算のみで計算する
      (縮小後の高さを切り上げ、target_heightを下回らないことを優先する)
    - `crop_total_px = resized_height_px - target_height`
    - `crop_top_px = crop_total_px // 2`(余り1pxは下側へ配分)
    - `crop_bottom_px = crop_total_px - crop_top_px`
    - `crop_box_px`は半開区間`(left, upper, right, lower)`(Pillowの
      `Image.crop()`と同じ規約)
    - リサンプリングフィルタは`PANEL_FIT_RESAMPLING_METHOD`(`LANCZOS`)固定
    """
    for name, value in (
        ("generation_width", generation_width),
        ("generation_height", generation_height),
        ("target_width", target_width),
        ("target_height", target_height),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise PilotError(f"{name}は正の整数である必要があります(bool不可): {value!r}")

    scale = target_width / generation_width
    resized_height = generation_height * scale

    if resized_height < target_height - 1e-6:
        raise PilotError(
            f"生成解像度{generation_width}x{generation_height}を幅{target_width}に"
            f"合わせて縮小すると高さが{resized_height:.2f}となり、対象コマの高さ"
            f"{target_height}に届きません(この生成解像度は対象コマへ収まりません。"
            "より横長寄りではない〔縦方向に余裕のある〕生成解像度を選択してください)"
        )

    crop_total = resized_height - target_height
    crop_top = crop_total / 2.0
    crop_ratio = crop_total / resized_height if resized_height > 0 else 0.0

    resized_height_px = (generation_height * target_width + generation_width - 1) // generation_width
    crop_total_px = resized_height_px - target_height
    crop_top_px = crop_total_px // 2
    crop_bottom_px = crop_total_px - crop_top_px

    return {
        "resize_to": {"width": target_width, "height": round(resized_height, 2)},
        "crop_box": {
            "left": 0,
            "upper": round(crop_top, 2),
            "right": target_width,
            "lower": round(crop_top + target_height, 2),
        },
        "crop_ratio": round(crop_ratio, 4),
        "final_size": {"width": target_width, "height": target_height},
        "resize_to_px": {"width": target_width, "height": resized_height_px},
        "crop_box_px": {
            "left": 0,
            "upper": crop_top_px,
            "right": target_width,
            "lower": crop_top_px + target_height,
        },
        "resampling_method": PANEL_FIT_RESAMPLING_METHOD,
    }


def _normalize(text):
    return unicodedata.normalize("NFKC", text or "").strip()


def build_negative_prompt(panel=None):
    """既存正本(BASE_NEGATIVE_PROMPT)を基礎に、今回必須の概念のうち
    まだ含まれていないものだけを追記する(重複追加しない)。

    panelを渡した場合、panel["negative_prompt"](Packet側のコマ固有の
    除外事項)も同様に重複排除しながら末尾へ追記する(Codexレビュー
    指摘、Minor: 以前はPacketのnegative_promptフィールドが完全に無視され、
    固定の基礎語彙・必須追加語だけがconditioningへ渡っていた)。
    """
    existing_terms = {term.strip().lower() for term in BASE_NEGATIVE_PROMPT.split(",")}
    additions = [
        concept
        for concept in REQUIRED_ADDITIONAL_NEGATIVE_CONCEPTS
        if concept.lower() not in existing_terms
    ]
    result = BASE_NEGATIVE_PROMPT
    if additions:
        result += ", " + ", ".join(additions)
        existing_terms |= {concept.lower() for concept in additions}

    if panel:
        panel_negative = panel.get("negative_prompt") or ""
        panel_terms = [term.strip() for term in panel_negative.split(",") if term.strip()]
        # 内包表記だとexisting_termsがイテレーション中に更新されず、
        # panel_terms自身の内部重複(大文字小文字違いを含む)を見逃す
        # (2回目のCodexレビュー指摘、Minor)。ループで都度更新しながら
        # 判定する。
        panel_additions = []
        for term in panel_terms:
            key = term.lower()
            if key in existing_terms:
                continue
            panel_additions.append(term)
            existing_terms.add(key)
        if panel_additions:
            result += ", " + ", ".join(panel_additions)

    return result


# Packetのenum値(manga_schema.pyが正本)から、英語positive prompt句への
# 決定論的マッピング(Codexレビュー指摘、Major対応: 以前はpanel/performerの
# framing・camera_angle・position・facing・gazeがpositive promptへ
# まったく反映されず、ドキュメント上の説明と実装が乖離していた)。
FRAMING_PROMPT_TERMS = {
    "close_up": "close-up shot",
    "bust": "bust shot",
    "waist": "waist-up shot",
    "full": "full body shot",
    "wide": "wide shot",
}
CAMERA_ANGLE_PROMPT_TERMS = {
    "eye_level": "eye-level angle",
    "high_angle": "high angle",
    "low_angle": "low angle",
    "over_shoulder": "over-the-shoulder angle",
    "top_down": "top-down angle",
}
POSITION_PROMPT_TERMS = {
    "left": "positioned on the left side of the frame",
    "center": "positioned in the center of the frame",
    "right": "positioned on the right side of the frame",
}
FACING_PROMPT_TERMS = {
    "face_left": "facing left",
    "face_right": "facing right",
    "front": "facing forward",
    "three_quarter_left": "three-quarter view facing left",
    "three_quarter_right": "three-quarter view facing right",
}
GAZE_PROMPT_TERMS = {
    "other_character": "looking at another character",
    "object": "looking at an object",
    "reader": "looking at the viewer",
    "down": "looking down",
    "off_panel_left": "looking off-panel to the left",
    "off_panel_right": "looking off-panel to the right",
}


def build_positive_prompt(panel, performer):
    """Packetのscene/background/framing/camera_angle/performer.expression等
    から、SDXL向け英語image_promptを組み立てる。Packet側に既にimage_prompt
    (英語)が用意されている場合はそれを基礎とし、panel.framing/camera_angle・
    performer.position/facing/gazeを既知enumから決定論的に英語句へ変換して
    追加した上で、キャラクター固定事項(衣装・髪型・胸の桜チャーム・黄緑系
    アウター、和風7:洋風3、恋愛要素なし、中国・韓国風意匠の回避)を明示する
    固定サフィックスを付加する。

    scene/backgroundの日本語生テキストはそのままSDXLへは渡さない(英語
    image_promptのみを場面記述の基礎とする)。framing等が未知の値や
    欠落の場合は、その項目のみ黙って省略する(構造検証自体は
    manga_schema_module.validate_packet()が別途担う)。
    """
    base = panel.get("image_prompt") or ""

    composition_terms = []
    framing_term = FRAMING_PROMPT_TERMS.get(panel.get("framing"))
    if framing_term:
        composition_terms.append(framing_term)
    camera_angle_term = CAMERA_ANGLE_PROMPT_TERMS.get(panel.get("camera_angle"))
    if camera_angle_term:
        composition_terms.append(camera_angle_term)
    position_term = POSITION_PROMPT_TERMS.get(performer.get("position"))
    if position_term:
        composition_terms.append(position_term)
    facing_term = FACING_PROMPT_TERMS.get(performer.get("facing"))
    if facing_term:
        composition_terms.append(facing_term)
    gaze_term = GAZE_PROMPT_TERMS.get(performer.get("gaze"))
    if gaze_term:
        composition_terms.append(gaze_term)

    fixed_suffix = (
        "young male adventurer named Haruto, short slightly tousled light brown hair, "
        "round dark brown eyes, simple leather-and-cloth novice adventurer gear, "
        "yellow-green sleeveless outer coat, small cherry blossom charm on the chest, "
        "japanese-inspired fantasy world with light western influence (roughly 7:3 japanese to western), "
        "no chinese-style clothing, no korean-style clothing, no romance elements, "
        "anime style, consistent character design"
    )

    parts = [part for part in [base, *composition_terms, fixed_suffix] if part]
    return ", ".join(parts)


def build_comfyui_workflow(panel, performer, reference_image_path, config, seed):
    """SDXL+IPAdapter用ComfyUI **API送信用**Workflow(class_type形式の
    ノードグラフ)を構築する。UI保存形式(nodes/links/groups等を持つ形式)
    とは異なる、/promptエンドポイントへ直接POSTできる形式。

    ノード名・既定パラメータは、既存profiles/sdxl/chibi/
    comfyui_sdxl_chibi.htmlが実際に使用している構成を踏襲する
    (CheckpointLoaderSimple→CLIPTextEncode×2→CLIPVisionLoader+LoadImage→
    IPAdapterUnifiedLoader→IPAdapterAdvanced→EmptyLatentImage→KSampler→
    VAEDecode→SaveImage)。モデル名・IPAdapterプリセット等はconfigから
    取得し、コード側で決め打ちしない。
    """
    positive_prompt = build_positive_prompt(panel, performer)
    negative_prompt = build_negative_prompt(panel)

    workflow = {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": config["checkpoint_name"]},
        },
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {"clip": ["1", 1], "text": positive_prompt},
        },
        "8": {
            "class_type": "CLIPTextEncode",
            "inputs": {"clip": ["1", 1], "text": negative_prompt},
        },
        "35": {
            "class_type": "CLIPVisionLoader",
            "inputs": {"clip_name": config["clip_vision_name"]},
        },
        "36": {
            "class_type": "LoadImage",
            # 実行時はComfyUIへ事前アップロード済みのファイル名を指定する
            # 必要がある(/upload/image)。dry-runでは、どのローカル正本
            # ファイルをアップロードすべきかが分かるよう、解決済みの実
            # パスのファイル名をそのまま入れる(実アップロードはしない)。
            "inputs": {"image": reference_image_path.name, "upload": "image"},
        },
        "30": {
            "class_type": "IPAdapterUnifiedLoader",
            "inputs": {
                "model": ["1", 0],
                "preset": config["ipadapter_preset"],
                "provider": "autocast",
            },
        },
        "31": {
            "class_type": "IPAdapterAdvanced",
            "inputs": {
                "model": ["30", 0],
                "ipadapter": ["30", 1],
                "image": ["36", 0],
                "clip_vision": ["35", 0],
                "weight": config["ipadapter_weight"],
                "weight_type": "linear",
                "combine_embeds": "concat",
                "start_at": 0.0,
                "end_at": 1.0,
                "embeds_scaling": "V only",
            },
        },
        "9": {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "width": config["generation_width"],
                "height": config["generation_height"],
                "batch_size": config.get("batch_size", 1),
            },
        },
        "10": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["31", 0],
                "positive": ["6", 0],
                "negative": ["8", 0],
                "latent_image": ["9", 0],
                "seed": seed,
                "control_after_generate": "fixed",
                "steps": config["steps"],
                "cfg": config["cfg"],
                "sampler_name": config["sampler_name"],
                "scheduler": config["scheduler"],
                "denoise": 1.0,
            },
        },
        "11": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["10", 0], "vae": ["1", 2]},
        },
        "12": {
            "class_type": "SaveImage",
            "inputs": {
                "images": ["11", 0],
                "filename_prefix": config.get("filename_prefix", "one_panel_pilot"),
            },
        },
    }
    return workflow, positive_prompt, negative_prompt


REQUIRED_WORKFLOW_NODE_IDS = ["1", "6", "8", "9", "10", "11", "12", "30", "31", "35", "36"]


def validate_workflow_shape(workflow):
    """Workflow(ノードグラフ)が最低限必要なノードを備えているかを検証する。
    実際にComfyUIへ送信して検証するわけではない(dry-runのため)。
    """
    reasons = []
    for node_id in REQUIRED_WORKFLOW_NODE_IDS:
        node = workflow.get(node_id)
        if not isinstance(node, dict) or "class_type" not in node or "inputs" not in node:
            reasons.append(f"Workflowノード{node_id!r}が不正または欠落しています")

    ksampler = workflow.get("10", {}).get("inputs", {})
    # 型チェックだけでは負数・0・NaN・Infinityを見逃す(Codexレビュー指摘、
    # Major: seed=-5/steps<=0/cfg<=0/cfg=nan/cfg=infがいずれも無検出で
    # 通過していた)。型・有限性・値域を合わせて検証する。
    for field, expected_type, allow_zero, minimum in (
        ("seed", int, True, 0),
        ("steps", int, False, 0),
        ("cfg", (int, float), False, 0),
    ):
        value = ksampler.get(field)
        if not isinstance(value, expected_type) or isinstance(value, bool):
            reasons.append(f"KSampler.{field}が数値として不正です: {value!r}")
            continue
        if isinstance(value, float) and not (
            value == value and value not in (float("inf"), float("-inf"))
        ):
            reasons.append(f"KSampler.{field}が有限の数値ではありません(NaN/Infinity不可): {value!r}")
            continue
        if allow_zero:
            if value < minimum:
                reasons.append(f"KSampler.{field}は{minimum}以上である必要があります: {value!r}")
        else:
            if value <= minimum:
                reasons.append(f"KSampler.{field}は{minimum}より大きい必要があります: {value!r}")

    latent_inputs = workflow.get("9", {}).get("inputs", {})
    for field in ("width", "height", "batch_size"):
        value = latent_inputs.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            reasons.append(f"EmptyLatentImage.{field}が正の整数として不正です: {value!r}")

    if latent_inputs.get("batch_size") != 1:
        reasons.append(
            f"生成枚数(batch_size)は初期値1である必要があります: {latent_inputs.get('batch_size')!r}"
        )

    negative_text = workflow.get("8", {}).get("inputs", {}).get("text", "")
    normalized_negative = _normalize(negative_text).lower()
    for required_term in ("text", "speech bubble", "manga panel border", "japanese characters"):
        if required_term not in normalized_negative:
            reasons.append(f"negative promptに必須概念{required_term!r}が含まれていません")

    return reasons


def check_runpod_env_vars():
    """RunPod接続に必要な環境変数の**存在確認のみ**を行う(値は一切読まず
    出力しない)。実際の接続・送信はこのモジュールでは行わない。
    """
    return {name: (name in os.environ) for name in RUNPOD_ENV_VARS}


def build_runpod_request_dry_run(workflow, config):
    """RunPodへ送信予定のリクエストJSON(dry-run用、実送信しない)を組み立てる。

    実際の送信時にAuthorizationヘッダーへ設定するAPIキーの値は、この関数の
    戻り値には一切含めない(環境変数からその場で読み、送信直前にのみ付与する
    設計。dry-run結果はディスク保存・ログ出力されうるため、秘密情報を
    含めない)。
    """
    client_id = "one-panel-pilot-dry-run"
    return {
        "prompt": workflow,
        "client_id": client_id,
        "_note": (
            "これはdry-run用の構造確認結果であり、実際にRunPod/ComfyUIへ"
            "送信されたものではない。実送信時は、環境変数"
            f"{RUNPOD_ENV_VARS[1]!r}のURLへPOSTし、Authorizationヘッダーへ"
            f"環境変数{RUNPOD_ENV_VARS[0]!r}の値をその場で設定する"
            "(この構造には含めない)"
        ),
    }


def _contains_secret_like_value(obj, env_var_names):
    """dry-run生成物に、環境変数由来の秘密情報の値が紛れ込んでいないかを
    確認する(値そのものはテスト側でos.environにセットしたダミー値を使い、
    その文字列がJSON化した結果へ現れないことを確認する用途)。
    """
    serialized = json.dumps(obj, ensure_ascii=False)
    for name in env_var_names:
        value = os.environ.get(name)
        if value and value in serialized:
            return True
    return False


def run_dry_run(packet_path, panel_no=1, config_path=None, expected_character="ハルト", seed=None):
    """Packet読み込みから、Workflow構築・RunPod向けdry-runリクエスト生成・
    5コマテンプレートへの寸法適合計算までを、実送信・実生成なしで一括実行し、
    結果をまとめたdictを返す。失敗時はPilotErrorを送出する。
    """
    if expected_character not in SUPPORTED_TEST_CHARACTERS:
        raise PilotError(
            f"このpilotが現時点で正しく動作するキャラクターは"
            f"{', '.join(SUPPORTED_TEST_CHARACTERS)}のみです: {expected_character!r}"
            "(build_positive_prompt()の固定サフィックスがハルトの外見を"
            "決め打ちしているため、他キャラクターを指定してもIPAdapter参照"
            "画像とテキストconditioningのキャラクターが食い違います)"
        )

    manga_schema_module = load_manga_schema()
    resolve_module = load_resolve_reference_image()

    packet = load_packet(packet_path)

    scope_reasons = validate_pilot_scope(packet, manga_schema_module, panel_no, expected_character)
    if scope_reasons:
        raise PilotError("; ".join(scope_reasons))

    panel = get_panel(packet, panel_no)
    performer = panel["performers"][0]

    reference_image_path = resolve_performer_reference_image(performer, resolve_module)

    config = load_config(config_path)
    resolved_seed = config.get("seed", 0) if seed is None else seed

    workflow, positive_prompt, negative_prompt = build_comfyui_workflow(
        panel, performer, reference_image_path, config, resolved_seed
    )
    workflow_reasons = validate_workflow_shape(workflow)
    if workflow_reasons:
        raise PilotError("; ".join(workflow_reasons))

    template = load_five_panel_template()
    geometry = get_panel_geometry(template, panel_no)
    fit = compute_panel_fit(
        config["generation_width"],
        config["generation_height"],
        geometry["inner"]["width"],
        geometry["inner"]["height"],
    )

    runpod_request = build_runpod_request_dry_run(workflow, config)
    env_var_status = check_runpod_env_vars()

    return {
        "packet_path": str(packet_path),
        "panel_no": panel_no,
        "performer_name": performer["name"],
        "performer_expression": performer["expression"],
        "reference_image_path": str(reference_image_path),
        "positive_prompt": positive_prompt,
        "negative_prompt": negative_prompt,
        "workflow": workflow,
        "panel_geometry": geometry,
        "panel_fit": fit,
        "runpod_request_dry_run": runpod_request,
        "runpod_env_vars_present": env_var_status,
        "generation_resolution": {
            "width": config["generation_width"],
            "height": config["generation_height"],
        },
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("packet", help="Manga News Packet v2 JSONファイルのパス")
    parser.add_argument("--panel-no", type=int, default=1, help="対象panel_no(既定: 1)")
    parser.add_argument(
        "--character",
        default="ハルト",
        help="試験対象キャラクター(既定・現時点で唯一対応: ハルト。"
        "positive promptの固定サフィックスがハルト専用のため他キャラクターは未対応)",
    )
    parser.add_argument("--config", default=None, help="config.jsonのパス(省略時はconfig.example.json)")
    parser.add_argument("--seed", type=int, default=None, help="固定するseed(省略時はconfigのseedを使用)")
    args = parser.parse_args()

    try:
        result = run_dry_run(
            args.packet,
            panel_no=args.panel_no,
            config_path=args.config,
            expected_character=args.character,
            seed=args.seed,
        )
    except PilotError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)

    printable = copy.deepcopy(result)
    print(json.dumps(printable, ensure_ascii=False, indent=2))
    print(
        f"\n[OK] dry-run成功: panel_no={result['panel_no']}, "
        f"performer={result['performer_name']}, "
        f"reference_image={result['reference_image_path']}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
