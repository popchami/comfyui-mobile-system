#!/usr/bin/env python3
"""scripts/comfyui_run_once.py(ハルト1枚の単発実行経路オーケストレーター)
のテスト。

外部通信は一切行わない。実際にRunPod・ComfyUIへ通信するのは
`execute=True`を明示した場合の`submit_prompt()`/`poll_history()`/
`download_generated_image()`だが、テストでは常に`session`(fake)を注入し、
実際の`requests`モジュール(`comfyui_run_once.requests`)が一切呼ばれない
ことも合わせて検証する。
"""
import copy
import json
import pathlib
import sys
import tempfile
import traceback
import unittest
from unittest import mock

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

import one_panel_pilot as opp  # noqa: E402
import comfyui_upload as cu  # noqa: E402
import resolve_reference_image as rri  # noqa: E402
import panel_pixel_convert as ppc  # noqa: E402
import comfyui_run_once as cro  # noqa: E402
from test_comfyui_upload import IsolatedUploadTestCase  # noqa: E402
from test_one_panel_pilot import FIXTURE_PATH, CONFIG_PATH  # noqa: E402


def _make_generation_png_bytes(width=1536, height=640):
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        Image.new("RGB", (width, height), (12, 34, 56)).save(f, format="PNG")
        path = pathlib.Path(f.name)
    try:
        return path.read_bytes()
    finally:
        path.unlink()


class FakeResponse:
    """requests.Responseの最小限の代替。status_code/headers/json()/
    iter_content()のみを実装する。
    """

    def __init__(self, status_code=200, headers=None, json_body=None, raw_body=None):
        self.status_code = status_code
        self.headers = headers or {}
        self._json_body = json_body
        self._raw_body = raw_body if raw_body is not None else b""

    def json(self):
        if self._json_body is None:
            raise ValueError("no json body configured for this FakeResponse")
        return self._json_body

    def iter_content(self, chunk_size):
        return iter([self._raw_body]) if self._raw_body else iter([])

    def close(self):
        pass


class FakeSession:
    """post()/get()をそれぞれ差し替え可能なfake session。"""

    def __init__(self):
        self.post_calls = []
        self.get_calls = []
        self._post_handler = None
        self._get_handler = None

    def set_post_handler(self, handler):
        self._post_handler = handler

    def set_get_handler(self, handler):
        self._get_handler = handler

    def post(self, url, **kwargs):
        self.post_calls.append((url, kwargs))
        return self._post_handler(url, **kwargs)

    def get(self, url, **kwargs):
        self.get_calls.append((url, kwargs))
        return self._get_handler(url, **kwargs)


UPLOAD_RESPONSE_BODY = {"name": "haruto_uploaded.png", "subfolder": "", "type": "input"}
PROMPT_ID = "abc123-def456"
PROMPT_RESPONSE_BODY = {"prompt_id": PROMPT_ID, "node_errors": {}}
HISTORY_IMAGE = {"filename": "gen_00001.png", "subfolder": "", "type": "output"}


def _history_body(prompt_id=PROMPT_ID, images=None, status=None):
    if images is None:
        images = [HISTORY_IMAGE]
    if status is None:
        # ComfyUI本体(execution.py PromptQueue.task_done())の実際のstatus
        # 形状(status_str/completed/messages)に合わせる(4回目のCodexレビュー
        # 指摘、Major対応)。
        status = {"status_str": "success", "completed": True, "messages": []}
    return {prompt_id: {"status": status, "outputs": {cro.SAVE_IMAGE_NODE_ID: {"images": images}}}}


class RunOnceTestCase(IsolatedUploadTestCase):
    """IsolatedUploadTestCase(実PNGシグネチャ付きharuto fixture)をそのまま
    再利用する。加えて、生成画像・変換後画像用の一時ディレクトリを用意する。
    """

    def setUp(self):
        super().setUp()
        self._work_tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._work_tmpdir.cleanup)
        self.work_dir = pathlib.Path(self._work_tmpdir.name)
        self.gen_dest = self.work_dir / "gen.png"
        self.conv_dest = self.work_dir / "converted.png"

    def _default_session(self, history_images=None, history_prompt_id=PROMPT_ID, node_errors=None):
        session = FakeSession()

        def post_handler(url, **kwargs):
            if url.endswith("/upload/image"):
                return FakeResponse(
                    status_code=200,
                    headers={"Content-Type": "application/json"},
                    raw_body=json.dumps(dict(UPLOAD_RESPONSE_BODY)).encode("utf-8"),
                )
            if url.endswith("/prompt"):
                body = {"prompt_id": PROMPT_ID, "node_errors": node_errors or {}}
                return FakeResponse(
                    status_code=200,
                    headers={"Content-Type": "application/json"},
                    raw_body=json.dumps(body).encode("utf-8"),
                )
            raise AssertionError(f"unexpected POST to {url}")

        def get_handler(url, **kwargs):
            if "/history/" in url:
                body = _history_body(prompt_id=history_prompt_id, images=history_images)
                return FakeResponse(
                    status_code=200,
                    headers={"Content-Type": "application/json"},
                    raw_body=json.dumps(body).encode("utf-8"),
                )
            if "/view" in url:
                return FakeResponse(
                    status_code=200,
                    headers={"Content-Type": "image/png"},
                    raw_body=_make_generation_png_bytes(),
                )
            raise AssertionError(f"unexpected GET to {url}")

        session.set_post_handler(post_handler)
        session.set_get_handler(get_handler)
        return session

    def _run_execute(self, session, **kwargs):
        kwargs.setdefault("base_url", "https://fake-pod.example")
        return cro.run_once(
            str(FIXTURE_PATH),
            str(self.gen_dest),
            str(self.conv_dest),
            config_path=str(CONFIG_PATH),
            execute=True,
            session=session,
            sleep_fn=lambda s: None,
            **kwargs,
        )


