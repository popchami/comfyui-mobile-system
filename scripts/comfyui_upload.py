#!/usr/bin/env python3
"""ComfyUIの`/upload/image`エンドポイントへ、正本参照画像PNGを安全に
アップロードするためのリクエスト構築・応答検証を提供する。

このモジュールをimportまたはテスト実行しても、RunPod・ComfyUIへの実通信は
一切発生しない。`send_upload_request()`という実送信用の関数は存在するが、
このリポジトリの現時点のコード・テストのどこからも呼び出していない
(テストでは`requests.post`自体をmockして、リクエスト構築・応答検証の
ロジックのみを検証する)。

RunPod方式についての注意(scripts/one_panel_pilot.py・ONE_PANEL_PILOT.md
と同じ理解): このリポジトリの既存実装
(profiles/sdxl/chibi/comfyui_sdxl_chibi.html等のブラウザUI)は、RunPodの
Serverless API(`https://api.runpod.ai/v2/{endpoint_id}/run(sync)`)ではなく、
RunPod Pod上で直接動くComfyUIサーバーへHTTPアクセスする方式
(Podのプロキシ経由URL、例: `https://xxxxx-8188.proxy.runpod.net`)を前提に
設計されている。本モジュールの`base_url`も同様に、ComfyUIサーバーそのものへ
到達するURLを想定する。ただしこれは既存コード・文書からの読み取りであり、
実際にRunPod Serverless API経由での接続が必要になる可能性を排除するもの
ではない(未確定事項として文書化する。ONE_PANEL_PILOT.md参照)。

標準ライブラリ+requests(このリポジトリでscripts/runpod_status_check.pyが
既に使用している既存依存)のみを使用する。Pillowはこのモジュールでは
使用しない(画像の実ピクセル処理はscripts/panel_pixel_convert.py側の責務)。
"""
import hashlib
import json
import os
import re
import stat
import sys
from pathlib import Path

import requests

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from reference_image_categories import CATEGORY_MANIFEST_REL, CATEGORY_PLACE_TO  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


class ComfyUIUploadError(Exception):
    """アップロードのリクエスト構築・応答検証における失敗を表す。"""


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
ALLOWED_UPLOAD_SUFFIXES = (".png",)

# 既存の正本PNG(profiles/sdxl/isekai_nihon_manga/reference_images/配下)の
# 実測最大サイズは約2.28MB(akira/equipment配下のtalisman系画像)。
# ハルトの表情PNG(1254x1254)をRGBA非圧縮換算しても約6.0MB程度。
# 将来のキャラクター追加・解像度変更にも耐えるよう、実測最大値の約7倍・
# 非圧縮換算の約2.6倍にあたる16MBを上限とする(無制限のアップロードを
# 許可しないための、実測値に基づく具体的根拠のある値)。
MAX_UPLOAD_FILE_SIZE_BYTES = 16 * 1024 * 1024

# `/upload/image`のJSON応答(name/subfolder/typeのみを含む小さなメタデータ)
# の受信サイズ上限(2回目のCodexレビュー指摘、Major対応: 以前は
# `response.json()`を直接呼んでおり、サイズ上限もContent-Type検証もなく
# 応答全体を無条件にメモリへ読み込んでいた)。
MAX_UPLOAD_RESPONSE_BYTES = 1 * 1024 * 1024  # 1MB

DEFAULT_UPLOAD_TIMEOUT_SECONDS = 30
# timeoutの上限(Codexレビュー指摘、Major対応: 以前は有限であることのみ
# 検証しており、巨大値〔例: 10**9秒〕を拒否できていなかった)。
MAX_UPLOAD_TIMEOUT_SECONDS = 120.0
DEFAULT_UPLOAD_IMAGE_TYPE = "input"
# ComfyUI本体が実際に使うフォルダ種別(input/temp/output)。これ以外の値は
# 応答・リクエストのどちらでも許可しない。
ALLOWED_UPLOAD_IMAGE_TYPES = ("input", "temp", "output")

_CONTROL_CHAR_RE = re.compile(r"[\x00-\x1f\x7f]")
# ComfyUI本体のLoadImage実装が末尾注釈として予約しているパターン。
_RESERVED_ANNOTATION_RE = re.compile(r"\s\[(?:input|temp|output)\]$")


