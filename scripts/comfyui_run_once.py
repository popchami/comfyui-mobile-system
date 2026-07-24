#!/usr/bin/env python3
"""ハルト1人・第1コマ・生成1枚に固定した「単発実行経路」のオーケストレーター。

Manga News Packet v2の読み込みから、正本画像アップロード・ComfyUI
Workflow送信・完了待ち・生成画像取得・実ピクセル変換までを、1回の明示操作
で順番に実行できるようにする。実際にRunPod・ComfyUIへ通信するのは
`execute=True`を明示した場合のみであり、既定は`dry-run`(通信なし)。

責務分離:

- 本モジュール(`run_once()`): 各段階の順序・状態管理・実行記録の組み立てを
  担うオーケストレーター。HTTP通信の詳細は持たない。
- `submit_prompt()`/`poll_history()`/`download_generated_image()`: それぞれ
  独立したHTTP境界(`/prompt`・`/history/{prompt_id}`・`/view`)。個別に
  timeout・応答検証・sessionの差し替えが可能。
- `scripts/comfyui_upload.py`: `/upload/image`境界(再利用、重複実装しない)。
- `scripts/one_panel_pilot.py`: Packet読み込み・Workflow構築・dry-run
  検証(`run_dry_run()`を再利用、重複実装しない)。
- `scripts/panel_pixel_convert.py`: 実ピクセル変換(`convert_generation_to_panel()`
  を再利用、重複実装しない)。

RunPod方式についての注意(scripts/comfyui_upload.py・ONE_PANEL_PILOT.md
と同じ理解): このリポジトリの既存実装はRunPod Pod上で直接動くComfyUI
サーバーへHTTPアクセスする方式(Podのプロキシ経由URL)を前提にしていると
読み取れるが、これは既存コード・文書からの読み取りに基づく理解であり、
RunPod Serverless API経由が必要になる可能性は排除していない(未確定事項)。
本モジュールは`api_mode="pod-direct"`のみを実装しており、
`api_mode="serverless"`を指定した場合は通信前に明確なエラーで拒否する
(未実装の方式で誤ったリクエスト形状を送らないため)。

安全設計:

- 既定は常にdry-run。`execute=True`を明示しない限り、HTTPクライアントは
  一切呼ばれない。
- 通信先URL・APIキーはコード・設定ファイルへ保存せず、引数または環境変数
  (`RUNPOD_ENDPOINT_URL`・`RUNPOD_API_KEY`)から受け取る。
- 例外メッセージ・実行記録JSON・ログには、URL実値・APIキー・生の
  prompt_id・ローカル絶対パスを一切含めない。
- 自動retryは行わない(1回のリクエストのみ。ポーリングは完了待ちの
  ためのものであり、送信のやり直しではない)。
- 対象はハルト・panel_no=1・生成1枚に固定し、それ以外の指定は拒否する。
"""
import copy
import hashlib
import json
import os
import re
import sys
import tempfile
import time
import urllib.parse
import uuid
from pathlib import Path

import requests

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import one_panel_pilot as opp  # noqa: E402
import comfyui_upload as cu  # noqa: E402
import panel_pixel_convert as ppc  # noqa: E402


class ComfyUIRunOnceError(Exception):
    """単発実行の失敗を表す。

    `stage`(どの段階で停止したか)・`error_code`(機械可読な短いコード)を
    保持する。メッセージ・属性のいずれにも秘密情報・接続先実値を含めない。
    """

    def __init__(self, message, stage, error_code):
        super().__init__(message)
        self.stage = stage
        self.error_code = error_code


# 単発実行の段階(実行記録・stopped_stageで使う順序付き一覧)。
STAGE_LOAD_PACKET = "load_packet"
STAGE_RESOLVE_REFERENCE = "resolve_reference"
STAGE_BUILD_WORKFLOW = "build_workflow"
STAGE_UPLOAD_IMAGE = "upload_image"
STAGE_VALIDATE_UPLOAD_RESPONSE = "validate_upload_response"
STAGE_APPLY_WORKFLOW_IMAGE = "apply_workflow_image"
STAGE_SUBMIT_PROMPT = "submit_prompt"
STAGE_VALIDATE_PROMPT_ID = "validate_prompt_id"
STAGE_POLL_COMPLETION = "poll_completion"
STAGE_VALIDATE_HISTORY = "validate_history"
STAGE_DOWNLOAD_IMAGE = "download_image"
STAGE_CONVERT_PIXELS = "convert_pixels"
STAGE_SAVE_RESULT = "save_result"

STAGE_ORDER = [
    STAGE_LOAD_PACKET,
    STAGE_RESOLVE_REFERENCE,
    STAGE_BUILD_WORKFLOW,
    STAGE_UPLOAD_IMAGE,
    STAGE_VALIDATE_UPLOAD_RESPONSE,
    STAGE_APPLY_WORKFLOW_IMAGE,
    STAGE_SUBMIT_PROMPT,
    STAGE_VALIDATE_PROMPT_ID,
    STAGE_POLL_COMPLETION,
    STAGE_VALIDATE_HISTORY,
    STAGE_DOWNLOAD_IMAGE,
    STAGE_CONVERT_PIXELS,
    STAGE_SAVE_RESULT,
]

SCHEMA_VERSION = 1

# --- HTTP境界の既定値 ------------------------------------------------------

DEFAULT_TIMEOUT_SECONDS = 30

# /prompt・/history応答はメタデータのみ(画像本体は含まない)なので小さい。
MAX_JSON_RESPONSE_BYTES = 2 * 1024 * 1024  # 2MB

# 生成画像(1536x640)のダウンロード上限。RGBA非圧縮換算(1536*640*4≈3.93MB)
# の約8倍の余裕を持たせた値(PNG圧縮で通常はこれより小さくなるが、
# 圧縮が効きにくい内容でも安全に収まるよう余裕を確保する)。
MAX_DOWNLOAD_BYTES = 32 * 1024 * 1024  # 32MB

ALLOWED_JSON_CONTENT_TYPES = ("application/json",)
ALLOWED_IMAGE_CONTENT_TYPES = ("image/png",)

# ポーリング既定値(既存chibi HTML実装が使う5分のハードタイムアウトを
# 参考値とする)。
DEFAULT_POLL_INTERVAL_SECONDS = 2.0
DEFAULT_POLL_MAX_ATTEMPTS = 150
DEFAULT_POLL_TOTAL_TIMEOUT_SECONDS = 300.0

# ポーリングパラメータの許容上限(bool・NaN・Infinity・0・負数に加え、
# 非現実的に巨大な値も拒否するための上限)。
MAX_POLL_INTERVAL_SECONDS = 60.0
MAX_POLL_MAX_ATTEMPTS = 1000
MAX_POLL_TOTAL_TIMEOUT_SECONDS = 3600.0