class NormalFlowTest(RunOnceTestCase):
    def test_full_execute_flow_succeeds(self):
        # 1: 正常な単発フロー
        session = self._default_session()
        result = self._run_execute(session)
        self.assertEqual(result["execution_mode"], "execute")
        self.assertTrue(result["workflow_validated"])
        self.assertTrue(result["upload_validated"])
        self.assertTrue(result["prompt_submitted"])
        self.assertTrue(result["generation_completed"])
        self.assertTrue(result["downloaded_image_validated"])
        self.assertEqual(result["output_dimensions"], {"width": 1009, "height": 345})
        self.assertIsNone(result["stopped_stage"])
        self.assertIsNone(result["error_code"])

    def test_upload_called_exactly_once(self):
        # 3: uploadが1回だけ
        session = self._default_session()
        self._run_execute(session)
        upload_calls = [c for c in session.post_calls if c[0].endswith("/upload/image")]
        self.assertEqual(len(upload_calls), 1)

    def test_prompt_submitted_exactly_once(self):
        # 4: prompt送信が1回だけ
        session = self._default_session()
        self._run_execute(session)
        prompt_calls = [c for c in session.post_calls if c[0].endswith("/prompt")]
        self.assertEqual(len(prompt_calls), 1)

    def test_download_called_exactly_once(self):
        # 6: downloadが1回だけ
        session = self._default_session()
        self._run_execute(session)
        view_calls = [c for c in session.get_calls if "/view" in c[0]]
        self.assertEqual(len(view_calls), 1)

    def test_single_image_accepted(self):
        # 7: 生成画像が1枚だけ採用される
        session = self._default_session(history_images=[HISTORY_IMAGE])
        result = self._run_execute(session)
        self.assertTrue(result["downloaded_image_validated"])

    def test_final_output_is_1009x345(self):
        # 21: 最終出力1009×345
        session = self._default_session()
        self._run_execute(session)
        with Image.open(self.conv_dest) as img:
            self.assertEqual(img.size, (1009, 345))

    def test_safe_area_flag_is_false(self):
        # 22: safe_area_containment_verified=false
        session = self._default_session()
        result = self._run_execute(session)
        self.assertFalse(result["safe_area_containment_verified"])

    def test_no_stray_temp_files_left(self):
        # 30: 一時ファイルをリポジトリへ残さない(作業ディレクトリのみ確認)
        session = self._default_session()
        self._run_execute(session)
        remaining = sorted(p.name for p in self.work_dir.iterdir())
        self.assertEqual(remaining, sorted(["gen.png", "converted.png"]))


class DryRunTest(RunOnceTestCase):
    def test_dry_run_makes_zero_http_calls(self):
        # 2 / 27: dry-runでHTTP呼び出し0回、execute指定なしでは通信不能
        session = FakeSession()
        session.set_post_handler(lambda url, **kw: (_ for _ in ()).throw(AssertionError("should not POST")))
        session.set_get_handler(lambda url, **kw: (_ for _ in ()).throw(AssertionError("should not GET")))
        result = cro.run_once(str(FIXTURE_PATH), str(self.gen_dest), str(self.conv_dest), config_path=str(CONFIG_PATH), session=session)
        self.assertEqual(result["execution_mode"], "dry-run")
        self.assertEqual(session.post_calls, [])
        self.assertEqual(session.get_calls, [])

    def test_dry_run_touches_no_real_requests_module(self):
        # 28: テスト中の実ネットワーク通信0回
        with mock.patch("comfyui_run_once.requests.post") as real_post, mock.patch(
            "comfyui_run_once.requests.get"
        ) as real_get:
            cro.run_once(str(FIXTURE_PATH), str(self.gen_dest), str(self.conv_dest), config_path=str(CONFIG_PATH))
            self.assertFalse(real_post.called)
            self.assertFalse(real_get.called)