def _is_within_root(path, root):
    try:
        resolved = path.resolve()
        resolved_root = Path(root).resolve()
    except OSError as e:
        raise ComfyUIUploadError(f"パスの解決に失敗しました: {path}({e})") from e
    return resolved == resolved_root or resolved_root in resolved.parents


# reference_image_categories.CATEGORY_PLACE_TO(正本)から、既知のカテゴリが
# 実際に配置される相対ディレクトリ構造の一覧を作る。
_KNOWN_PLACE_TO_PARTS = {category: Path(place_to).parts for category, place_to in CATEGORY_PLACE_TO.items()}


def _is_registered_in_manifest(path, root):
    """pathが、`<正本root>/<character>/<既知categoryのplace_to>/<filename>`
    という既知の構造に一致し、かつそのcharacter/categoryのmanifest.jsonに
    実際に登録されたファイルであることを確認する。

    2回目のCodexレビュー指摘、Major対応: 以前はディレクトリ構造の一致
    だけを確認しており、既知のcharacter/categoryディレクトリ内に直接
    置かれた「manifestに登録されていない」ファイル(resolverを一切通して
    いないファイル)を見逃していた。resolve_reference_image.py側の
    論理ID解析・トラバーサル対策そのものは重複実装せず、
    「manifest.jsonの値としてこのファイル名が登録されているか」という
    読み取り専用の突き合わせのみを行う。
    """
    root = Path(root).resolve()
    try:
        relative = path.resolve().relative_to(root)
    except ValueError:
        return False
    parts = relative.parts
    if len(parts) < 2:
        return False
    character = parts[0]
    filename = parts[-1]

    for category, place_to_parts in _KNOWN_PLACE_TO_PARTS.items():
        if len(parts) != 1 + len(place_to_parts) + 1:
            continue
        if parts[1 : 1 + len(place_to_parts)] != place_to_parts:
            continue

        manifest_path = root / character / CATEGORY_MANIFEST_REL[category]
        if not manifest_path.is_file():
            continue
        try:
            with manifest_path.open(encoding="utf-8") as f:
                manifest = json.load(f)
        except (OSError, ValueError):
            continue
        if not isinstance(manifest, dict):
            continue

        for key, entry in manifest.items():
            if isinstance(key, str) and key.startswith("_"):
                continue
            entry_filename = entry.get("file") if isinstance(entry, dict) else entry
            if entry_filename == filename:
                return True

    return False


def validate_upload_source_path(path, resolve_module):
    """アップロード対象PNGのパスを検証する。

    既存のresolve_performer_reference_image()が返した検証済みPathを渡す
    前提だが、basenameだけを信用せず、アップロード境界としてここで独自に
    再検証する(defense in depth):

    - Pathオブジェクトであること(生のbasename文字列を直接渡さない)
    - シンボリックリンクでないこと
    - 通常ファイルとして存在すること
    - 拡張子が`.png`であること
    - 正本ディレクトリ(resolve_module.REFERENCE_IMAGES_ROOT)の中に
      収まっていること
    - ファイルサイズが上限以下であること
    - PNGシグネチャ(先頭8バイト)が一致すること

    検証したファイルサイズ(バイト数)を返す。
    """
    if not isinstance(path, Path):
        raise ComfyUIUploadError(
            f"pathはPathオブジェクトである必要があります(basename文字列を直接渡さない): {path!r}"
        )
    if path.is_symlink():
        raise ComfyUIUploadError(f"シンボリックリンクはアップロード対象として許可されません: {path}")
    if not path.is_file():
        raise ComfyUIUploadError(f"アップロード対象のファイルが見つかりません: {path}")
    if path.suffix.lower() not in ALLOWED_UPLOAD_SUFFIXES:
        raise ComfyUIUploadError(
            f"アップロード対象の拡張子が許可されていません(許可: "
            f"{', '.join(ALLOWED_UPLOAD_SUFFIXES)}): {path}"
        )
    if not _is_within_root(path, resolve_module.REFERENCE_IMAGES_ROOT):
        raise ComfyUIUploadError(f"アップロード対象が正本ディレクトリの外を指しています: {path}")
    if not _is_registered_in_manifest(path, resolve_module.REFERENCE_IMAGES_ROOT):
        raise ComfyUIUploadError(
            f"アップロード対象がmanifest.jsonに登録された正本参照画像として"
            f"確認できません(resolverを通さず配置された可能性): {path}"
        )

    size = path.stat().st_size
    if size <= 0:
        raise ComfyUIUploadError(f"アップロード対象のファイルサイズが0バイトです: {path}")
    if size > MAX_UPLOAD_FILE_SIZE_BYTES:
        raise ComfyUIUploadError(
            f"アップロード対象のファイルサイズが上限({MAX_UPLOAD_FILE_SIZE_BYTES}バイト)を"
            f"超えています: {path}({size}バイト)"
        )

    with path.open("rb") as f:
        header = f.read(len(PNG_SIGNATURE))
    if header != PNG_SIGNATURE:
        raise ComfyUIUploadError(f"PNGシグネチャが一致しません(画像以外の可能性): {path}")

    return size