# 各HTTPリクエストのtimeout・ダウンロードサイズ上限の許容上限
# (2回目のCodexレビュー指摘、Major対応: 以前は個別のtimeout・
# download_max_bytes引数がbool・非有限・巨大値を拒否していなかった)。
MAX_REQUEST_TIMEOUT_SECONDS = 120.0
MAX_DOWNLOAD_BYTES_HARD_CAP = 64 * 1024 * 1024  # 64MB(既定32MBの2倍を上限とする)

_PROMPT_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,128}$")

SAVE_IMAGE_NODE_ID = "12"  # scripts/one_panel_pilot.py の build_comfyui_workflow() が組み立てるnode_id

# scripts/one_panel_pilot.py の build_comfyui_workflow() が組み立てる固定node
# グラフの、node_id→期待class_typeの対応(4回目のCodexレビュー指摘、Major
# 対応: 以前は`opp.validate_workflow_shape()`が各node_idに`class_type`・
# `inputs`キーが存在することしか確認しておらず、class_type自体の値や
# SaveImageの一意性を検証していなかった。Workflowが変更されてnode 12が
# SaveImage以外になっても、あるいは別のSaveImageノードが追加されても、
# 送信前に検知できなかった)。
EXPECTED_NODE_CLASS_TYPES = {
    "1": "CheckpointLoaderSimple",
    "6": "CLIPTextEncode",
    "8": "CLIPTextEncode",
    "9": "EmptyLatentImage",
    "10": "KSampler",
    "11": "VAEDecode",
    "12": "SaveImage",
    "30": "IPAdapterUnifiedLoader",
    "31": "IPAdapterAdvanced",
    "35": "CLIPVisionLoader",
    "36": "LoadImage",
}

# EmptyLatentImage(node "9")の固定生成解像度・バッチサイズ(このpilotは
# ハルト・panel_no=1・生成1枚に固定するため、これ以外の値を許容しない)。
EXPECTED_LATENT_WIDTH = 1536
EXPECTED_LATENT_HEIGHT = 640
EXPECTED_LATENT_BATCH_SIZE = 1


def _validate_fixed_workflow_contract(workflow, stage):
    """`/prompt`送信直前に、固定node-idグラフの契約を再検証する。

    - 各固定node_idのclass_typeが期待通りであること
    - SaveImageノードがnode "12"の1個だけであること(他のnode_idに
      SaveImageが紛れ込んでいないこと)
    - EmptyLatentImage(node "9")のwidth/height/batch_sizeが、この
      pilotが前提とする1536×640×1で固定されていること

    `opp.validate_workflow_shape()`(必須node_idの存在・型のみ検証)を
    補完し、Workflow差し替え・改変によって固定node-id前提が崩れていないか
    を送信直前に確認する。
    """
    for node_id, expected_class_type in EXPECTED_NODE_CLASS_TYPES.items():
        node = workflow.get(node_id)
        if not isinstance(node, dict) or node.get("class_type") != expected_class_type:
            raise ComfyUIRunOnceError(
                f"node_id={node_id!r}のclass_typeが期待値と一致しません"
                f"(期待: {expected_class_type})",
                stage=stage,
                error_code="WORKFLOW_CONTRACT_MISMATCH",
            )

    save_image_node_ids = [
        node_id
        for node_id, node in workflow.items()
        if isinstance(node, dict) and node.get("class_type") == "SaveImage"
    ]
    if save_image_node_ids != [SAVE_IMAGE_NODE_ID]:
        raise ComfyUIRunOnceError(
            "SaveImageノードはnode_id="
            f"{SAVE_IMAGE_NODE_ID!r}の1個だけである必要があります"
            f"(実際: {len(save_image_node_ids)}個)",
            stage=stage,
            error_code="WORKFLOW_CONTRACT_MISMATCH",
        )

    latent_inputs = workflow.get("9", {}).get("inputs", {})
    if (
        latent_inputs.get("width") != EXPECTED_LATENT_WIDTH
        or latent_inputs.get("height") != EXPECTED_LATENT_HEIGHT
        or latent_inputs.get("batch_size") != EXPECTED_LATENT_BATCH_SIZE
    ):
        raise ComfyUIRunOnceError(
            "EmptyLatentImageのwidth/height/batch_sizeが固定契約"
            f"({EXPECTED_LATENT_WIDTH}x{EXPECTED_LATENT_HEIGHT}x"
            f"{EXPECTED_LATENT_BATCH_SIZE})と一致しません",
            stage=stage,
            error_code="WORKFLOW_CONTRACT_MISMATCH",
        )


def _validate_timeout_value(timeout, stage, error_code):
    """timeout引数(秒)がbool・非数値・NaN・Infinity・0以下・巨大値でない
    ことを検証する(2回目のCodexレビュー指摘、Major対応)。
    """
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)):
        raise ComfyUIRunOnceError("timeoutは数値である必要があります(bool不可)", stage=stage, error_code=error_code)
    if timeout != timeout or timeout in (float("inf"), float("-inf")):
        raise ComfyUIRunOnceError("timeoutは有限の数値である必要があります", stage=stage, error_code=error_code)
    if timeout <= 0:
        raise ComfyUIRunOnceError("timeoutは正の数値である必要があります", stage=stage, error_code=error_code)
    if timeout > MAX_REQUEST_TIMEOUT_SECONDS:
        raise ComfyUIRunOnceError(
            f"timeoutが上限({MAX_REQUEST_TIMEOUT_SECONDS}秒)を超えています", stage=stage, error_code=error_code
        )


def _validate_download_max_bytes(max_bytes, stage, error_code):
    if isinstance(max_bytes, bool) or not isinstance(max_bytes, int):
        raise ComfyUIRunOnceError(
            "download_max_bytesは整数である必要があります(bool不可)", stage=stage, error_code=error_code
        )
    if max_bytes <= 0 or max_bytes > MAX_DOWNLOAD_BYTES_HARD_CAP:
        raise ComfyUIRunOnceError(
            f"download_max_bytesは1以上{MAX_DOWNLOAD_BYTES_HARD_CAP}以下である必要があります",
            stage=stage,
            error_code=error_code,
        )


def _validate_base_url(base_url, stage):
    """base_urlを検証し、正規化した`scheme://host[:port]`だけを返す。

    2回目のCodexレビュー指摘、Critical対応: 以前はbase_urlが空でないこと
    しか確認しておらず、userinfo(認証情報の混入)・query・fragment・
    パス付き・http(平文)・ホスト名欠落を許していた。これにより、
    Authorizationヘッダーが意図しないホストへ送られたり、URL自体に
    埋め込まれた認証情報がそのまま使われたりする可能性があった。
    """
    if not isinstance(base_url, str) or not base_url:
        raise ComfyUIRunOnceError("base_urlが指定されていません", stage=stage, error_code="INVALID_BASE_URL")
    try:
        parsed = urllib.parse.urlsplit(base_url)
    except ValueError:
        raise ComfyUIRunOnceError("base_urlの形式が不正です", stage=stage, error_code="INVALID_BASE_URL") from None

    if parsed.scheme != "https":
        raise ComfyUIRunOnceError(
            "base_urlはhttps schemeである必要があります", stage=stage, error_code="INVALID_BASE_URL"
        )
    if not parsed.hostname:
        raise ComfyUIRunOnceError("base_urlにホスト名がありません", stage=stage, error_code="INVALID_BASE_URL")
    if parsed.username or parsed.password:
        raise ComfyUIRunOnceError(
            "base_urlに認証情報(userinfo)を含めることはできません", stage=stage, error_code="INVALID_BASE_URL"
        )
    if parsed.query or parsed.fragment:
        raise ComfyUIRunOnceError(
            "base_urlにquery/fragmentを含めることはできません", stage=stage, error_code="INVALID_BASE_URL"
        )
    if parsed.path not in ("", "/"):
        raise ComfyUIRunOnceError("base_urlにパスを含めることはできません", stage=stage, error_code="INVALID_BASE_URL")

    return f"{parsed.scheme}://{parsed.netloc}"


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