class RejectionTest(RunOnceTestCase):
    def test_multiple_images_rejected(self):
        # 8: 複数画像を拒否
        session = self._default_session(history_images=[HISTORY_IMAGE, dict(HISTORY_IMAGE, filename="second.png")])
        with self.assertRaises(cro.ComfyUIRunOnceError) as ctx:
            self._run_execute(session)
        self.assertEqual(ctx.exception.error_code, "MULTIPLE_IMAGES")
        self.assertEqual(ctx.exception.stage, cro.STAGE_VALIDATE_HISTORY)

    def test_zero_images_rejected(self):
        # 9: 画像0枚を拒否
        session = self._default_session(history_images=[])
        with self.assertRaises(cro.ComfyUIRunOnceError) as ctx:
            self._run_execute(session)
        self.assertEqual(ctx.exception.error_code, "NO_IMAGES")

    def test_node_errors_rejected_before_polling(self):
        # 10 / 29: node_errorsを拒否、途中失敗後に後続HTTP処理を呼ばない
        session = self._default_session(node_errors={"36": ["some error"]})
        with self.assertRaises(cro.ComfyUIRunOnceError) as ctx:
            self._run_execute(session)
        self.assertEqual(ctx.exception.error_code, "NODE_ERRORS")
        self.assertEqual(session.get_calls, [])  # historyへも/viewへも一切到達していない

    def test_invalid_prompt_id_rejected(self):
        # 11: 不正prompt_idを拒否
        session = self._default_session()

        def bad_post_handler(url, **kwargs):
            if url.endswith("/upload/image"):
                return FakeResponse(
                    status_code=200,
                    headers={"Content-Type": "application/json"},
                    raw_body=json.dumps(dict(UPLOAD_RESPONSE_BODY)).encode("utf-8"),
                )
            if url.endswith("/prompt"):
                body = {"prompt_id": "not a safe id!!", "node_errors": {}}
                return FakeResponse(
                    status_code=200,
                    headers={"Content-Type": "application/json"},
                    raw_body=json.dumps(body).encode("utf-8"),
                )
            raise AssertionError("unexpected")

        session.set_post_handler(bad_post_handler)
        with self.assertRaises(cro.ComfyUIRunOnceError) as ctx:
            self._run_execute(session)
        self.assertEqual(ctx.exception.error_code, "INVALID_PROMPT_ID")

    def test_prompt_id_mismatch_never_accepted_eventually_times_out(self):
        # 12: prompt_id不一致を拒否(該当history entryが見つからないため
        # 最終的にPOLL_TIMEOUTとなる。誤って別prompt_idのentryを採用しない)
        session = self._default_session(history_prompt_id="some-other-prompt-id")
        with self.assertRaises(cro.ComfyUIRunOnceError) as ctx:
            self._run_execute(session, poll_max_attempts=2, poll_total_timeout_seconds=10.0)
        self.assertEqual(ctx.exception.error_code, "POLL_TIMEOUT")

    def test_poll_timeout_bounded_by_max_attempts(self):
        # 5 / 13: pollが設定上限を超えない、poll timeout
        session = self._default_session(history_images=None)

        def never_found_get_handler(url, **kwargs):
            if "/history/" in url:
                body = {}  # 該当prompt_idのentryが常に存在しない
                return FakeResponse(
                    status_code=200,
                    headers={"Content-Type": "application/json"},
                    raw_body=json.dumps(body).encode("utf-8"),
                )
            raise AssertionError(f"unexpected GET to {url}")

        session.set_get_handler(never_found_get_handler)
        with self.assertRaises(cro.ComfyUIRunOnceError) as ctx:
            self._run_execute(session, poll_max_attempts=3, poll_total_timeout_seconds=100.0)
        self.assertEqual(ctx.exception.error_code, "POLL_TIMEOUT")
        history_calls = [c for c in session.get_calls if "/history/" in c[0]]
        self.assertEqual(len(history_calls), 3)

    def test_http_error_status_rejected(self):
        # 14: HTTPエラー
        session = self._default_session()
        original_get_handler = session._get_handler

        def error_get_handler(url, **kwargs):
            if "/history/" in url:
                return FakeResponse(status_code=500)
            return original_get_handler(url, **kwargs)

        session.set_get_handler(error_get_handler)
        with self.assertRaises(cro.ComfyUIRunOnceError) as ctx:
            self._run_execute(session)
        self.assertEqual(ctx.exception.error_code, "HISTORY_HTTP_ERROR")

    def test_invalid_json_rejected(self):
        # 15: 不正JSON
        session = self._default_session()
        original_get_handler = session._get_handler

        def bad_json_get_handler(url, **kwargs):
            if "/history/" in url:
                return FakeResponse(
                    status_code=200,
                    headers={"Content-Type": "application/json"},
                    raw_body=b"{not valid json",
                )
            return original_get_handler(url, **kwargs)

        session.set_get_handler(bad_json_get_handler)
        with self.assertRaises(cro.ComfyUIRunOnceError) as ctx:
            self._run_execute(session)
        self.assertEqual(ctx.exception.error_code, "HISTORY_RESPONSE_INVALID")

    def test_invalid_content_type_rejected(self):
        # 16: 不正Content-Type
        session = self._default_session()
        original_get_handler = session._get_handler

        def bad_content_type_handler(url, **kwargs):
            if "/history/" in url:
                return FakeResponse(
                    status_code=200,
                    headers={"Content-Type": "text/html"},
                    raw_body=json.dumps(_history_body()).encode("utf-8"),
                )
            return original_get_handler(url, **kwargs)

        session.set_get_handler(bad_content_type_handler)
        with self.assertRaises(cro.ComfyUIRunOnceError) as ctx:
            self._run_execute(session)
        self.assertEqual(ctx.exception.error_code, "HISTORY_RESPONSE_INVALID")

    def test_redirect_rejected(self):
        # 17: redirect先ホスト不一致(すべてのredirectを一律拒否)
        session = self._default_session()
        original_get_handler = session._get_handler

        def redirect_get_handler(url, **kwargs):
            if "/history/" in url:
                return FakeResponse(status_code=302, headers={"Location": "https://evil.example/steal"})
            return original_get_handler(url, **kwargs)

        session.set_get_handler(redirect_get_handler)
        with self.assertRaises(cro.ComfyUIRunOnceError) as ctx:
            self._run_execute(session)
        self.assertEqual(ctx.exception.error_code, "HISTORY_REDIRECT")

    def test_download_size_limit_exceeded_rejected(self):
        # 18: ダウンロード上限超過
        session = self._default_session()
        original_get_handler = session._get_handler

        def oversized_get_handler(url, **kwargs):
            if "/view" in url:
                return FakeResponse(
                    status_code=200,
                    headers={"Content-Type": "image/png"},
                    raw_body=cu.PNG_SIGNATURE + b"\x00" * 100,
                )
            return original_get_handler(url, **kwargs)

        session.set_get_handler(oversized_get_handler)
        with self.assertRaises(cro.ComfyUIRunOnceError) as ctx:
            self._run_execute(session, download_max_bytes=50)
        self.assertEqual(ctx.exception.error_code, "DOWNLOAD_TOO_LARGE")

    def test_download_png_signature_invalid_rejected(self):
        # 19: PNGシグネチャ不正(HTMLエラーページ等を画像として保存しない)
        session = self._default_session()
        original_get_handler = session._get_handler

        def html_error_page_handler(url, **kwargs):
            if "/view" in url:
                return FakeResponse(
                    status_code=200,
                    headers={"Content-Type": "image/png"},
                    raw_body=b"<html><body>not really a png</body></html>",
                )
            return original_get_handler(url, **kwargs)

        session.set_get_handler(html_error_page_handler)
        with self.assertRaises(cro.ComfyUIRunOnceError) as ctx:
            self._run_execute(session)
        self.assertEqual(ctx.exception.error_code, "DOWNLOAD_NOT_PNG")
        self.assertFalse(self.gen_dest.exists())

    def test_wrong_generation_dimensions_rejected(self):
        # 20: 1536×640以外の生成画像を拒否
        session = self._default_session()
        original_get_handler = session._get_handler

        def wrong_size_view_handler(url, **kwargs):
            if "/view" in url:
                return FakeResponse(
                    status_code=200,
                    headers={"Content-Type": "image/png"},
                    raw_body=_make_generation_png_bytes(width=800, height=600),
                )
            return original_get_handler(url, **kwargs)

        session.set_get_handler(wrong_size_view_handler)
        with self.assertRaises(cro.ComfyUIRunOnceError) as ctx:
            self._run_execute(session)
        self.assertEqual(ctx.exception.stage, cro.STAGE_CONVERT_PIXELS)
        self.assertEqual(ctx.exception.error_code, "CONVERSION_FAILED")
        self.assertFalse(self.conv_dest.exists())

    def test_non_haruto_character_rejected(self):
        # 24: ハルト以外を拒否
        with self.assertRaises(cro.ComfyUIRunOnceError) as ctx:
            cro.run_once(str(FIXTURE_PATH), str(self.gen_dest), str(self.conv_dest), expected_character="ナツキ")
        self.assertEqual(ctx.exception.error_code, "UNSUPPORTED_CHARACTER")

    def test_non_panel_1_rejected(self):
        # 25: panel 1以外を拒否
        with self.assertRaises(cro.ComfyUIRunOnceError) as ctx:
            cro.run_once(str(FIXTURE_PATH), str(self.gen_dest), str(self.conv_dest), panel_no=2)
        self.assertEqual(ctx.exception.error_code, "UNSUPPORTED_PANEL_NO")

    def test_batch_size_not_one_rejected_on_revalidation(self):
        # 26: batch_size 1以外を拒否(アップロード後の再検証で検出)
        session = self._default_session()
        real_run_dry_run = opp.run_dry_run

        def patched_run_dry_run(*args, **kwargs):
            result = real_run_dry_run(*args, **kwargs)
            result = copy.deepcopy(result)
            result["workflow"]["9"]["inputs"]["batch_size"] = 4
            return result

        with mock.patch.object(opp, "run_dry_run", side_effect=patched_run_dry_run):
            with self.assertRaises(cro.ComfyUIRunOnceError) as ctx:
                self._run_execute(session)
        self.assertEqual(ctx.exception.stage, cro.STAGE_APPLY_WORKFLOW_IMAGE)
        self.assertEqual(ctx.exception.error_code, "WORKFLOW_INVALID_AFTER_UPLOAD")
        # batch_size不正の時点で停止し、prompt送信へは進まない。
        prompt_calls = [c for c in session.post_calls if c[0].endswith("/prompt")]
        self.assertEqual(prompt_calls, [])

    def test_serverless_api_mode_rejected_before_any_network_call(self):
        session = FakeSession()
        session.set_post_handler(lambda url, **kw: (_ for _ in ()).throw(AssertionError("should not POST")))
        session.set_get_handler(lambda url, **kw: (_ for _ in ()).throw(AssertionError("should not GET")))
        with self.assertRaises(cro.ComfyUIRunOnceError) as ctx:
            cro.run_once(
                str(FIXTURE_PATH),
                str(self.gen_dest),
                str(self.conv_dest),
                execute=True,
                api_mode="serverless",
                base_url="https://fake-pod.example",
                session=session,
            )
        self.assertEqual(ctx.exception.error_code, "UNSUPPORTED_API_MODE")

    def test_missing_base_url_rejected_before_any_network_call(self):
        session = FakeSession()
        session.set_post_handler(lambda url, **kw: (_ for _ in ()).throw(AssertionError("should not POST")))
        session.set_get_handler(lambda url, **kw: (_ for _ in ()).throw(AssertionError("should not GET")))
        with mock.patch.dict("os.environ", {}, clear=False):
            import os as _os

            _os.environ.pop("RUNPOD_ENDPOINT_URL", None)
            with self.assertRaises(cro.ComfyUIRunOnceError) as ctx:
                cro.run_once(
                    str(FIXTURE_PATH), str(self.gen_dest), str(self.conv_dest), execute=True, session=session
                )
        self.assertEqual(ctx.exception.error_code, "MISSING_BASE_URL")

    def _run_execute_with_mutated_workflow(self, mutate_fn):
        session = self._default_session()
        real_run_dry_run = opp.run_dry_run

        def patched_run_dry_run(*args, **kwargs):
            result = real_run_dry_run(*args, **kwargs)
            result = copy.deepcopy(result)
            mutate_fn(result["workflow"])
            return result

        with mock.patch.object(opp, "run_dry_run", side_effect=patched_run_dry_run):
            with self.assertRaises(cro.ComfyUIRunOnceError) as ctx:
                self._run_execute(session)
        prompt_calls = [c for c in session.post_calls if c[0].endswith("/prompt")]
        self.assertEqual(prompt_calls, [])
        return ctx.exception

    def test_node_12_not_save_image_rejected(self):
        # Review B指摘1(Major)の回帰テスト: node 12がSaveImage以外へ
        # 変更されても、以前は送信直前検証をすり抜けていた。
        def mutate(workflow):
            workflow["12"]["class_type"] = "PreviewImage"

        exc = self._run_execute_with_mutated_workflow(mutate)
        self.assertEqual(exc.error_code, "WORKFLOW_CONTRACT_MISMATCH")

    def test_node_1_not_checkpoint_loader_rejected(self):
        # Review B round 2指摘1(Major)の回帰テスト: 以前は
        # EXPECTED_NODE_CLASS_TYPESがnode "1"/"6"/"8"を網羅しておらず、
        # これらのclass_type改変が送信直前検証をすり抜けていた。
        def mutate(workflow):
            workflow["1"]["class_type"] = "UnetLoaderGGUF"

        exc = self._run_execute_with_mutated_workflow(mutate)
        self.assertEqual(exc.error_code, "WORKFLOW_CONTRACT_MISMATCH")

    def test_duplicate_save_image_node_rejected(self):
        # Review B指摘1(Major)の回帰テスト: node 12以外にもSaveImageが
        # 存在する場合、「生成1枚」という前提が崩れ得るため拒否する。
        def mutate(workflow):
            workflow["99"] = copy.deepcopy(workflow["12"])

        exc = self._run_execute_with_mutated_workflow(mutate)
        self.assertEqual(exc.error_code, "WORKFLOW_CONTRACT_MISMATCH")

    def test_wrong_empty_latent_image_dimensions_rejected(self):
        # Review B指摘2(Major)の回帰テスト: EmptyLatentImageの
        # width/heightがこのpilotの固定契約(1536x640)と異なる場合に拒否する。
        def mutate(workflow):
            workflow["9"]["inputs"]["width"] = 1024
            workflow["9"]["inputs"]["height"] = 1024

        exc = self._run_execute_with_mutated_workflow(mutate)
        self.assertEqual(exc.error_code, "WORKFLOW_CONTRACT_MISMATCH")

    def test_history_image_type_temp_rejected_for_save_image_output(self):
        # Review B指摘5(Major)の回帰テスト: ComfyUI本体のSaveImageは
        # 常にtype="output"で書き出すため、SaveImageノードの出力記述で
        # type="temp"/"input"は不正な応答として拒否する。
        session = self._default_session(
            history_images=[{"filename": "gen_00001.png", "subfolder": "", "type": "temp"}]
        )
        with self.assertRaises(cro.ComfyUIRunOnceError) as ctx:
            self._run_execute(session)
        self.assertEqual(ctx.exception.error_code, "HISTORY_IMAGE_INVALID")

    def test_history_status_missing_entirely_rejected(self):
        # Review B指摘3(Major)の回帰テスト: ComfyUI本体は常にstatusキーを
        # 含むため(execution.py PromptQueue.task_done())、statusキー自体が
        # 欠損した応答は不正として拒否する(以前はoutputsのみで成功扱い)。
        session = self._default_session()
        original_get_handler = session._get_handler

        def get_handler(url, **kwargs):
            if "/history/" in url:
                body = {PROMPT_ID: {"outputs": {cro.SAVE_IMAGE_NODE_ID: {"images": [HISTORY_IMAGE]}}}}
                return FakeResponse(
                    status_code=200,
                    headers={"Content-Type": "application/json"},
                    raw_body=json.dumps(body).encode("utf-8"),
                )
            return original_get_handler(url, **kwargs)

        session.set_get_handler(get_handler)
        with self.assertRaises(cro.ComfyUIRunOnceError) as ctx:
            self._run_execute(session)
        self.assertEqual(ctx.exception.error_code, "GENERATION_FAILED")

    def test_history_status_completed_false_rejected(self):
        session = self._default_session(
            history_images=None,
        )
        original_get_handler = session._get_handler

        def get_handler(url, **kwargs):
            if "/history/" in url:
                body = _history_body(status={"status_str": "success", "completed": False, "messages": []})
                return FakeResponse(
                    status_code=200,
                    headers={"Content-Type": "application/json"},
                    raw_body=json.dumps(body).encode("utf-8"),
                )
            return original_get_handler(url, **kwargs)

        session.set_get_handler(get_handler)
        with self.assertRaises(cro.ComfyUIRunOnceError) as ctx:
            self._run_execute(session)
        self.assertEqual(ctx.exception.error_code, "GENERATION_FAILED")

    def test_history_entry_explicit_null_rejected(self):
        # Review B指摘4(Minor)の回帰テスト: `{prompt_id: null}`のような
        # キーは存在するが値がnullの応答を、キー欠損(=待機継続)と区別して
        # 不正な応答として拒否する。
        session = self._default_session()
        original_get_handler = session._get_handler

        def get_handler(url, **kwargs):
            if "/history/" in url:
                body = {PROMPT_ID: None}
                return FakeResponse(
                    status_code=200,
                    headers={"Content-Type": "application/json"},
                    raw_body=json.dumps(body).encode("utf-8"),
                )
            return original_get_handler(url, **kwargs)

        session.set_get_handler(get_handler)
        with self.assertRaises(cro.ComfyUIRunOnceError) as ctx:
            self._run_execute(session, poll_max_attempts=2, poll_total_timeout_seconds=10.0)
        self.assertEqual(ctx.exception.error_code, "HISTORY_ENTRY_INVALID")