def _default_session():
    """session省略時に使う内部Session。

    requestsモジュールのグローバルなtrust_env(HTTP_PROXY/HTTPS_PROXY/
    NO_PROXY環境変数や~/.netrcの自動読み込み)を無効化し、呼び出し元が
    意図しないproxy・認証設定を継承しないようにする(Codexレビュー指摘、
    Major対応)。呼び出し元が独自のsessionを渡した場合、そのsessionの
    trust_env・proxy設定は呼び出し元自身の責任とする。
    """
    session = requests.Session()
    session.trust_env = False
    return session


def _validate_image_type(image_type):
    if image_type not in ALLOWED_UPLOAD_IMAGE_TYPES:
        raise ComfyUIUploadError(
            f"未対応のtypeです(許可: {', '.join(ALLOWED_UPLOAD_IMAGE_TYPES)}): {image_type!r}"
        )


def _validate_timeout(timeout):
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)):
        raise ComfyUIUploadError(f"timeoutは数値である必要があります(bool不可): {timeout!r}")
    if timeout != timeout or timeout in (float("inf"), float("-inf")):
        raise ComfyUIUploadError(f"timeoutは有限の数値である必要があります: {timeout!r}")
    if timeout <= 0:
        raise ComfyUIUploadError(f"timeoutは正の数値である必要があります: {timeout!r}")
    if timeout > MAX_UPLOAD_TIMEOUT_SECONDS:
        raise ComfyUIUploadError(
            f"timeoutが上限({MAX_UPLOAD_TIMEOUT_SECONDS}秒)を超えています: {timeout!r}"
        )


def _build_upload_filename_from_content(content, stem, suffix):
    digest = hashlib.sha256(content).hexdigest()[:12]
    return f"{stem}_{digest}{suffix}"


def build_upload_filename(path):
    """同名画像衝突を避けるための決定論的なアップロード先ファイル名を作る。

    元ファイル内容のSHA-256先頭12桁を末尾に付与する(同一内容なら常に
    同一名になり、内容が異なれば別名になる。乱数を使わないため再現可能で
    テストしやすい)。

    dry-run(build_upload_request())専用。実送信(send_upload_request())は
    検証・ハッシュ計算・送信を同一の読み取り結果から行うため、この関数を
    使わない(下記_read_and_verify_source_bytes()参照)。
    """
    return _build_upload_filename_from_content(path.read_bytes(), path.stem, path.suffix.lower())