def _new_client_id():
    """ComfyUIの`/prompt`・`/ws`で使うclient_idを生成する。

    秘密情報ではないが、実行記録JSONへは含めない(再現・追跡目的の識別子を
    無条件に外部出力しないため)。
    """
    return uuid.uuid4().hex


def _hash_prompt_id(prompt_id):
    """実行記録へ含めてよい、生のprompt_idを含まない非可逆な短いハッシュを作る。"""
    return hashlib.sha256(prompt_id.encode("utf-8")).hexdigest()[:16]


def _validate_prompt_id(prompt_id):
    if not isinstance(prompt_id, str) or not _PROMPT_ID_RE.match(prompt_id):
        raise ComfyUIRunOnceError(
            "prompt_idが安全な文字列ではありません",
            stage=STAGE_VALIDATE_PROMPT_ID,
            error_code="INVALID_PROMPT_ID",
        )
    return prompt_id


def _validate_poll_params(poll_interval_seconds, max_attempts, total_timeout_seconds):
    checks = (
        ("poll_interval_seconds", poll_interval_seconds, MAX_POLL_INTERVAL_SECONDS),
        ("total_timeout_seconds", total_timeout_seconds, MAX_POLL_TOTAL_TIMEOUT_SECONDS),
    )
    for name, value, max_value in checks:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ComfyUIRunOnceError(
                f"{name}は数値である必要があります(bool不可)",
                stage=STAGE_POLL_COMPLETION,
                error_code="INVALID_POLL_PARAMS",
            )
        if value != value or value in (float("inf"), float("-inf")):
            raise ComfyUIRunOnceError(
                f"{name}は有限の数値である必要があります",
                stage=STAGE_POLL_COMPLETION,
                error_code="INVALID_POLL_PARAMS",
            )
        if value <= 0:
            raise ComfyUIRunOnceError(
                f"{name}は正の数値である必要があります",
                stage=STAGE_POLL_COMPLETION,
                error_code="INVALID_POLL_PARAMS",
            )
        if value > max_value:
            raise ComfyUIRunOnceError(
                f"{name}が上限({max_value})を超えています",
                stage=STAGE_POLL_COMPLETION,
                error_code="INVALID_POLL_PARAMS",
            )

    if isinstance(max_attempts, bool) or not isinstance(max_attempts, int):
        raise ComfyUIRunOnceError(
            "max_attemptsは整数である必要があります(bool不可)",
            stage=STAGE_POLL_COMPLETION,
            error_code="INVALID_POLL_PARAMS",
        )
    if max_attempts <= 0 or max_attempts > MAX_POLL_MAX_ATTEMPTS:
        raise ComfyUIRunOnceError(
            f"max_attemptsは1以上{MAX_POLL_MAX_ATTEMPTS}以下である必要があります",
            stage=STAGE_POLL_COMPLETION,
            error_code="INVALID_POLL_PARAMS",
        )


def _reject_redirect(response, stage, error_code):
    """3xx応答(redirect)を一律で拒否する。

    別ホストへのredirectで接続先が入れ替わる事態を避けるため、同一ホストへの
    redirectであっても一切追従しない(呼び出し側は常に`allow_redirects=False`
    でリクエストすること)。Location値はログ・例外へ含めない(接続先実値の
    漏洩を避ける)。
    """
    if 300 <= response.status_code < 400:
        raise ComfyUIRunOnceError(
            f"予期しないredirect応答です(HTTP {response.status_code}、リダイレクト先は追従しません)",
            stage=stage,
            error_code=error_code,
        )


def _read_capped_bytes(response, max_bytes, stage, error_code):
    total = 0
    chunks = []
    try:
        # `stream=True`化後、応答本文の読み込み中にもrequestsの例外
        # (Timeout・ConnectionError・ChunkedEncodingError等)が送出され
        # 得る(3回目のCodexレビュー指摘、Major対応: 以前はこの読み込み
        # ループが呼び出し元のHTTP例外捕捉の外にあり、接続先URLを含む
        # 生の例外メッセージがそのまま漏れ得た)。
        for chunk in response.iter_content(chunk_size=65536):
            if not chunk:
                continue
            total += len(chunk)
            if total > max_bytes:
                raise ComfyUIRunOnceError(
                    f"応答サイズが上限({max_bytes}バイト)を超えています",
                    stage=stage,
                    error_code=error_code,
                )
            chunks.append(chunk)
    except requests.exceptions.RequestException:
        raise ComfyUIRunOnceError(
            "応答本文の読み込みに失敗しました", stage=stage, error_code=error_code
        ) from None
    finally:
        response.close()
    return b"".join(chunks)


def _validate_content_type(response, allowed_prefixes, stage, error_code):
    content_type = (response.headers.get("Content-Type") or "").split(";")[0].strip().lower()
    if content_type not in allowed_prefixes:
        raise ComfyUIRunOnceError(
            f"Content-Typeが許可されていません(許可: {', '.join(allowed_prefixes)})",
            stage=stage,
            error_code=error_code,
        )