class SecretLeakTest(RunOnceTestCase):
    def test_no_secrets_or_paths_leak_on_success(self):
        # 23: URL、トークン、prompt_id、絶対パスがログ・例外・結果へ露出しない(正常系)
        secret_endpoint = "https://secret-pod-xyz789.proxy.runpod.net"
        secret_api_key = "sk-super-secret-runpod-key-00000"
        session = self._default_session()
        with mock.patch.dict("os.environ", {"RUNPOD_API_KEY": secret_api_key}):
            result = cro.run_once(
                str(FIXTURE_PATH),
                str(self.gen_dest),
                str(self.conv_dest),
                config_path=str(CONFIG_PATH),
                execute=True,
                base_url=secret_endpoint,
                session=session,
                sleep_fn=lambda s: None,
            )
        serialized = json.dumps(result, ensure_ascii=False)
        self.assertNotIn(secret_endpoint, serialized)
        self.assertNotIn(secret_api_key, serialized)
        self.assertNotIn(PROMPT_ID, serialized)
        self.assertNotIn(str(self.work_dir), serialized)
        self.assertNotIn(str(ROOT), serialized)

    def test_no_secrets_leak_via_exception_chain_on_failure(self):
        secret_endpoint = "https://secret-pod-xyz789.proxy.runpod.net"
        secret_api_key = "sk-super-secret-runpod-key-00000"
        session = self._default_session()
        original_get_handler = session._get_handler

        def failing_handler(url, **kwargs):
            if "/history/" in url:
                return FakeResponse(status_code=500)
            return original_get_handler(url, **kwargs)

        session.set_get_handler(failing_handler)
        with mock.patch.dict("os.environ", {"RUNPOD_API_KEY": secret_api_key}):
            with self.assertRaises(cro.ComfyUIRunOnceError) as ctx:
                self._run_execute(session, base_url=secret_endpoint)

        self.assertNotIn(secret_api_key, str(ctx.exception))
        self.assertNotIn(secret_endpoint, str(ctx.exception))
        tb_text = "".join(
            traceback.format_exception(type(ctx.exception), ctx.exception, ctx.exception.__traceback__)
        )
        self.assertNotIn(secret_api_key, tb_text)