def _read_and_verify_source_bytes(path, resolve_module):
    """アップロード対象PNGを1回だけ読み込み、検証(パス構造・シンボリック
    リンク拒否・正本ディレクトリ内であること・既知category構造・サイズ
    上限・PNGシグネチャ)と、実際に送信するバイト列の取得を、同一の
    ファイルディスクリプタ経由で行う。

    Codexレビュー指摘(Major)対応: 以前はパス検証・ハッシュ計算・送信で
    それぞれ別々にファイルをopenしており、検証後から送信までの間に
    ファイルが差し替えられても検出できないTOCTOU(time-of-check to
    time-of-use)の窓があった。`os.O_NOFOLLOW`によりシンボリックリンクへの
    open自体をアトミックに拒否し、以降はすべて同じバイト列を参照する。
    """
    if not isinstance(path, Path):
        raise ComfyUIUploadError(
            f"pathはPathオブジェクトである必要があります(basename文字列を直接渡さない): {path!r}"
        )
    if path.suffix.lower() not in ALLOWED_UPLOAD_SUFFIXES:
        raise ComfyUIUploadError(
            f"アップロード対象の拡張子が許可されていません(許可: "
            f"{', '.join(ALLOWED_UPLOAD_SUFFIXES)}): {path}"
        )
    if not _is_within_root(path, resolve_module.REFERENCE_IMAGES_ROOT):
        raise ComfyUIUploadError(f"アップロード対象が正本ディレクトリの外を指しています: {path}")
    if not _is_registered_in_manifest(path, resolve_module.REFERENCE_IMAGES_ROOT):
        raise ComfyUIUploadError(
            f"アップロード対象がmanifest.jsonに登録された正本参照画像として"
            f"確認できません(resolverを通さず配置された可能性): {path}"
        )

    nofollow_flag = getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(str(path), os.O_RDONLY | nofollow_flag)
    except OSError:
        raise ComfyUIUploadError(
            f"アップロード対象のファイルを開けません(シンボリックリンクまたは存在しない可能性): {path}"
        ) from None

    try:
        # O_NOFOLLOWは最終pathコンポーネントのシンボリックリンクは防ぐが、
        # 検証からopenまでの間に中間ディレクトリ自体がシンボリックリンクへ
        # 差し替えられるレースまでは防がない(2回目のCodexレビュー指摘、
        # Major対応)。Linux限定で、実際にopenされた実体の経路を
        # /proc/self/fd経由で読み直し、依然として正本root配下にあることを
        # openの直後という可能な限り小さい時間窓で再確認する
        # (/procが利用できない環境ではこの追加チェックのみ静かにスキップ
        # する。その場合でもO_NOFOLLOWによる最終コンポーネント保護は有効)。
        try:
            real_fd_path = Path(os.readlink(f"/proc/self/fd/{fd}"))
        except OSError:
            real_fd_path = None
        if real_fd_path is not None and not _is_within_root(
            real_fd_path, resolve_module.REFERENCE_IMAGES_ROOT
        ):
            raise ComfyUIUploadError(
                f"アップロード対象の実体が正本ディレクトリの外を指しています: {path}"
            )

        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode):
            raise ComfyUIUploadError(f"アップロード対象が通常ファイルではありません: {path}")
        if st.st_size <= 0:
            raise ComfyUIUploadError(f"アップロード対象のファイルサイズが0バイトです: {path}")
        if st.st_size > MAX_UPLOAD_FILE_SIZE_BYTES:
            raise ComfyUIUploadError(
                f"アップロード対象のファイルサイズが上限({MAX_UPLOAD_FILE_SIZE_BYTES}バイト)を"
                f"超えています: {path}({st.st_size}バイト)"
            )
        with os.fdopen(fd, "rb") as f:
            fd = None  # fdopen()がfdの所有権を引き継いだ(二重closeを避ける)
            content = f.read()
    finally:
        if fd is not None:
            os.close(fd)

    if content[: len(PNG_SIGNATURE)] != PNG_SIGNATURE:
        raise ComfyUIUploadError(f"PNGシグネチャが一致しません(画像以外の可能性): {path}")

    return content


def build_upload_request(path, resolve_module, overwrite=False, image_type=DEFAULT_UPLOAD_IMAGE_TYPE):
    """実際には送信せず、`/upload/image`へ送るリクエストの内容を構築する
    (dry-run)。ファイルハンドルは含めず、JSONシリアライズ可能な内容のみ
    返す(実送信時にはsend_upload_request()が改めてファイルを開く)。

    overwriteは既定でFalse(ComfyUI側で既存の同名ファイルをサイレントに
    上書きしない)。同名衝突自体はbuild_upload_filename()の内容ハッシュ
    命名で避ける設計とし、overwriteはそれでも衝突した場合の明示的な
    意思表示として扱う。
    """
    _validate_image_type(image_type)

    size = validate_upload_source_path(path, resolve_module)
    filename = build_upload_filename(path)

    return {
        "endpoint_path": "/upload/image",
        "method": "POST",
        "source_path": str(path),
        "upload_filename": filename,
        "content_length": size,
        "content_type": "image/png",
        "form_fields": {
            "type": image_type,
            "overwrite": "true" if overwrite else "false",
        },
        "_note": (
            "この辞書は実送信を行わない(dry-run)。実送信にはsend_upload_request()を"
            "使用する。base_url・APIキー等の実値はこの辞書のどこにも含めない。"
        ),
    }