def _read_capped_json(response, max_bytes, stage, error_code):
    _validate_content_type(response, ALLOWED_JSON_CONTENT_TYPES, stage, error_code)
    content = _read_capped_bytes(response, max_bytes, stage, error_code)
    try:
        return json.loads(content.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        raise ComfyUIRunOnceError(
            "応答のJSON解析に失敗しました",
            stage=stage,
            error_code=error_code,
        ) from None


def _auth_headers():
    """`RUNPOD_API_KEY`が設定されている場合のみAuthorizationヘッダーを作る。

    値自体は関数のローカル変数にのみ保持し、戻り値以外のどこにも
    (ログ・例外・実行記録)出力しない。
    """
    api_key = os.environ.get("RUNPOD_API_KEY")
    if not api_key:
        return {}
    return {"Authorization": f"Bearer {api_key}"}


def submit_prompt(base_url, workflow, session=None, timeout=DEFAULT_TIMEOUT_SECONDS, client_id=None):
    """ComfyUIの`/prompt`へWorkflowを1回だけPOSTし、検証済みprompt_idを返す。

    - `node_errors`が空でない場合は生成待ちへ進まず明確に拒否する。
    - `prompt_id`は安全な文字列パターンであることを検証する
      (`/history/{prompt_id}`のURLパス組み立てに使うため)。
    - retryは行わない(1回のみ)。
    """
    if not isinstance(workflow, dict):
        raise ComfyUIRunOnceError(
            "workflowはdictである必要があります", stage=STAGE_SUBMIT_PROMPT, error_code="INVALID_WORKFLOW"
        )
    _validate_timeout_value(timeout, STAGE_SUBMIT_PROMPT, "INVALID_TIMEOUT")
    base_url = _validate_base_url(base_url, STAGE_SUBMIT_PROMPT)
    client_id = client_id or _new_client_id()
    http = session or _default_session()
    url = f"{base_url}/prompt"

    try:
        response = http.post(
            url,
            json={"prompt": workflow, "client_id": client_id},
            headers=_auth_headers(),
            timeout=timeout,
            allow_redirects=False,
            stream=True,
        )
    except requests.exceptions.Timeout:
        raise ComfyUIRunOnceError(
            "prompt送信がタイムアウトしました", stage=STAGE_SUBMIT_PROMPT, error_code="SUBMIT_TIMEOUT"
        ) from None
    except requests.exceptions.RequestException:
        raise ComfyUIRunOnceError(
            "prompt送信が失敗しました(接続先・認証情報の詳細はここには含めません)",
            stage=STAGE_SUBMIT_PROMPT,
            error_code="SUBMIT_FAILED",
        ) from None

    _reject_redirect(response, STAGE_SUBMIT_PROMPT, "SUBMIT_REDIRECT")
    if response.status_code != 200:
        raise ComfyUIRunOnceError(
            f"prompt送信が失敗しました(HTTP {response.status_code})",
            stage=STAGE_SUBMIT_PROMPT,
            error_code="SUBMIT_HTTP_ERROR",
        )

    body = _read_capped_json(response, MAX_JSON_RESPONSE_BYTES, STAGE_SUBMIT_PROMPT, "SUBMIT_RESPONSE_INVALID")
    if not isinstance(body, dict):
        raise ComfyUIRunOnceError(
            "prompt応答がオブジェクトではありません",
            stage=STAGE_SUBMIT_PROMPT,
            error_code="SUBMIT_RESPONSE_INVALID",
        )

    # node_errorsをtruthinessだけで判定しない(2回目のCodexレビュー指摘、
    # Major対応: 以前は`[]`や`0`等のfalsyな非dict値も「エラーなし」として
    # 通過していた)。キー自体が欠損している場合のみ「エラーなし」として
    # 許容する(このリポジトリでは実際のComfyUI応答スキーマを確認できて
    # いないため、欠損自体を拒否するほど断定しない)。`"node_errors": null`
    # のような明示的なnullは、キー欠損とは区別して型違反として拒否する
    # (3回目のCodexレビュー指摘、Major対応: `body.get()`だけではキー欠損と
    # 明示的なnullを区別できず、以前はnullも欠損と同様に通過していた)。
    if "node_errors" in body:
        node_errors = body["node_errors"]
        if not isinstance(node_errors, dict):
            raise ComfyUIRunOnceError(
                "prompt応答のnode_errorsの型が不正です",
                stage=STAGE_VALIDATE_PROMPT_ID,
                error_code="INVALID_NODE_ERRORS",
            )
        if node_errors:
            raise ComfyUIRunOnceError(
                "prompt応答にnode_errorsが含まれています(生成待ちへは進みません)",
                stage=STAGE_VALIDATE_PROMPT_ID,
                error_code="NODE_ERRORS",
            )

    prompt_id = body.get("prompt_id")
    if not isinstance(prompt_id, str) or not prompt_id:
        raise ComfyUIRunOnceError(
            "prompt応答にprompt_idが含まれていません",
            stage=STAGE_VALIDATE_PROMPT_ID,
            error_code="MISSING_PROMPT_ID",
        )
    return _validate_prompt_id(prompt_id)


def _validate_history_image_descriptor(descriptor):
    """SaveImageノードのhistory出力内、1画像記述(filename/subfolder/type)を
    検証する。

    comfyui_upload.py が`/upload/image`応答(name/subfolder/type)に対して
    行っている検証(単一segment・パストラバーサル拒否・ComfyUI予約注釈拒否)
    を、`filename`キーに対して再利用する(重複実装しない)。

    ComfyUI本体(nodes.py `SaveImage.__init__()`が`self.type = "output"`を
    固定している)を確認したところ、SaveImageノードが書き出す画像の`type`は
    常に`"output"`である(4回目のCodexレビュー指摘、Major対応: 以前は
    `/upload/image`応答用の`input`/`temp`/`output`という広い許可集合を
    そのまま再利用しており、SaveImageの出力ではないはずの`input`/`temp`
    画像を生成結果として誤って採用し得た)。
    """
    if not isinstance(descriptor, dict):
        raise ComfyUIRunOnceError(
            "生成画像情報がオブジェクトではありません",
            stage=STAGE_VALIDATE_HISTORY,
            error_code="HISTORY_IMAGE_INVALID",
        )
    filename = descriptor.get("filename")
    subfolder = descriptor.get("subfolder", "")
    image_type = descriptor.get("type")
    try:
        cu._validate_server_path_component("filename", filename, allow_empty=False, allow_nested=False)
        cu._validate_server_path_component("subfolder", subfolder, allow_empty=True, allow_nested=True)
    except cu.ComfyUIUploadError as e:
        raise ComfyUIRunOnceError(
            f"生成画像情報の検証に失敗しました: {e}",
            stage=STAGE_VALIDATE_HISTORY,
            error_code="HISTORY_IMAGE_INVALID",
        ) from None
    if image_type != "output":
        raise ComfyUIRunOnceError(
            "生成画像情報のtypeがSaveImage出力として不正です(outputである必要があります)",
            stage=STAGE_VALIDATE_HISTORY,
            error_code="HISTORY_IMAGE_INVALID",
        )
    return {"filename": filename, "subfolder": subfolder, "type": image_type}


def poll_history(
    base_url,
    prompt_id,
    session=None,
    timeout=DEFAULT_TIMEOUT_SECONDS,
    poll_interval_seconds=DEFAULT_POLL_INTERVAL_SECONDS,
    max_attempts=DEFAULT_POLL_MAX_ATTEMPTS,
    total_timeout_seconds=DEFAULT_POLL_TOTAL_TIMEOUT_SECONDS,
    sleep_fn=time.sleep,
    monotonic_fn=time.monotonic,
):
    """`/history/{prompt_id}`を有限回・有限時間だけポーリングし、検証済みの
    生成画像記述(1枚だけ)を返す。

    - poll_interval_seconds・max_attempts・total_timeout_secondsはすべて
      正の有限値であることを検証する(bool・NaN・Infinity・0・負数・
      非現実的な巨大値を拒否)。
    - `total_timeout_seconds`は`monotonic_fn`(既定`time.monotonic`)による
      実経過時間で管理する(2回目のCodexレビュー指摘、Major対応: 以前は
      予定sleep秒数の積算のみで、HTTP応答時間・JSON処理時間・実際の
      sleep時間を含んでおらず、低速な応答が続くと総timeoutを大幅に
      超過し得た)。個々のHTTPリクエストのtimeoutも残り時間以下に
      切り詰める
    - 監視用の無限ループは作らない(max_attempts・total_timeout_secondsの
      いずれかに達したら明確なタイムアウトエラーで停止する)。
    - 対象prompt_idの履歴だけを採用する(別prompt_idのデータは無視)。
    - SaveImageノードの出力画像が0枚または2枚以上の場合は拒否する
      (先頭を黙って採用しない)。
    """
    _validate_poll_params(poll_interval_seconds, max_attempts, total_timeout_seconds)
    _validate_timeout_value(timeout, STAGE_POLL_COMPLETION, "INVALID_TIMEOUT")
    prompt_id = _validate_prompt_id(prompt_id)
    base_url = _validate_base_url(base_url, STAGE_POLL_COMPLETION)
    http = session or _default_session()
    url = f"{base_url}/history/{prompt_id}"

    deadline = monotonic_fn() + total_timeout_seconds

    for attempt in range(max_attempts):
        remaining = deadline - monotonic_fn()
        if remaining <= 0:
            break
        request_timeout = min(timeout, remaining)

        try:
            response = http.get(
                url, headers=_auth_headers(), timeout=request_timeout, allow_redirects=False, stream=True
            )
        except requests.exceptions.Timeout:
            raise ComfyUIRunOnceError(
                "history取得がタイムアウトしました", stage=STAGE_POLL_COMPLETION, error_code="HISTORY_TIMEOUT"
            ) from None
        except requests.exceptions.RequestException:
            raise ComfyUIRunOnceError(
                "history取得が失敗しました(接続先・認証情報の詳細はここには含めません)",
                stage=STAGE_POLL_COMPLETION,
                error_code="HISTORY_REQUEST_FAILED",
            ) from None

        _reject_redirect(response, STAGE_POLL_COMPLETION, "HISTORY_REDIRECT")
        if response.status_code != 200:
            raise ComfyUIRunOnceError(
                f"history取得が失敗しました(HTTP {response.status_code})",
                stage=STAGE_POLL_COMPLETION,
                error_code="HISTORY_HTTP_ERROR",
            )

        body = _read_capped_json(response, MAX_JSON_RESPONSE_BYTES, STAGE_POLL_COMPLETION, "HISTORY_RESPONSE_INVALID")
        if not isinstance(body, dict):
            raise ComfyUIRunOnceError(
                "history応答がオブジェクトではありません",
                stage=STAGE_POLL_COMPLETION,
                error_code="HISTORY_RESPONSE_INVALID",
            )

        # `prompt_id in body`でキー欠損(=まだ生成待ち)と、キーは存在する
        # が値が`null`である応答(=不正な応答)を区別する(4回目のCodex
        # レビュー指摘、Minor対応: 以前は`body.get(prompt_id)`のみを使い、
        # 両者を区別できず、不正な応答も待機継続として扱っていた)。
        if prompt_id in body:
            entry = body[prompt_id]
            if not isinstance(entry, dict):
                raise ComfyUIRunOnceError(
                    "history entryがオブジェクトではありません",
                    stage=STAGE_VALIDATE_HISTORY,
                    error_code="HISTORY_ENTRY_INVALID",
                )
            # 応答本文の読み込み完了直後にも総timeoutを再確認する(3回目の
            # Codexレビュー指摘、Major対応: 個々のリクエストのtimeoutは
            # 残り時間以下に切り詰めているが、低速なストリーミング応答は
            # 単発のtimeout未満のまま総予算を超過し得るため、成功として
            # 返す直前にも締切超過をPOLL_TIMEOUTとして扱う)。
            if monotonic_fn() > deadline:
                raise ComfyUIRunOnceError(
                    "生成完了の待機がタイムアウトしました(応答受信完了時に総timeoutを超過)",
                    stage=STAGE_POLL_COMPLETION,
                    error_code="POLL_TIMEOUT",
                )
            return _validate_history_entry(entry)

        remaining = deadline - monotonic_fn()
        if attempt + 1 >= max_attempts or remaining <= 0:
            break
        sleep_fn(min(poll_interval_seconds, remaining))

    raise ComfyUIRunOnceError(
        "生成完了の待機がタイムアウトしました(poll上限に到達)",
        stage=STAGE_POLL_COMPLETION,
        error_code="POLL_TIMEOUT",
    )


def _validate_history_entry(entry):
    """history[prompt_id]の1件を検証し、SaveImageノードの検証済み画像記述を返す。

    ComfyUI本体(execution.py `PromptQueue.task_done()`/`main.py`)の実装を
    確認したところ、historyの各entryは常に`status`キーを持ち、その値は
    `{"status_str": "success"|"error", "completed": bool, "messages": [...]}`
    という形の辞書である(4回目のCodexレビュー指摘、Major対応: 以前は
    既存ブラウザUI実装が`status`を参照していないことを理由に、`status`
    欠損・非dictを許容していたが、ComfyUI本体のソースで実際のスキーマを
    確認できたため、欠損・非dict・`status_str!="success"`・
    `completed is not True`をすべて拒否するよう厳格化する)。
    """
    if not isinstance(entry, dict):
        raise ComfyUIRunOnceError(
            "history entryがオブジェクトではありません",
            stage=STAGE_VALIDATE_HISTORY,
            error_code="HISTORY_ENTRY_INVALID",
        )

    status = entry.get("status")
    if not isinstance(status, dict):
        raise ComfyUIRunOnceError(
            "history entryにstatusが含まれていないか、形式が不正です",
            stage=STAGE_VALIDATE_HISTORY,
            error_code="GENERATION_FAILED",
        )
    if status.get("status_str") != "success":
        raise ComfyUIRunOnceError(
            "history entryが成功状態を示していません(status_strがsuccess以外)",
            stage=STAGE_VALIDATE_HISTORY,
            error_code="GENERATION_FAILED",
        )
    if status.get("completed") is not True:
        raise ComfyUIRunOnceError(
            "history entryが完了を示していません(status.completedがTrueではない)",
            stage=STAGE_VALIDATE_HISTORY,
            error_code="GENERATION_FAILED",
        )

    outputs = entry.get("outputs")
    if not isinstance(outputs, dict):
        raise ComfyUIRunOnceError(
            "history entryにoutputsがありません",
            stage=STAGE_VALIDATE_HISTORY,
            error_code="HISTORY_NO_OUTPUTS",
        )

    save_image_output = outputs.get(SAVE_IMAGE_NODE_ID)
    if not isinstance(save_image_output, dict):
        raise ComfyUIRunOnceError(
            f"history entryにnode_id={SAVE_IMAGE_NODE_ID!r}(SaveImage)の出力がありません",
            stage=STAGE_VALIDATE_HISTORY,
            error_code="HISTORY_NO_SAVE_IMAGE_OUTPUT",
        )

    images = save_image_output.get("images")
    if not isinstance(images, list) or len(images) == 0:
        raise ComfyUIRunOnceError(
            "生成画像が0枚です", stage=STAGE_VALIDATE_HISTORY, error_code="NO_IMAGES"
        )
    if len(images) > 1:
        raise ComfyUIRunOnceError(
            f"生成画像が複数({len(images)}枚)返されました(先頭を黙って採用しません)",
            stage=STAGE_VALIDATE_HISTORY,
            error_code="MULTIPLE_IMAGES",
        )

    return _validate_history_image_descriptor(images[0])


def download_generated_image(
    base_url,
    image_descriptor,
    dest_path,
    session=None,
    timeout=DEFAULT_TIMEOUT_SECONDS,
    max_bytes=MAX_DOWNLOAD_BYTES,
    overwrite=False,
):
    """`/view`から生成画像を1回だけ取得し、検証した上でdest_pathへ保存する。

    - Content-TypeがPNGとして許可できることを確認する。
    - ダウンロードサイズ上限を適用する。
    - PNGシグネチャを検証する(HTMLエラーページ等を画像として保存しない)。
    - 一時ファイルへ保存し、検証後に確定する(既存出力を無断で上書きしない)。
    """
    _validate_timeout_value(timeout, STAGE_DOWNLOAD_IMAGE, "INVALID_TIMEOUT")
    _validate_download_max_bytes(max_bytes, STAGE_DOWNLOAD_IMAGE, "INVALID_DOWNLOAD_MAX_BYTES")
    base_url = _validate_base_url(base_url, STAGE_DOWNLOAD_IMAGE)

    dest_path = Path(dest_path)
    if dest_path.exists() and not overwrite:
        raise ComfyUIRunOnceError(
            f"出力先が既に存在します(overwrite未指定): {dest_path.name}",
            stage=STAGE_DOWNLOAD_IMAGE,
            error_code="DOWNLOAD_DEST_EXISTS",
        )

    params = {
        "filename": image_descriptor["filename"],
        "subfolder": image_descriptor.get("subfolder") or "",
        "type": image_descriptor["type"],
    }
    http = session or _default_session()
    url = f"{base_url}/view"

    try:
        response = http.get(
            url, params=params, headers=_auth_headers(), timeout=timeout, allow_redirects=False, stream=True
        )
    except requests.exceptions.Timeout:
        raise ComfyUIRunOnceError(
            "画像取得がタイムアウトしました", stage=STAGE_DOWNLOAD_IMAGE, error_code="DOWNLOAD_TIMEOUT"
        ) from None
    except requests.exceptions.RequestException:
        raise ComfyUIRunOnceError(
            "画像取得が失敗しました(接続先・認証情報の詳細はここには含めません)",
            stage=STAGE_DOWNLOAD_IMAGE,
            error_code="DOWNLOAD_FAILED",
        ) from None

    _reject_redirect(response, STAGE_DOWNLOAD_IMAGE, "DOWNLOAD_REDIRECT")
    if response.status_code != 200:
        raise ComfyUIRunOnceError(
            f"画像取得が失敗しました(HTTP {response.status_code})",
            stage=STAGE_DOWNLOAD_IMAGE,
            error_code="DOWNLOAD_HTTP_ERROR",
        )
    _validate_content_type(response, ALLOWED_IMAGE_CONTENT_TYPES, STAGE_DOWNLOAD_IMAGE, "DOWNLOAD_CONTENT_TYPE")

    content = _read_capped_bytes(response, max_bytes, STAGE_DOWNLOAD_IMAGE, "DOWNLOAD_TOO_LARGE")
    if content[: len(cu.PNG_SIGNATURE)] != cu.PNG_SIGNATURE:
        raise ComfyUIRunOnceError(
            "取得した画像のPNGシグネチャが一致しません(画像以外の可能性)",
            stage=STAGE_DOWNLOAD_IMAGE,
            error_code="DOWNLOAD_NOT_PNG",
        )

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path_str = tempfile.mkstemp(
        dir=str(dest_path.parent), prefix=f".{dest_path.name}.tmp-", suffix=".png"
    )
    tmp_path = Path(tmp_path_str)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(content)

        if overwrite:
            os.replace(tmp_path, dest_path)
            tmp_path = None
        else:
            try:
                os.link(tmp_path, dest_path)
            except FileExistsError:
                raise ComfyUIRunOnceError(
                    f"出力先が既に存在します(overwrite未指定): {dest_path.name}",
                    stage=STAGE_DOWNLOAD_IMAGE,
                    error_code="DOWNLOAD_DEST_EXISTS",
                ) from None
    finally:
        if tmp_path is not None:
            tmp_path.unlink(missing_ok=True)

    return {"dest_path": str(dest_path), "content_length": len(content)}


# opp.PilotErrorの既知メッセージ先頭パターンから、絶対パスを含まない
# 機械可読なerror_codeへ分類するための一覧(3回目のCodexレビュー指摘、
# Minor対応)。one_panel_pilot.py側のメッセージ文言に依存するため、
# 一致しない場合は安全側にフォールバックする("DRY_RUN_FAILED")。
_PILOT_ERROR_CODE_PREFIXES = (
    ("Packetファイルが見つかりません", "PACKET_NOT_FOUND"),
    ("PacketのJSONが不正です", "PACKET_INVALID_JSON"),
    ("five_panel_template.json", "PACKET_TEMPLATE_INVALID"),
    ("panel_no=", "PACKET_PANEL_NOT_FOUND"),
    ("設定ファイル", "CONFIG_INVALID"),
    ("参照画像の解決に失敗しました", "REFERENCE_RESOLUTION_FAILED"),
    ("解決した参照画像が通常ファイルではありません", "REFERENCE_RESOLUTION_FAILED"),
    ("manga_schema.py", "SCHEMA_MODULE_INVALID"),
)


def _classify_pilot_error_code(exc):
    message = str(exc)
    for prefix, code in _PILOT_ERROR_CODE_PREFIXES:
        if message.startswith(prefix):
            return code
    return "DRY_RUN_FAILED"


def run_once(
    packet_path,
    generation_dest_path,
    converted_dest_path,
    config_path=None,
    panel_no=1,
    expected_character="ハルト",
    seed=None,
    execute=False,
    api_mode="pod-direct",
    base_url=None,
    session=None,
    poll_interval_seconds=DEFAULT_POLL_INTERVAL_SECONDS,
    poll_max_attempts=DEFAULT_POLL_MAX_ATTEMPTS,
    poll_total_timeout_seconds=DEFAULT_POLL_TOTAL_TIMEOUT_SECONDS,
    sleep_fn=time.sleep,
    download_max_bytes=MAX_DOWNLOAD_BYTES,
    overwrite=False,
):
    """ハルト・panel_no=1・生成1枚に固定した単発実行を行う。

    `execute=False`(既定)の場合、実際のHTTP通信は一切行わず、Packet読み込み・
    Workflow構築・検証・アップロードリクエストの構築(dry-run)までを行い、
    実行記録を返す。`execute=True`の場合のみ、`/upload/image`→`/prompt`→
    `/history/{prompt_id}`ポーリング→`/view`ダウンロード→実ピクセル変換まで
    実際に(ただし本セッションのテストではsessionをmockした状態でのみ)実行する。
    """
    if not isinstance(execute, bool):
        raise ComfyUIRunOnceError(
            f"executeはbool型である必要があります: {type(execute).__name__}",
            stage=STAGE_LOAD_PACKET,
            error_code="INVALID_EXECUTE_TYPE",
        )
    if not isinstance(overwrite, bool):
        raise ComfyUIRunOnceError(
            f"overwriteはbool型である必要があります: {type(overwrite).__name__}",
            stage=STAGE_LOAD_PACKET,
            error_code="INVALID_OVERWRITE_TYPE",
        )
    if expected_character != "ハルト":
        raise ComfyUIRunOnceError(
            f"このpilotが現時点で正しく動作するキャラクターはハルトのみです: {expected_character!r}",
            stage=STAGE_LOAD_PACKET,
            error_code="UNSUPPORTED_CHARACTER",
        )
    if isinstance(panel_no, bool) or panel_no != 1:
        raise ComfyUIRunOnceError(
            f"このpilotが現時点で対応するpanel_noは1のみです: {panel_no!r}",
            stage=STAGE_LOAD_PACKET,
            error_code="UNSUPPORTED_PANEL_NO",
        )
    if api_mode not in ("pod-direct",):
        raise ComfyUIRunOnceError(
            f"api_mode={api_mode!r}は未対応です(現時点でpod-directのみ実装済み。"
            "RunPod Serverless APIへの対応は未確定・未実装です)",
            stage=STAGE_LOAD_PACKET,
            error_code="UNSUPPORTED_API_MODE",
        )
    if execute and not base_url:
        base_url = os.environ.get("RUNPOD_ENDPOINT_URL")
    if execute and not base_url:
        raise ComfyUIRunOnceError(
            "実接続にはbase_url(またはRUNPOD_ENDPOINT_URL環境変数)が必要です",
            stage=STAGE_LOAD_PACKET,
            error_code="MISSING_BASE_URL",
        )
    if execute:
        # base_urlはここで一度だけ検証・正規化し、以降のupload/prompt/
        # history/downloadすべてに同じ正規化済みURLを渡す(2回目のCodex
        # レビュー指摘、Critical対応: 以前はsubmit_prompt()以降でしか
        # 検証しておらず、`/upload/image`だけがhttp・userinfo混入等の
        # 不正なbase_urlのまま送信され得た)。
        base_url = _validate_base_url(base_url, STAGE_LOAD_PACKET)

    # execute=Trueの場合、実HTTP通信(upload)へ到達する前に出力先パスの
    # 整合性を検証する(Codexレビュー指摘、Critical対応: 以前はupload・
    # prompt送信・download完了後にpixel変換の段階で初めて出力先の衝突が
    # 判明し、generation_dest_pathだけが中途半端な成果物として残り得た)。
    generation_dest_path_obj = None
    converted_dest_path_obj = None
    if execute:
        if not generation_dest_path or not converted_dest_path:
            raise ComfyUIRunOnceError(
                "execute=Trueにはgeneration_dest_pathとconverted_dest_pathの両方が必要です",
                stage=STAGE_LOAD_PACKET,
                error_code="MISSING_DEST_PATH",
            )
        generation_dest_path_obj = Path(generation_dest_path)
        converted_dest_path_obj = Path(converted_dest_path)
        # 字句比較ではなく.resolve()後の実体パスで比較する(2回目のCodex
        # レビュー指摘、Critical対応: `..`や中間symlinkによる別表記で
        # 同一ファイルを指しているケースを見逃さないため。
        # scripts/panel_pixel_convert.pyの同一性チェックと同じ基準)。
        if generation_dest_path_obj.resolve() == converted_dest_path_obj.resolve():
            raise ComfyUIRunOnceError(
                "generation_dest_pathとconverted_dest_pathは同一にできません",
                stage=STAGE_LOAD_PACKET,
                error_code="DEST_PATH_COLLISION",
            )
        if not overwrite:
            if generation_dest_path_obj.exists():
                raise ComfyUIRunOnceError(
                    f"出力先が既に存在します(overwrite未指定): {generation_dest_path_obj.name}",
                    stage=STAGE_LOAD_PACKET,
                    error_code="DEST_PATH_EXISTS",
                )
            if converted_dest_path_obj.exists():
                raise ComfyUIRunOnceError(
                    f"出力先が既に存在します(overwrite未指定): {converted_dest_path_obj.name}",
                    stage=STAGE_LOAD_PACKET,
                    error_code="DEST_PATH_EXISTS",
                )

    stage = STAGE_LOAD_PACKET
    record = {
        "schema_version": SCHEMA_VERSION,
        "execution_mode": "execute" if execute else "dry-run",
        "character": expected_character,
        "panel_number": panel_no,
        "workflow_validated": False,
        "upload_validated": False,
        "prompt_submitted": False,
        "prompt_id_hash": None,
        "generation_completed": False,
        "downloaded_image_validated": False,
        "source_dimensions": None,
        "output_dimensions": None,
        "safe_area_containment_verified": False,
        "stopped_stage": None,
        "error_code": None,
    }

    try:
        # --- 1〜3節: Packet読み込み・参照解決・Workflow構築・検証(常にローカルのみ) ---
        stage = STAGE_LOAD_PACKET
        try:
            dry_run_result = opp.run_dry_run(
                packet_path, panel_no=panel_no, config_path=config_path, expected_character=expected_character, seed=seed
            )
        except opp.PilotError as e:
            # opp.PilotErrorの本文はPacket・config・参照画像のローカル絶対パスを
            # 含み得るため、そのまま転記しない(Codexレビュー指摘、Major対応)。
            # ただし、どの段階で失敗したかという機械可読な分類だけは
            # (絶対パスを含まない固定メッセージの先頭一致で)保持する
            # (3回目のCodexレビュー指摘、Minor対応: 以前はすべて
            # DRY_RUN_FAILEDへ一律に潰しており、利用者が原因を切り分け
            # られなかった)。
            raise ComfyUIRunOnceError(
                "Packet読み込み・Workflow構築・dry-run検証のいずれかに失敗しました"
                "(error_codeで大まかな失敗箇所を確認してください。詳細な原因は"
                "呼び出し元でpacket_path・config_path・参照画像の設定内容を"
                "個別に見直して切り分けてください)",
                stage=stage,
                error_code=_classify_pilot_error_code(e),
            ) from None

        stage = STAGE_RESOLVE_REFERENCE
        reference_image_path = Path(dry_run_result["reference_image_path"])

        stage = STAGE_BUILD_WORKFLOW
        workflow = dry_run_result["workflow"]
        record["workflow_validated"] = True
        record["source_dimensions"] = dict(dry_run_result["generation_resolution"])

        resolve_module = opp.load_resolve_reference_image()
        config = opp.load_config(config_path)

        if not execute:
            # dry-runはここで停止する(アップロードリクエストの構築のみ確認)。
            # upload_validatedはローカルでのリクエスト構築成否のみを示し、
            # サーバー応答の検証は一切行っていないため、常にFalseのままとする
            # (Codexレビュー指摘、Minor対応: 以前はTrueにしており、
            # 「サーバー側で検証済み」と誤解され得た)。
            cu.build_upload_request(reference_image_path, resolve_module)
            return record

        # --- execute: 実際にHTTP通信を行う経路(このセッションのテストでは
        # sessionを必ずmockして、実ソケット通信を発生させない) ---
        stage = STAGE_UPLOAD_IMAGE
        try:
            upload_response = cu.send_upload_request(base_url, reference_image_path, resolve_module, session=session)
        except cu.ComfyUIUploadError:
            # cu.ComfyUIUploadErrorをここで捕捉せずcatch-allへ流すと
            # error_code="UNEXPECTED_ERROR"になってしまい、実際の失敗段階
            # (upload応答の検証失敗)を正しく示せない(Codexレビュー指摘、
            # Minor対応)。
            raise ComfyUIRunOnceError(
                "アップロード応答の検証に失敗しました", stage=stage, error_code="UPLOAD_FAILED"
            ) from None
        record["upload_validated"] = True

        stage = STAGE_VALIDATE_UPLOAD_RESPONSE
        # send_upload_request()は内部でvalidate_upload_response()を通した
        # 結果を返すため、ここでは重ねて呼び出さない。

        stage = STAGE_APPLY_WORKFLOW_IMAGE
        workflow = cu.apply_uploaded_image_to_workflow(workflow, upload_response)
        workflow_reasons = opp.validate_workflow_shape(workflow)
        if workflow_reasons:
            raise ComfyUIRunOnceError(
                "; ".join(workflow_reasons), stage=stage, error_code="WORKFLOW_INVALID_AFTER_UPLOAD"
            )
        _validate_fixed_workflow_contract(workflow, stage)

        stage = STAGE_SUBMIT_PROMPT
        prompt_id = submit_prompt(base_url, workflow, session=session)
        record["prompt_submitted"] = True

        stage = STAGE_VALIDATE_PROMPT_ID
        record["prompt_id_hash"] = _hash_prompt_id(prompt_id)

        stage = STAGE_POLL_COMPLETION
        image_descriptor = poll_history(
            base_url,
            prompt_id,
            session=session,
            poll_interval_seconds=poll_interval_seconds,
            max_attempts=poll_max_attempts,
            total_timeout_seconds=poll_total_timeout_seconds,
            sleep_fn=sleep_fn,
        )
        record["generation_completed"] = True

        stage = STAGE_VALIDATE_HISTORY
        # image_descriptorはpoll_history()内部で検証済み。

        stage = STAGE_DOWNLOAD_IMAGE
        download_generated_image(
            base_url,
            image_descriptor,
            generation_dest_path_obj,
            session=session,
            max_bytes=download_max_bytes,
            overwrite=overwrite,
        )
        record["downloaded_image_validated"] = True

        stage = STAGE_CONVERT_PIXELS
        try:
            conversion_result = ppc.convert_generation_to_panel(
                generation_dest_path_obj,
                converted_dest_path_obj,
                panel_no=panel_no,
                generation_width=record["source_dimensions"]["width"],
                generation_height=record["source_dimensions"]["height"],
                overwrite=overwrite,
            )
        except ppc.PanelPixelConvertError as e:
            # 変換成功と画像内容の妥当性は区別する: ここは「取得した生成画像が
            # 期待寸法・形式でなかった」という変換失敗であり、safe_area内へ
            # 人物が収まっているかどうかとは無関係(そちらは常に未検証)。
            raise ComfyUIRunOnceError(f"実ピクセル変換に失敗しました: {e}", stage=stage, error_code="CONVERSION_FAILED") from None
        record["output_dimensions"] = dict(conversion_result["final_size"])
        record["safe_area_containment_verified"] = conversion_result["safe_area_containment_verified"]

        stage = STAGE_SAVE_RESULT
        return record

    except ComfyUIRunOnceError as e:
        record["stopped_stage"] = e.stage
        record["error_code"] = e.error_code
        raise
    except Exception as e:
        record["stopped_stage"] = stage
        record["error_code"] = "UNEXPECTED_ERROR"
        raise ComfyUIRunOnceError(
            f"想定外のエラーで停止しました(段階: {stage})", stage=stage, error_code="UNEXPECTED_ERROR"
        ) from None


def main():
    import argparse

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("packet", help="Manga News Packet v2 JSONファイルのパス")
    parser.add_argument("--panel-no", type=int, default=1, help="対象panel_no(既定・現時点で唯一対応: 1)")
    parser.add_argument("--character", default="ハルト", help="対象キャラクター(既定・現時点で唯一対応: ハルト)")
    parser.add_argument("--config", default=None, help="config.jsonのパス(省略時はconfig.example.json)")
    parser.add_argument("--seed", type=int, default=None, help="固定するseed値(省略時はconfigのseedを使用)")
    parser.add_argument(
        "--execute",
        action="store_true",
        help=(
            "実際にRunPod・ComfyUIへ通信する。**注意: 実行するとRunPod料金が"
            "発生し得ます。** 省略時(既定)はdry-run(通信なし)"
        ),
    )
    parser.add_argument(
        "--api-mode",
        default="pod-direct",
        choices=["pod-direct"],
        help="接続方式(現時点でpod-directのみ実装済み。serverlessは未実装)",
    )
    parser.add_argument(
        "--generation-dest", default=None, help="--execute時、生成画像(1536x640)の保存先パス"
    )
    parser.add_argument(
        "--converted-dest", default=None, help="--execute時、変換後画像(1009x345)の保存先パス"
    )
    parser.add_argument("--overwrite", action="store_true", help="出力先が既に存在する場合に上書きを許可する")
    args = parser.parse_args()

    if args.execute and not (args.generation_dest and args.converted_dest):
        print(
            "[ERROR] --executeには--generation-destと--converted-destの指定が必要です",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        result = run_once(
            args.packet,
            args.generation_dest,
            args.converted_dest,
            config_path=args.config,
            panel_no=args.panel_no,
            expected_character=args.character,
            seed=args.seed,
            execute=args.execute,
            api_mode=args.api_mode,
            overwrite=args.overwrite,
        )
    except ComfyUIRunOnceError as e:
        print(f"[ERROR] {e}(stage={e.stage}, error_code={e.error_code})", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"[OK] execution_mode={result['execution_mode']}", file=sys.stderr)


if __name__ == "__main__":
    main()