class StrictTypeAndDestPathValidationTest(RunOnceTestCase):
    """1回目のCodexレビュー指摘(Finding 1・Critical / Finding 9・Major)の
    回帰テスト: execute/overwrite/panel_noの厳格なbool検証、および
    出力先パスの衝突・既存チェックがHTTP通信より前に行われることを確認する。
    """

    def _blocking_session(self):
        session = FakeSession()
        session.set_post_handler(lambda url, **kw: (_ for _ in ()).throw(AssertionError("should not POST")))
        session.set_get_handler(lambda url, **kw: (_ for _ in ()).throw(AssertionError("should not GET")))
        return session

    def test_truthy_non_bool_execute_rejected(self):
        session = self._blocking_session()
        with self.assertRaises(cro.ComfyUIRunOnceError) as ctx:
            cro.run_once(
                str(FIXTURE_PATH),
                str(self.gen_dest),
                str(self.conv_dest),
                config_path=str(CONFIG_PATH),
                execute="false",
                base_url="https://fake-pod.example",
                session=session,
            )
        self.assertEqual(ctx.exception.error_code, "INVALID_EXECUTE_TYPE")
        self.assertEqual(session.post_calls, [])

    def test_non_bool_overwrite_rejected(self):
        session = self._blocking_session()
        with self.assertRaises(cro.ComfyUIRunOnceError) as ctx:
            cro.run_once(
                str(FIXTURE_PATH),
                str(self.gen_dest),
                str(self.conv_dest),
                config_path=str(CONFIG_PATH),
                execute=True,
                overwrite=1,
                base_url="https://fake-pod.example",
                session=session,
            )
        self.assertEqual(ctx.exception.error_code, "INVALID_OVERWRITE_TYPE")
        self.assertEqual(session.post_calls, [])

    def test_bool_panel_no_rejected_even_though_equal_to_one(self):
        session = self._blocking_session()
        with self.assertRaises(cro.ComfyUIRunOnceError) as ctx:
            cro.run_once(
                str(FIXTURE_PATH),
                str(self.gen_dest),
                str(self.conv_dest),
                config_path=str(CONFIG_PATH),
                panel_no=True,
                execute=True,
                base_url="https://fake-pod.example",
                session=session,
            )
        self.assertEqual(ctx.exception.error_code, "UNSUPPORTED_PANEL_NO")
        self.assertEqual(session.post_calls, [])

    def test_dest_path_collision_rejected_before_any_network_call(self):
        session = self._blocking_session()
        with self.assertRaises(cro.ComfyUIRunOnceError) as ctx:
            cro.run_once(
                str(FIXTURE_PATH),
                str(self.gen_dest),
                str(self.gen_dest),
                config_path=str(CONFIG_PATH),
                execute=True,
                base_url="https://fake-pod.example",
                session=session,
            )
        self.assertEqual(ctx.exception.error_code, "DEST_PATH_COLLISION")
        self.assertEqual(session.post_calls, [])

    def test_existing_dest_path_rejected_before_any_network_call_without_overwrite(self):
        session = self._blocking_session()
        self.gen_dest.write_bytes(b"stale")
        with self.assertRaises(cro.ComfyUIRunOnceError) as ctx:
            cro.run_once(
                str(FIXTURE_PATH),
                str(self.gen_dest),
                str(self.conv_dest),
                config_path=str(CONFIG_PATH),
                execute=True,
                base_url="https://fake-pod.example",
                session=session,
            )
        self.assertEqual(ctx.exception.error_code, "DEST_PATH_EXISTS")
        self.assertEqual(session.post_calls, [])
        # 絶対パスがメッセージに含まれない(basenameのみ)。
        self.assertNotIn(str(self.work_dir), str(ctx.exception))

    def test_dry_run_upload_validated_is_false(self):
        # Finding 13: dry-runはローカルのリクエスト構築のみを行い、
        # サーバー応答は一切検証していないため、upload_validatedはFalseのまま。
        result = cro.run_once(str(FIXTURE_PATH), str(self.gen_dest), str(self.conv_dest), config_path=str(CONFIG_PATH))
        self.assertFalse(result["upload_validated"])

    def test_pilot_error_message_does_not_leak_absolute_path(self):
        # Finding 10: Packet読み込み失敗時、opp.PilotErrorの生メッセージ
        # (絶対パスを含み得る)をそのまま転記しない。
        missing_packet_path = self.work_dir / "does-not-exist.json"
        with self.assertRaises(cro.ComfyUIRunOnceError) as ctx:
            cro.run_once(str(missing_packet_path), str(self.gen_dest), str(self.conv_dest), config_path=str(CONFIG_PATH))
        # error_codeはPilotErrorのメッセージ先頭パターンから分類される
        # (絶対パスを含まない機械可読な分類、Finding 8の回帰テスト)。
        self.assertEqual(ctx.exception.error_code, "PACKET_NOT_FOUND")
        self.assertNotIn(str(missing_packet_path), str(ctx.exception))

    def test_upload_response_error_wrapped_with_upload_stage(self):
        # Finding 12: cu.ComfyUIUploadErrorはUNEXPECTED_ERRORへ落とさず、
        # upload段階のエラーとして正しく属性づけする。
        session = self._default_session()

        def bad_upload_post_handler(url, **kwargs):
            if url.endswith("/upload/image"):
                return FakeResponse(status_code=200, headers={"Content-Type": "text/html"}, raw_body=b"<html/>")
            raise AssertionError(f"unexpected POST to {url}")

        session.set_post_handler(bad_upload_post_handler)
        with self.assertRaises(cro.ComfyUIRunOnceError) as ctx:
            self._run_execute(session)
        self.assertEqual(ctx.exception.error_code, "UPLOAD_FAILED")
        self.assertEqual(ctx.exception.stage, cro.STAGE_UPLOAD_IMAGE)