def _validate_server_path_component(label, value, allow_empty, allow_nested):
    """`allow_nested=False`の場合、単一segment(basename相当)以外を一切
    拒否する(`/`・`\\`を1文字でも含めば拒否)。`allow_nested=True`
    (subfolder用)の場合のみ、複数segmentへの分割・各segment検証を行う
    (Codexレビュー指摘、Minor対応: 以前は`name`もsegment単位でしか検証して
    おらず、`nested/a.png`のような複数segmentのnameを誤って受理していた)。
    """
    if not isinstance(value, str):
        raise ComfyUIUploadError(f"応答の{label}が文字列ではありません: {value!r}")
    if not value:
        if allow_empty:
            return
        raise ComfyUIUploadError(f"応答の{label}が空です")
    if _CONTROL_CHAR_RE.search(value):
        raise ComfyUIUploadError(f"応答の{label}に制御文字が含まれています: {value!r}")
    # ComfyUI本体が予約する末尾注釈(` [input]`/` [temp]`/` [output]`)を
    # name/subfolderの値自体に含めることを拒否する(2回目のCodexレビュー
    # 指摘、Major対応: 検証済みのtypeとは無関係に、応答のnameへ
    # `normal.png [output]`のような値を仕込むことで、type="input"のまま
    # 実際にはoutputフォルダをLoadImageへ参照させられてしまっていた)。
    if _RESERVED_ANNOTATION_RE.search(value):
        raise ComfyUIUploadError(
            f"応答の{label}にComfyUI予約の末尾注釈([input]/[temp]/[output])が"
            f"含まれています: {value!r}"
        )
    if value.startswith("/") or value.startswith("\\"):
        raise ComfyUIUploadError(f"応答の{label}が絶対パス形式です: {value!r}")
    if re.match(r"^[A-Za-z]:[\\/]", value):
        raise ComfyUIUploadError(f"応答の{label}がドライブレター付き絶対パスです: {value!r}")

    if not allow_nested:
        if "/" in value or "\\" in value:
            raise ComfyUIUploadError(f"応答の{label}にパス区切りが含まれています: {value!r}")
        if value in (".", ".."):
            raise ComfyUIUploadError(f"応答の{label}に不正な値が含まれています: {value!r}")
        return

    # subfolderの区切りは`/`のみ許可する(Codexレビュー指摘、Minor対応:
    # 以前は`\`も区切りとして分割・許容していたため、Windows風・混在区切り
    # (例: `sub\dir`)がそのまま`subfolder/name`形式へ混入し、`name`側の
    # 「バックスラッシュを1文字でも含めば拒否」という方針と一致していなかった)。
    if "\\" in value:
        raise ComfyUIUploadError(f"応答の{label}にバックスラッシュは使用できません: {value!r}")
    for segment in value.split("/"):
        if segment in ("", ".", ".."):
            raise ComfyUIUploadError(f"応答の{label}に不正なパス要素が含まれています: {value!r}")


def validate_upload_response(response_json):
    """ComfyUIの`/upload/image`応答(name/subfolder/type)を検証し、
    LoadImageへ渡してよい正規化済みの値(dict)を返す。

    nameは単一のファイル名(basename相当)のみを許可し、パス区切りを
    1文字でも含めば拒否する。subfolderのみ複数segmentを許可した上で、
    絶対パス・`..`・制御文字を拒否する。typeはComfyUIが実際に使う
    input/temp/outputのいずれかのみ許可する。

    既に検証済みの応答(このモジュール自身が返した辞書)を再度渡しても
    安全なよう、べき等に検証する(build_load_image_value()・
    apply_uploaded_image_to_workflow()が内部で再度呼び出す)。
    """
    if not isinstance(response_json, dict):
        raise ComfyUIUploadError(f"応答がオブジェクトではありません: {response_json!r}")

    name = response_json.get("name")
    subfolder = response_json.get("subfolder", "")
    image_type = response_json.get("type")

    _validate_server_path_component("name", name, allow_empty=False, allow_nested=False)
    _validate_server_path_component("subfolder", subfolder, allow_empty=True, allow_nested=True)
    _validate_image_type(image_type)

    return {"name": name, "subfolder": subfolder, "type": image_type}


def build_load_image_value(validated_response):
    """検証済みのアップロード応答から、WorkflowのLoadImage.imageへ設定する
    べき値を組み立てる(ComfyUI本体の実仕様通り、subfolderが空でなければ
    `subfolder/name`形式にする)。

    引数名に反して、呼び出し側が実際にはvalidate_upload_response()を
    通していない辞書を渡す可能性を排除するため、ここで改めて
    validate_upload_response()を通す(Codexレビュー指摘、Major対応:
    以前は関数名・引数名だけが検証済みであることを前提にしており、
    未検証の応答(`../escape.png`等)を直接渡すとそのままWorkflowへ
    反映されてしまっていた)。

    typeが`temp`/`output`の場合、ComfyUI本体のLoadImage実装
    (`folder_paths.annotated_filepath()`)は末尾に` [temp]`/` [output]`
    という注釈がなければ既定の`input`フォルダへフォールバックしてしまう
    (2回目のCodexレビュー指摘、Major対応: 以前はtypeを無視していたため、
    `image_type="temp"`/`"output"`でアップロードしても、LoadImageは
    誤って`input`フォルダから同名ファイルを探してしまっていた)。
    `type="input"`(既定)の場合は注釈を付けない(既存のComfyUI Workflow
    が期待する素の`name`/`subfolder/name`形式のまま)。
    """
    validated_response = validate_upload_response(validated_response)
    name = validated_response["name"]
    subfolder = validated_response.get("subfolder") or ""
    image_type = validated_response["type"]

    value = f"{subfolder}/{name}" if subfolder else name
    if image_type != "input":
        value = f"{value} [{image_type}]"
    return value


def apply_uploaded_image_to_workflow(workflow, validated_response, load_image_node_id="36"):
    """検証済みのアップロード応答を、WorkflowのLoadImageノードへ反映した
    新しいworkflow(コピー)を返す。呼び出し側の元workflowは変更しない。

    workflow/node/inputsの構造を明示的に検証してから書き換える
    (Codexレビュー指摘、Major対応: 以前は`inputs`がdictでない場合等に
    素の`TypeError`が漏れていた)。
    """
    import copy

    if not isinstance(workflow, dict):
        raise ComfyUIUploadError(f"workflowはdictである必要があります: {type(workflow).__name__}")

    node = workflow.get(load_image_node_id)
    if not isinstance(node, dict):
        raise ComfyUIUploadError(f"Workflowにnode_id={load_image_node_id!r}のLoadImageノードがありません")
    if node.get("class_type") != "LoadImage":
        raise ComfyUIUploadError(
            f"node_id={load_image_node_id!r}のclass_typeがLoadImageではありません: "
            f"{node.get('class_type')!r}"
        )
    inputs = node.get("inputs")
    if not isinstance(inputs, dict):
        raise ComfyUIUploadError(f"node_id={load_image_node_id!r}のinputsがdictではありません")
    if "image" not in inputs:
        raise ComfyUIUploadError(f"node_id={load_image_node_id!r}のinputsにimageフィールドがありません")

    # build_load_image_value()内部でvalidate_upload_response()を通すため、
    # ここでは重ねて呼び出さない(べき等な検証を1回で済ませる)。
    load_image_value = build_load_image_value(validated_response)

    updated = copy.deepcopy(workflow)
    updated[load_image_node_id]["inputs"]["image"] = load_image_value
    return updated