class BaseUrlValidationTest(unittest.TestCase):
    """Finding 2(Critical)の回帰テスト: base_urlのuserinfo・query・
    fragment・http scheme・ホスト名欠落・末尾パスをすべて拒否する。
    """

    def _blocking_session(self):
        session = FakeSession()
        session.set_post_handler(lambda url, **kw: (_ for _ in ()).throw(AssertionError("should not POST")))
        return session

    def test_userinfo_rejected(self):
        session = self._blocking_session()
        with self.assertRaises(cro.ComfyUIRunOnceError) as ctx:
            cro.submit_prompt("https://attacker:secretpass@evil.example", {"1": {}}, session=session)
        self.assertEqual(ctx.exception.error_code, "INVALID_BASE_URL")
        self.assertEqual(session.post_calls, [])

    def test_http_scheme_rejected(self):
        session = self._blocking_session()
        with self.assertRaises(cro.ComfyUIRunOnceError) as ctx:
            cro.submit_prompt("http://fake-pod.example", {"1": {}}, session=session)
        self.assertEqual(ctx.exception.error_code, "INVALID_BASE_URL")

    def test_query_rejected(self):
        session = self._blocking_session()
        with self.assertRaises(cro.ComfyUIRunOnceError) as ctx:
            cro.submit_prompt("https://fake-pod.example?x=1", {"1": {}}, session=session)
        self.assertEqual(ctx.exception.error_code, "INVALID_BASE_URL")

    def test_fragment_rejected(self):
        session = self._blocking_session()
        with self.assertRaises(cro.ComfyUIRunOnceError) as ctx:
            cro.submit_prompt("https://fake-pod.example#frag", {"1": {}}, session=session)
        self.assertEqual(ctx.exception.error_code, "INVALID_BASE_URL")

    def test_trailing_path_rejected(self):
        session = self._blocking_session()
        with self.assertRaises(cro.ComfyUIRunOnceError) as ctx:
            cro.submit_prompt("https://fake-pod.example/some/path", {"1": {}}, session=session)
        self.assertEqual(ctx.exception.error_code, "INVALID_BASE_URL")

    def test_missing_hostname_rejected(self):
        session = self._blocking_session()
        with self.assertRaises(cro.ComfyUIRunOnceError) as ctx:
            cro.submit_prompt("https://", {"1": {}}, session=session)
        self.assertEqual(ctx.exception.error_code, "INVALID_BASE_URL")


class NodeErrorsAndHistoryStatusRegressionTest(RunOnceTestCase):
    """Finding 11(node_errorsの型)・Finding 8(historyのstatus)の回帰テスト。"""

    def test_non_dict_node_errors_rejected(self):
        # 以前はnode_errors=[]のような非dict値もfalsyとして通過していた。
        session = self._default_session()
        original_post_handler = session._post_handler

        def post_handler(url, **kwargs):
            if url.endswith("/prompt"):
                body = {"prompt_id": PROMPT_ID, "node_errors": []}
                return FakeResponse(
                    status_code=200,
                    headers={"Content-Type": "application/json"},
                    raw_body=json.dumps(body).encode("utf-8"),
                )
            return original_post_handler(url, **kwargs)

        session.set_post_handler(post_handler)
        with self.assertRaises(cro.ComfyUIRunOnceError) as ctx:
            self._run_execute(session)
        self.assertEqual(ctx.exception.error_code, "INVALID_NODE_ERRORS")

    def test_explicit_null_node_errors_rejected(self):
        # 3回目のCodexレビュー指摘、Major対応の回帰テスト: キー欠損と
        # 明示的な`"node_errors": null`は区別され、後者も型違反として拒否する。
        session = self._default_session()
        original_post_handler = session._post_handler

        def post_handler(url, **kwargs):
            if url.endswith("/prompt"):
                body = {"prompt_id": PROMPT_ID, "node_errors": None}
                return FakeResponse(
                    status_code=200,
                    headers={"Content-Type": "application/json"},
                    raw_body=json.dumps(body).encode("utf-8"),
                )
            return original_post_handler(url, **kwargs)

        session.set_post_handler(post_handler)
        with self.assertRaises(cro.ComfyUIRunOnceError) as ctx:
            self._run_execute(session)
        self.assertEqual(ctx.exception.error_code, "INVALID_NODE_ERRORS")

    def test_missing_node_errors_key_still_tolerated(self):
        # node_errorsキー自体が欠損している場合は、引き続き「エラーなし」
        # として許容される(実際のComfyUI応答スキーマが未確認のため)。
        session = self._default_session()
        original_post_handler = session._post_handler

        def post_handler(url, **kwargs):
            if url.endswith("/prompt"):
                body = {"prompt_id": PROMPT_ID}
                return FakeResponse(
                    status_code=200,
                    headers={"Content-Type": "application/json"},
                    raw_body=json.dumps(body).encode("utf-8"),
                )
            return original_post_handler(url, **kwargs)

        session.set_post_handler(post_handler)
        result = self._run_execute(session)
        self.assertTrue(result["prompt_submitted"])

    def test_status_dict_without_status_str_key_rejected(self):
        # 3回目のCodexレビュー指摘、Major対応の回帰テスト: 以前は
        # `status_str is not None and status_str != "success"`のため、
        # status_strキー自体が欠損した`status`辞書(例: `{}`)がホワイト
        # リストをすり抜けて成功扱いになっていた。
        session = self._default_session()
        original_get_handler = session._get_handler

        def get_handler(url, **kwargs):
            if "/history/" in url:
                body = {
                    PROMPT_ID: {
                        "status": {},
                        "outputs": {cro.SAVE_IMAGE_NODE_ID: {"images": [HISTORY_IMAGE]}},
                    }
                }
                return FakeResponse(
                    status_code=200,
                    headers={"Content-Type": "application/json"},
                    raw_body=json.dumps(body).encode("utf-8"),
                )
            return original_get_handler(url, **kwargs)

        session.set_get_handler(get_handler)
        with self.assertRaises(cro.ComfyUIRunOnceError) as ctx:
            self._run_execute(session)
        self.assertEqual(ctx.exception.error_code, "GENERATION_FAILED")

    def test_cancelled_status_rejected(self):
        # 以前はstatus_str=="error"以外(cancelled等)を成功扱いしていた。
        session = self._default_session()
        original_get_handler = session._get_handler

        def get_handler(url, **kwargs):
            if "/history/" in url:
                body = {
                    PROMPT_ID: {
                        "status": {"status_str": "cancelled"},
                        "outputs": {cro.SAVE_IMAGE_NODE_ID: {"images": [HISTORY_IMAGE]}},
                    }
                }
                return FakeResponse(
                    status_code=200,
                    headers={"Content-Type": "application/json"},
                    raw_body=json.dumps(body).encode("utf-8"),
                )
            return original_get_handler(url, **kwargs)

        session.set_get_handler(get_handler)
        with self.assertRaises(cro.ComfyUIRunOnceError) as ctx:
            self._run_execute(session)
        self.assertEqual(ctx.exception.error_code, "GENERATION_FAILED")


class MonotonicPollTimeoutTest(unittest.TestCase):
    """Finding 5(Major)の回帰テスト: 総timeoutは実時間(monotonic)基準で
    強制され、sleep_fnが何もしなくても、経過時間の蓄積だけで超過扱いになる。
    `run_once()`はmonotonic_fnを直接公開していないため、`poll_history()`を
    直接呼び出して検証する。
    """

    def test_total_timeout_enforced_via_monotonic_clock_even_with_noop_sleep(self):
        session = FakeSession()

        def never_found_get_handler(url, **kwargs):
            if "/history/" in url:
                return FakeResponse(
                    status_code=200,
                    headers={"Content-Type": "application/json"},
                    raw_body=json.dumps({}).encode("utf-8"),
                )
            raise AssertionError(f"unexpected GET to {url}")

        session.set_get_handler(never_found_get_handler)

        fake_clock = {"t": 0.0}

        def fake_monotonic():
            fake_clock["t"] += 50.0
            return fake_clock["t"]

        with self.assertRaises(cro.ComfyUIRunOnceError) as ctx:
            cro.poll_history(
                "https://fake-pod.example",
                PROMPT_ID,
                session=session,
                sleep_fn=lambda s: None,
                max_attempts=1000,
                total_timeout_seconds=100.0,
                monotonic_fn=fake_monotonic,
            )
        self.assertEqual(ctx.exception.error_code, "POLL_TIMEOUT")
        # monotonic_fnが50秒刻みで進むため、total_timeout=100秒なら
        # 数回のhistory呼び出しで打ち切られる(1000回には遠く届かない)。
        history_calls = [c for c in session.get_calls if "/history/" in c[0]]
        self.assertLess(len(history_calls), 10)

    def test_success_entry_arriving_after_deadline_is_rejected(self):
        # 3回目のCodexレビュー指摘、Major対応の回帰テスト: 応答本文の
        # 読み込み完了が締切を過ぎていた場合、たとえ有効なentryが得られても
        # 成功として返さず、POLL_TIMEOUTとして扱う(低速ストリーミング応答が
        # 個々のtimeout未満のまま総予算を超過するケースを見逃さないため)。
        session = FakeSession()

        def found_get_handler(url, **kwargs):
            if "/history/" in url:
                return FakeResponse(
                    status_code=200,
                    headers={"Content-Type": "application/json"},
                    raw_body=json.dumps(_history_body()).encode("utf-8"),
                )
            raise AssertionError(f"unexpected GET to {url}")

        session.set_get_handler(found_get_handler)

        # monotonic_fnは呼び出しごとに締切を大きく超えた時刻を返す
        # (=応答本文の読み込みに時間がかかったことを模す)。
        fake_clock = {"t": 0.0}

        def fake_monotonic():
            fake_clock["t"] += 1000.0
            return fake_clock["t"]

        with self.assertRaises(cro.ComfyUIRunOnceError) as ctx:
            cro.poll_history(
                "https://fake-pod.example",
                PROMPT_ID,
                session=session,
                sleep_fn=lambda s: None,
                max_attempts=10,
                total_timeout_seconds=100.0,
                monotonic_fn=fake_monotonic,
            )
        self.assertEqual(ctx.exception.error_code, "POLL_TIMEOUT")