def send_upload_request(
    base_url,
    path,
    resolve_module,
    overwrite=False,
    image_type=DEFAULT_UPLOAD_IMAGE_TYPE,
    timeout=DEFAULT_UPLOAD_TIMEOUT_SECONDS,
    session=None,
):
    """実際に`/upload/image`へPOSTする。

    このリポジトリの現時点のコード・テストのどこからも呼び出していない
    (実接続の準備〔ONE_PANEL_PILOT.md記載のチェックリスト〕が整った後にのみ
    使用する想定)。テストでは`session`(またはrequestsモジュール自体)を
    mockし、実ソケット通信なしにこの関数の構築・解析ロジックのみを検証する。

    sessionを渡すことで、実接続時にrequests.Session()を再利用できる
    (毎回新規TCP接続を張らないHTTPクライアント境界)。省略時はrequests
    モジュール自体を使う(1回限りの接続に相当)。

    retryは行わない(1回のリクエストのみ。無制限の自動リトライはしない。
    再試行が必要な場合は呼び出し側が明示的に実装すること)。

    APIキー・接続先URLの実値は、例外メッセージ・戻り値のいずれにも含めない
    (2回目のCodexレビュー指摘、Critical対応: 以前は`raise ... from e`で
    元のrequests例外を`__cause__`として連鎖させていたため、`str(exception)`
    自体は安全でも、`repr()`やtraceback出力〔`logger.exception()`等〕経由で
    接続先URL等が漏れ得た。`from None`で連鎖自体を断つ)。
    """
    _validate_image_type(image_type)
    _validate_timeout(timeout)

    content = _read_and_verify_source_bytes(path, resolve_module)
    filename = _build_upload_filename_from_content(content, path.stem, path.suffix.lower())
    url = f"{base_url.rstrip('/')}/upload/image"
    http = session or _default_session()

    try:
        response = http.post(
            url,
            files={"image": (filename, content, "image/png")},
            data={"type": image_type, "overwrite": "true" if overwrite else "false"},
            timeout=timeout,
            allow_redirects=False,
            stream=True,
        )
    except requests.exceptions.Timeout:
        raise ComfyUIUploadError("アップロードリクエストがタイムアウトしました") from None
    except requests.exceptions.RequestException:
        raise ComfyUIUploadError(
            "アップロードリクエストが失敗しました(接続先・認証情報の詳細はここには含めません)"
        ) from None

    # 2回目のCodexレビュー指摘、Major対応: uploadだけredirectに追従して
    # いたため、他の境界(submit_prompt/poll_history/download_generated_image)
    # と同様にすべてのredirect応答を一律拒否する。
    if 300 <= response.status_code < 400:
        raise ComfyUIUploadError(
            f"予期しないredirect応答です(HTTP {response.status_code}、リダイレクト先は追従しません)"
        )
    if response.status_code != 200:
        raise ComfyUIUploadError(f"アップロードが失敗しました(HTTP {response.status_code})")

    content_type = (response.headers.get("Content-Type") or "").split(";")[0].strip().lower()
    if content_type != "application/json":
        raise ComfyUIUploadError("アップロード応答のContent-Typeが許可されていません")

    body_chunks = []
    total = 0
    try:
        # `stream=True`化後、応答本文の読み込み中にもrequestsの例外が
        # 送出され得る(3回目のCodexレビュー指摘、Major対応: 以前はこの
        # 読み込みループが上のHTTP例外捕捉の外にあり、接続先URLを含む
        # 生の例外メッセージがそのまま漏れ得た)。
        for chunk in response.iter_content(chunk_size=65536):
            if not chunk:
                continue
            total += len(chunk)
            if total > MAX_UPLOAD_RESPONSE_BYTES:
                raise ComfyUIUploadError(
                    f"アップロード応答サイズが上限({MAX_UPLOAD_RESPONSE_BYTES}バイト)を超えています"
                )
            body_chunks.append(chunk)
    except requests.exceptions.RequestException:
        raise ComfyUIUploadError("アップロード応答本文の読み込みに失敗しました") from None
    finally:
        response.close()

    try:
        response_json = json.loads(b"".join(body_chunks).decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        raise ComfyUIUploadError("アップロード応答のJSON解析に失敗しました") from None

    return validate_upload_response(response_json)