class UploadValidatedBeforeAnyNetworkCallTest(RunOnceTestCase):
    """Finding 1(Critical、round 2)の回帰テスト: base_urlの検証は
    `/upload/image`を含むどのHTTP呼び出しよりも前に行われ、不正な
    base_url(http・userinfo混入等)ではuploadにすら到達しない。
    """

    def test_invalid_base_url_rejected_before_upload_post(self):
        session = FakeSession()
        session.set_post_handler(lambda url, **kw: (_ for _ in ()).throw(AssertionError("should not POST")))
        session.set_get_handler(lambda url, **kw: (_ for _ in ()).throw(AssertionError("should not GET")))
        with self.assertRaises(cro.ComfyUIRunOnceError) as ctx:
            cro.run_once(
                str(FIXTURE_PATH),
                str(self.gen_dest),
                str(self.conv_dest),
                config_path=str(CONFIG_PATH),
                execute=True,
                base_url="http://attacker:secretpass@evil.example",
                session=session,
            )
        self.assertEqual(ctx.exception.error_code, "INVALID_BASE_URL")
        self.assertEqual(session.post_calls, [])


class StreamReadExceptionRegressionTest(RunOnceTestCase):
    """Finding 3(Major、round 2)の回帰テスト: `stream=True`化後、応答本文の
    読み込み中に発生するrequests例外が、接続先URLを含んだまま漏れない
    ことを確認する。
    """

    def test_submit_prompt_body_read_exception_does_not_leak_url(self):
        import requests

        secret_url = "https://secret-pod.example/prompt"
        response = mock.MagicMock()
        response.status_code = 200
        response.headers = {"Content-Type": "application/json"}
        response.iter_content = mock.MagicMock(side_effect=requests.exceptions.ConnectionError(secret_url))
        session = mock.MagicMock()
        session.post.return_value = response
        with self.assertRaises(cro.ComfyUIRunOnceError) as ctx:
            cro.submit_prompt("https://fake-pod.example", {"1": {}}, session=session)
        self.assertNotIn(secret_url, str(ctx.exception))
        response.close.assert_called_once()

    def test_poll_history_body_read_exception_does_not_leak_url(self):
        import requests

        secret_url = "https://secret-pod.example/history/abc"
        response = mock.MagicMock()
        response.status_code = 200
        response.headers = {"Content-Type": "application/json"}
        response.iter_content = mock.MagicMock(side_effect=requests.exceptions.ConnectionError(secret_url))
        session = mock.MagicMock()
        session.get.return_value = response
        with self.assertRaises(cro.ComfyUIRunOnceError) as ctx:
            cro.poll_history("https://fake-pod.example", PROMPT_ID, session=session, sleep_fn=lambda s: None)
        self.assertNotIn(secret_url, str(ctx.exception))
        response.close.assert_called_once()


class DefaultSessionWiringTest(RunOnceTestCase):
    """Finding 7(Minor、round 2)の回帰テスト: session省略時、
    `_default_session()`が実際にHTTP関数から呼ばれる配線になっている
    ことを確認する(helper単体の`trust_env`確認だけでは不十分なため)。
    """

    def test_submit_prompt_uses_default_session_when_session_omitted(self):
        fake_session = mock.MagicMock()
        fake_response = mock.MagicMock()
        fake_response.status_code = 200
        fake_response.headers = {"Content-Type": "application/json"}
        fake_response.iter_content = mock.MagicMock(
            return_value=iter([json.dumps({"prompt_id": PROMPT_ID, "node_errors": {}}).encode("utf-8")])
        )
        fake_session.post.return_value = fake_response
        with mock.patch("comfyui_run_once._default_session", return_value=fake_session) as patched:
            cro.submit_prompt("https://fake-pod.example", {"1": {}})
        patched.assert_called_once()
        self.assertTrue(fake_session.post.called)

    def test_send_upload_request_uses_default_session_when_session_omitted(self):
        path = self.resolved_path()
        fake_session = mock.MagicMock()
        fake_response = mock.MagicMock()
        fake_response.status_code = 200
        fake_response.headers = {"Content-Type": "application/json"}
        fake_response.iter_content = mock.MagicMock(
            return_value=iter([json.dumps(dict(UPLOAD_RESPONSE_BODY)).encode("utf-8")])
        )
        fake_session.post.return_value = fake_response
        with mock.patch("comfyui_upload._default_session", return_value=fake_session) as patched:
            cu.send_upload_request("https://fake-pod.example", path, rri, session=None)
        patched.assert_called_once()
        self.assertTrue(fake_session.post.called)


class DefaultSessionTrustEnvTest(unittest.TestCase):
    """Finding 4(Major)の回帰テスト: session省略時に生成される内部Sessionは
    proxy環境変数・~/.netrcを継承しない(trust_env=False)。
    """

    def test_comfyui_run_once_default_session_disables_trust_env(self):
        session = cro._default_session()
        self.addCleanup(session.close)
        self.assertFalse(session.trust_env)

    def test_comfyui_upload_default_session_disables_trust_env(self):
        session = cu._default_session()
        self.addCleanup(session.close)
        self.assertFalse(session.trust_env)


if __name__ == "__main__":
    unittest.main()
