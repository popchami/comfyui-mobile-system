#!/usr/bin/env python3
"""scripts/comfyui_upload.py(ComfyUI `/upload/image`のリクエスト構築・
応答検証)のテスト。

RunPod・ComfyUIへの実通信は一切行わない。`send_upload_request()`は
`requests.post`相当をmockした`session`経由でのみ呼び出し、実ソケット
通信は発生しない。reference_image解決の隔離は、既存
tests/test_one_panel_pilot.py の`IsolatedReferenceImagesTestCase`を
そのまま再利用する(重複実装しない)。
"""
import copy
import json
import os
import pathlib
import socket
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

import one_panel_pilot as opp  # noqa: E402
import resolve_reference_image as rri  # noqa: E402
import comfyui_upload as cu  # noqa: E402
from test_one_panel_pilot import IsolatedReferenceImagesTestCase  # noqa: E402


class IsolatedUploadTestCase(IsolatedReferenceImagesTestCase):
    """IsolatedReferenceImagesTestCaseが用意する隔離済みharuto fixtureに、
    実在するPNGバイト列(先頭にPNGシグネチャを持つ)を書き込み直す。
    アップロード契約はPNGシグネチャ・サイズ等を実際に検証するため、
    親クラスのfake bytes(`b"fake-neutral-png-bytes"`)ではPNGシグネチャ
    検証に失敗してしまうための追加セットアップ。

    加えて、テスト中の実ソケット通信を包括的に禁止し(2回目のCodexレビュー
    指摘、Minor対応: 従来はrequests.post/getのmockのみで、mockし忘れた
    経路が実DNS・実TCP接続に到達する可能性を排除できていなかった)、
    RUNPOD_API_KEY・RUNPOD_ENDPOINT_URLをテストごとに隔離する(個別の
    テストがmock.patch.dictで明示的に設定した場合はそちらが優先される)。
    """

    def setUp(self):
        super().setUp()
        real_png_bytes = cu.PNG_SIGNATURE + b"\x00" * 64
        for name in ("00-neutral.png", "04-surprise-weak.png"):
            (self.root / "haruto" / "images" / name).write_bytes(real_png_bytes)

        socket_patcher = mock.patch(
            "socket.socket", side_effect=AssertionError("real socket通信がテスト中に試みられました")
        )
        socket_patcher.start()
        self.addCleanup(socket_patcher.stop)

        env_patcher = mock.patch.dict(os.environ, {}, clear=False)
        env_patcher.start()
        self.addCleanup(env_patcher.stop)
        os.environ.pop("RUNPOD_API_KEY", None)
        os.environ.pop("RUNPOD_ENDPOINT_URL", None)

    def resolved_path(self, expression="neutral", filename="00-neutral.png"):
        performer = {
            "name": "ハルト",
            "expression": expression,
            "reference_image": f"haruto/{expression}.png",
        }
        return opp.resolve_performer_reference_image(performer, rri)


class ValidateUploadSourcePathTest(IsolatedUploadTestCase):
    def test_valid_resolved_path_accepted(self):
        path = self.resolved_path()
        size = cu.validate_upload_source_path(path, rri)
        self.assertGreater(size, 0)

    def test_rejects_non_path_object(self):
        with self.assertRaises(cu.ComfyUIUploadError):
            cu.validate_upload_source_path(str(self.resolved_path()), rri)

    def test_rejects_symlink(self):
        target = self.resolved_path()
        link = self.root / "haruto" / "images" / "symlink-to-neutral.png"
        link.symlink_to(target)
        with self.assertRaises(cu.ComfyUIUploadError):
            cu.validate_upload_source_path(link, rri)

    def test_rejects_path_outside_reference_images_root(self):
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(cu.PNG_SIGNATURE + b"\x00" * 16)
            outside_path = pathlib.Path(f.name)
        try:
            with self.assertRaises(cu.ComfyUIUploadError):
                cu.validate_upload_source_path(outside_path, rri)
        finally:
            outside_path.unlink()

    def test_rejects_non_png_extension(self):
        bad = self.root / "haruto" / "images" / "not-an-image.txt"
        bad.write_bytes(cu.PNG_SIGNATURE + b"\x00" * 16)
        with self.assertRaises(cu.ComfyUIUploadError):
            cu.validate_upload_source_path(bad, rri)

    def test_rejects_missing_file(self):
        missing = self.root / "haruto" / "images" / "does-not-exist.png"
        with self.assertRaises(cu.ComfyUIUploadError):
            cu.validate_upload_source_path(missing, rri)

    def test_rejects_wrong_png_signature(self):
        bad = self.root / "haruto" / "images" / "not-real-png.png"
        bad.write_bytes(b"not a real png signature" + b"\x00" * 16)
        with self.assertRaises(cu.ComfyUIUploadError):
            cu.validate_upload_source_path(bad, rri)

    def test_rejects_oversized_file(self):
        big = self.root / "haruto" / "images" / "too-big.png"
        with mock.patch.object(cu, "MAX_UPLOAD_FILE_SIZE_BYTES", 100):
            big.write_bytes(cu.PNG_SIGNATURE + b"\x00" * 200)
            with self.assertRaises(cu.ComfyUIUploadError):
                cu.validate_upload_source_path(big, rri)

    def test_rejects_empty_file(self):
        empty = self.root / "haruto" / "images" / "empty.png"
        empty.write_bytes(b"")
        with self.assertRaises(cu.ComfyUIUploadError):
            cu.validate_upload_source_path(empty, rri)

    def test_rejects_file_not_under_known_category_structure(self):
        # Codexレビュー指摘(Major)の回帰テスト: 正本root直下(character/
        # categoryの構造を経由しない位置)へ置かれた、resolverを一切通して
        # いないファイルを拒否できること。
        rogue = self.root / "unmanifested.png"
        rogue.write_bytes(cu.PNG_SIGNATURE + b"\x00" * 32)
        with self.assertRaises(cu.ComfyUIUploadError):
            cu.validate_upload_source_path(rogue, rri)

    def test_rejects_file_directly_under_character_dir_without_category(self):
        rogue = self.root / "haruto" / "unmanifested.png"
        rogue.write_bytes(cu.PNG_SIGNATURE + b"\x00" * 32)
        with self.assertRaises(cu.ComfyUIUploadError):
            cu.validate_upload_source_path(rogue, rri)

    def test_rejects_file_in_correct_directory_but_not_registered_in_manifest(self):
        # 2回目のCodexレビュー指摘(Major)の回帰テスト: 以前はディレクトリ
        # 構造の一致だけを確認しており、character/categoryの正しい
        # ディレクトリ内に直接置かれた「manifest.jsonに登録されていない」
        # ファイル(resolverを一切通していないファイル)を見逃していた。
        rogue = self.root / "haruto" / "images" / "not-in-manifest.png"
        rogue.write_bytes(cu.PNG_SIGNATURE + b"\x00" * 32)
        with self.assertRaises(cu.ComfyUIUploadError):
            cu.validate_upload_source_path(rogue, rri)

    def test_intermediate_directory_symlink_swap_rejected_end_to_end(self):
        # 2回目のCodexレビュー指摘(Major)の回帰テスト: O_NOFOLLOWは最終
        # pathコンポーネントのシンボリックリンクは防ぐが、検証からopenまでの
        # 間に中間ディレクトリ自体がシンボリックリンクへ差し替えられる
        # レースまでは防がない。通常の(mockなしの)呼び出しでも、中間
        # ディレクトリが正本外を指すシンボリックリンクへ差し替わっている
        # 場合は拒否されることを確認する。
        import os
        import tempfile

        path = self.resolved_path()
        images_dir = self.root / "haruto" / "images"
        with tempfile.TemporaryDirectory() as outside_tmp:
            outside_dir = pathlib.Path(outside_tmp)
            (outside_dir / path.name).write_bytes(cu.PNG_SIGNATURE + b"\x00" * 999)

            backup_dir = self.root / "haruto" / "images_backup"
            images_dir.rename(backup_dir)
            try:
                os.symlink(outside_dir, images_dir)
                with self.assertRaises(cu.ComfyUIUploadError):
                    cu._read_and_verify_source_bytes(path, rri)
            finally:
                if images_dir.is_symlink() or images_dir.exists():
                    images_dir.unlink()
                backup_dir.rename(images_dir)

    def test_proc_based_realpath_check_is_independent_defense_layer(self):
        # 通常のpath-basedチェック(_is_within_root等)は、事前にシンボリック
        # リンクを差し替えてから呼び出す静的なテストでは、呼び出し時点で
        # Path.resolve()が既に差し替え後の状態を見てしまうため、新しい
        # /proc/self/fdベースのチェックの寄与を単体で証明できない。ここでは
        # 「path-basedの検証はすべて通過した後、実際のos.open()を呼ぶ
        # 直前」に中間ディレクトリを差し替えることで、実際の競合タイミングを
        # 模倣し、/proc-basedチェックが単体で実体の脱出を検出できることを
        # 確認する(2回目のCodexレビュー指摘、Major対応の直接的な検証)。
        import os
        import tempfile

        path = self.resolved_path()
        images_dir = self.root / "haruto" / "images"
        real_os_open = os.open

        with tempfile.TemporaryDirectory() as outside_tmp:
            outside_dir = pathlib.Path(outside_tmp)
            (outside_dir / path.name).write_bytes(cu.PNG_SIGNATURE + b"\x00" * 999)
            backup_dir = self.root / "haruto" / "images_backup"

            def swap_then_open(path_arg, flags):
                images_dir.rename(backup_dir)
                os.symlink(outside_dir, images_dir)
                return real_os_open(path_arg, flags)

            try:
                with mock.patch("comfyui_upload.os.open", side_effect=swap_then_open):
                    with self.assertRaises(cu.ComfyUIUploadError) as ctx:
                        cu._read_and_verify_source_bytes(path, rri)
                    self.assertIn("実体", str(ctx.exception))
            finally:
                if images_dir.is_symlink():
                    images_dir.unlink()
                    backup_dir.rename(images_dir)


class BuildUploadFilenameTest(IsolatedUploadTestCase):
    def test_deterministic_for_same_content(self):
        path = self.resolved_path()
        self.assertEqual(cu.build_upload_filename(path), cu.build_upload_filename(path))

    def test_different_for_different_content(self):
        a = self.resolved_path("neutral", "00-neutral.png")
        b = self.resolved_path("surprise-weak", "04-surprise-weak.png")
        self.assertNotEqual(cu.build_upload_filename(a), cu.build_upload_filename(b))

    def test_preserves_suffix(self):
        path = self.resolved_path()
        self.assertTrue(cu.build_upload_filename(path).endswith(".png"))


class BuildUploadRequestTest(IsolatedUploadTestCase):
    def test_builds_expected_shape_without_sending(self):
        path = self.resolved_path()
        request = cu.build_upload_request(path, rri)
        self.assertEqual(request["endpoint_path"], "/upload/image")
        self.assertEqual(request["method"], "POST")
        self.assertEqual(request["form_fields"]["overwrite"], "false")
        self.assertEqual(request["form_fields"]["type"], "input")
        self.assertGreater(request["content_length"], 0)

    def test_overwrite_true_reflected(self):
        path = self.resolved_path()
        request = cu.build_upload_request(path, rri, overwrite=True)
        self.assertEqual(request["form_fields"]["overwrite"], "true")

    def test_rejects_unknown_image_type(self):
        path = self.resolved_path()
        with self.assertRaises(cu.ComfyUIUploadError):
            cu.build_upload_request(path, rri, image_type="not-a-real-type")

    def test_request_is_json_serializable(self):
        path = self.resolved_path()
        request = cu.build_upload_request(path, rri)
        json.dumps(request)  # 例外が出なければシリアライズ可能


class ValidateUploadResponseTest(unittest.TestCase):
    def test_valid_response_accepted(self):
        validated = cu.validate_upload_response({"name": "a.png", "subfolder": "", "type": "input"})
        self.assertEqual(validated, {"name": "a.png", "subfolder": "", "type": "input"})

    def test_valid_response_with_subfolder_accepted(self):
        validated = cu.validate_upload_response({"name": "a.png", "subfolder": "sub", "type": "input"})
        self.assertEqual(validated["subfolder"], "sub")

    def test_rejects_non_dict_response(self):
        with self.assertRaises(cu.ComfyUIUploadError):
            cu.validate_upload_response(["not", "a", "dict"])

    def test_rejects_missing_name(self):
        with self.assertRaises(cu.ComfyUIUploadError):
            cu.validate_upload_response({"subfolder": "", "type": "input"})

    def test_rejects_empty_name(self):
        with self.assertRaises(cu.ComfyUIUploadError):
            cu.validate_upload_response({"name": "", "subfolder": "", "type": "input"})

    def test_rejects_path_traversal_in_name(self):
        with self.assertRaises(cu.ComfyUIUploadError):
            cu.validate_upload_response({"name": "../escape.png", "subfolder": "", "type": "input"})

    def test_rejects_absolute_path_in_name(self):
        with self.assertRaises(cu.ComfyUIUploadError):
            cu.validate_upload_response({"name": "/etc/passwd", "subfolder": "", "type": "input"})

    def test_rejects_backslash_absolute_path(self):
        with self.assertRaises(cu.ComfyUIUploadError):
            cu.validate_upload_response({"name": r"\windows\path.png", "subfolder": "", "type": "input"})

    def test_rejects_drive_letter_absolute_path(self):
        with self.assertRaises(cu.ComfyUIUploadError):
            cu.validate_upload_response({"name": r"C:\evil.png", "subfolder": "", "type": "input"})

    def test_rejects_control_characters_in_name(self):
        with self.assertRaises(cu.ComfyUIUploadError):
            cu.validate_upload_response({"name": "a\x00.png", "subfolder": "", "type": "input"})

    def test_rejects_path_traversal_in_subfolder(self):
        with self.assertRaises(cu.ComfyUIUploadError):
            cu.validate_upload_response({"name": "a.png", "subfolder": "../../etc", "type": "input"})

    def test_rejects_unknown_type(self):
        with self.assertRaises(cu.ComfyUIUploadError):
            cu.validate_upload_response({"name": "a.png", "subfolder": "", "type": "bogus"})

    def test_rejects_nested_segments_in_name(self):
        # Codexレビュー指摘(Minor)の回帰テスト: 以前はnameもsubfolderと
        # 同じsegment単位検証だったため、"nested/a.png"のような複数
        # segmentのnameを誤って受理していた。nameは単一segmentのみ許可する。
        with self.assertRaises(cu.ComfyUIUploadError):
            cu.validate_upload_response({"name": "nested/a.png", "subfolder": "", "type": "input"})

    def test_rejects_backslash_nested_segments_in_name(self):
        with self.assertRaises(cu.ComfyUIUploadError):
            cu.validate_upload_response({"name": "nested\\a.png", "subfolder": "", "type": "input"})

    def test_subfolder_with_multiple_segments_still_accepted(self):
        # subfolderは複数segmentを許可する(nameとは異なる)。
        validated = cu.validate_upload_response({"name": "a.png", "subfolder": "sub/dir", "type": "input"})
        self.assertEqual(validated["subfolder"], "sub/dir")

    def test_rejects_backslash_separator_in_subfolder(self):
        # Review B指摘(Minor)の回帰テスト: 以前はsubfolderの区切りとして
        # `\`も許容していたため、Windows風・混在区切り(`sub\dir`)が
        # そのまま`subfolder/name`形式へ混入し、nameの「バックスラッシュを
        # 1文字でも含めば拒否」という方針と一致していなかった。
        with self.assertRaises(cu.ComfyUIUploadError):
            cu.validate_upload_response({"name": "a.png", "subfolder": r"sub\dir", "type": "input"})

    def test_rejects_reserved_type_annotation_embedded_in_name(self):
        # Review B 2回目の指摘(Major)の回帰テスト: type="input"のまま、
        # nameへComfyUI予約の末尾注釈(` [output]`等)を直接埋め込むことで、
        # 検証済みのtypeとは無関係に実際にはoutputフォルダをLoadImageへ
        # 参照させられてしまっていた。
        with self.assertRaises(cu.ComfyUIUploadError):
            cu.validate_upload_response({"name": "normal.png [output]", "subfolder": "", "type": "input"})

    def test_rejects_reserved_type_annotation_embedded_in_subfolder(self):
        with self.assertRaises(cu.ComfyUIUploadError):
            cu.validate_upload_response({"name": "a.png", "subfolder": "sub [temp]", "type": "input"})

    def test_legitimate_temp_type_still_works_after_reserved_annotation_check(self):
        validated = cu.validate_upload_response({"name": "a.png", "subfolder": "", "type": "temp"})
        self.assertEqual(cu.build_load_image_value(validated), "a.png [temp]")

    def test_rejects_non_string_name(self):
        with self.assertRaises(cu.ComfyUIUploadError):
            cu.validate_upload_response({"name": 12345, "subfolder": "", "type": "input"})


class BuildLoadImageValueTest(unittest.TestCase):
    def test_no_subfolder(self):
        value = cu.build_load_image_value({"name": "a.png", "subfolder": "", "type": "input"})
        self.assertEqual(value, "a.png")

    def test_with_subfolder(self):
        value = cu.build_load_image_value({"name": "a.png", "subfolder": "sub", "type": "input"})
        self.assertEqual(value, "sub/a.png")

    def test_unvalidated_unsafe_response_rejected(self):
        # Codexレビュー指摘(Major)の回帰テスト: 引数名が`validated_response`
        # であっても、実際にはvalidate_upload_response()を通していない
        # 未検証の辞書を渡した場合、そのままLoadImageへ渡してはならない。
        with self.assertRaises(cu.ComfyUIUploadError):
            cu.build_load_image_value({"name": "../escape.png", "subfolder": "", "type": "input"})

    def test_temp_type_gets_bracket_annotation(self):
        # Review B指摘(Major)の回帰テスト: ComfyUI本体のLoadImage実装は、
        # `input`以外のtypeでは末尾に` [temp]`/` [output]`という注釈が
        # なければ既定のinputフォルダへフォールバックしてしまう。以前は
        # typeを無視しており、この注釈が付与されていなかった。
        value = cu.build_load_image_value({"name": "a.png", "subfolder": "", "type": "temp"})
        self.assertEqual(value, "a.png [temp]")

    def test_output_type_with_subfolder_gets_bracket_annotation(self):
        value = cu.build_load_image_value({"name": "a.png", "subfolder": "sub", "type": "output"})
        self.assertEqual(value, "sub/a.png [output]")

    def test_input_type_gets_no_annotation(self):
        value = cu.build_load_image_value({"name": "a.png", "subfolder": "", "type": "input"})
        self.assertNotIn("[", value)


class ApplyUploadedImageToWorkflowTest(unittest.TestCase):
    def _workflow(self):
        return {
            "36": {"class_type": "LoadImage", "inputs": {"image": "placeholder.png", "upload": "image"}},
        }

    def test_applies_validated_name(self):
        workflow = self._workflow()
        validated = {"name": "server-name.png", "subfolder": "", "type": "input"}
        updated = cu.apply_uploaded_image_to_workflow(workflow, validated)
        self.assertEqual(updated["36"]["inputs"]["image"], "server-name.png")

    def test_unvalidated_unsafe_response_not_applied(self):
        # Codexレビュー指摘(Major)の回帰テスト: 検証前のupload応答
        # (例: パストラバーサルを含むname)をそのままLoadImageへ注入できない。
        workflow = self._workflow()
        unsafe_response = {"name": "../escape.png", "subfolder": "", "type": "input"}
        with self.assertRaises(cu.ComfyUIUploadError):
            cu.apply_uploaded_image_to_workflow(workflow, unsafe_response)
        # 元workflowにも一切反映されていないこと。
        self.assertEqual(workflow["36"]["inputs"]["image"], "placeholder.png")

    def test_non_dict_workflow_rejected_cleanly(self):
        with self.assertRaises(cu.ComfyUIUploadError):
            cu.apply_uploaded_image_to_workflow([], {"name": "a.png", "subfolder": "", "type": "input"})

    def test_non_loadimage_class_type_rejected(self):
        workflow = {"36": {"class_type": "SaveImage", "inputs": {"image": "x.png"}}}
        with self.assertRaises(cu.ComfyUIUploadError):
            cu.apply_uploaded_image_to_workflow(workflow, {"name": "a.png", "subfolder": "", "type": "input"})

    def test_non_dict_inputs_rejected_cleanly_not_typeerror(self):
        # Codexレビュー指摘(Major)の回帰テスト: 以前はinputsがdictでない
        # 場合、素のTypeErrorが漏れていた。
        workflow = {"36": {"class_type": "LoadImage", "inputs": []}}
        with self.assertRaises(cu.ComfyUIUploadError):
            cu.apply_uploaded_image_to_workflow(workflow, {"name": "a.png", "subfolder": "", "type": "input"})

    def test_inputs_missing_image_field_rejected(self):
        workflow = {"36": {"class_type": "LoadImage", "inputs": {"upload": "image"}}}
        with self.assertRaises(cu.ComfyUIUploadError):
            cu.apply_uploaded_image_to_workflow(workflow, {"name": "a.png", "subfolder": "", "type": "input"})

    def test_does_not_mutate_original_workflow(self):
        workflow = self._workflow()
        original = copy.deepcopy(workflow)
        validated = {"name": "server-name.png", "subfolder": "", "type": "input"}
        cu.apply_uploaded_image_to_workflow(workflow, validated)
        self.assertEqual(workflow, original)

    def test_missing_load_image_node_raises(self):
        with self.assertRaises(cu.ComfyUIUploadError):
            cu.apply_uploaded_image_to_workflow({}, {"name": "a.png", "subfolder": "", "type": "input"})


class SendUploadRequestTest(IsolatedUploadTestCase):
    """requests.post相当をmockした`session`経由でのみ呼び出す。実ソケット
    通信は一切発生しない。
    """

    def _fake_session(
        self, status_code=200, json_body=None, side_effect=None, headers=None, raw_body=None
    ):
        # 2回目のCodexレビュー指摘、Major対応: send_upload_request()が
        # Content-Type検証・ストリーミング読み込み(iter_content())を行う
        # ようになったため、`.json.return_value`だけでなく`.headers`・
        # `.iter_content()`も実際の応答形状に合わせてmockする。
        session = mock.MagicMock()
        if side_effect is not None:
            session.post.side_effect = side_effect
        else:
            response = mock.MagicMock()
            response.status_code = status_code
            response.headers = headers if headers is not None else {"Content-Type": "application/json"}
            if raw_body is None:
                raw_body = json.dumps(json_body if json_body is not None else {}).encode("utf-8")
            response.iter_content = mock.MagicMock(return_value=iter([raw_body]))
            session.post.return_value = response
        return session

    def test_successful_upload_returns_validated_response(self):
        path = self.resolved_path()
        session = self._fake_session(json_body={"name": "server-name.png", "subfolder": "", "type": "input"})
        result = cu.send_upload_request("https://fake-pod.example", path, rri, session=session)
        self.assertEqual(result, {"name": "server-name.png", "subfolder": "", "type": "input"})
        called_url = session.post.call_args.args[0]
        self.assertEqual(called_url, "https://fake-pod.example/upload/image")

    def test_never_touches_real_requests_module(self):
        path = self.resolved_path()
        session = self._fake_session(json_body={"name": "a.png", "subfolder": "", "type": "input"})
        with mock.patch("comfyui_upload.requests.post") as real_post:
            cu.send_upload_request("https://fake-pod.example", path, rri, session=session)
            self.assertFalse(real_post.called)

    def test_non_200_status_raises(self):
        path = self.resolved_path()
        session = self._fake_session(status_code=500, json_body={})
        with self.assertRaises(cu.ComfyUIUploadError):
            cu.send_upload_request("https://fake-pod.example", path, rri, session=session)

    def test_invalid_json_response_raises(self):
        path = self.resolved_path()
        session = self._fake_session(raw_body=b"{not valid json")
        with self.assertRaises(cu.ComfyUIUploadError):
            cu.send_upload_request("https://fake-pod.example", path, rri, session=session)

    def test_timeout_raises_clean_error(self):
        import requests

        path = self.resolved_path()
        session = self._fake_session(side_effect=requests.exceptions.Timeout("boom"))
        with self.assertRaises(cu.ComfyUIUploadError) as ctx:
            cu.send_upload_request("https://fake-pod.example", path, rri, session=session)
        self.assertNotIn("boom", str(ctx.exception))

    def test_connection_error_does_not_leak_url_or_secrets(self):
        import requests

        path = self.resolved_path()
        secret_url = "https://secret-pod-abcxyz.proxy.runpod.net/upload/image"
        session = self._fake_session(side_effect=requests.exceptions.ConnectionError(secret_url))
        with self.assertRaises(cu.ComfyUIUploadError) as ctx:
            cu.send_upload_request(secret_url.rsplit("/upload/image", 1)[0], path, rri, session=session)
        self.assertNotIn(secret_url, str(ctx.exception))
        self.assertNotIn("secret-pod-abcxyz", str(ctx.exception))

    def test_connection_error_does_not_leak_secrets_via_exception_chain(self):
        # Codexレビュー指摘(Critical)の回帰テスト: str(exception)自体は
        # 安全でも、`raise ... from e`による例外チェーン(__cause__)や
        # traceback出力(logger.exception()等が使う)経由で、requests例外
        # 本文に含まれる接続先URL・秘密情報が漏れていた。
        import requests
        import traceback

        path = self.resolved_path()
        secret_url = "https://secret-pod-abcxyz.proxy.runpod.net/upload/image"
        secret_token = "token=SECRET123"
        session = self._fake_session(
            side_effect=requests.exceptions.ConnectionError(f"{secret_url} {secret_token}")
        )
        with self.assertRaises(cu.ComfyUIUploadError) as ctx:
            cu.send_upload_request("https://secret-pod-abcxyz.proxy.runpod.net", path, rri, session=session)

        self.assertIsNone(ctx.exception.__cause__)
        tb_text = "".join(
            traceback.format_exception(type(ctx.exception), ctx.exception, ctx.exception.__traceback__)
        )
        self.assertNotIn(secret_url, tb_text)
        self.assertNotIn(secret_token, tb_text)

    def test_timeout_none_rejected(self):
        # Codexレビュー指摘(Major)の回帰テスト: timeout=Noneはrequestsに
        # とって「無期限」を意味するため、事前に拒否しなければならない。
        path = self.resolved_path()
        session = mock.MagicMock()
        with self.assertRaises(cu.ComfyUIUploadError):
            cu.send_upload_request("https://fake-pod.example", path, rri, session=session, timeout=None)
        self.assertFalse(session.post.called)

    def test_timeout_bool_rejected(self):
        path = self.resolved_path()
        session = mock.MagicMock()
        with self.assertRaises(cu.ComfyUIUploadError):
            cu.send_upload_request("https://fake-pod.example", path, rri, session=session, timeout=True)
        self.assertFalse(session.post.called)

    def test_timeout_negative_rejected(self):
        path = self.resolved_path()
        session = mock.MagicMock()
        with self.assertRaises(cu.ComfyUIUploadError):
            cu.send_upload_request("https://fake-pod.example", path, rri, session=session, timeout=-5)
        self.assertFalse(session.post.called)

    def test_timeout_infinite_rejected(self):
        path = self.resolved_path()
        session = mock.MagicMock()
        with self.assertRaises(cu.ComfyUIUploadError):
            cu.send_upload_request(
                "https://fake-pod.example", path, rri, session=session, timeout=float("inf")
            )
        self.assertFalse(session.post.called)

    def test_valid_finite_timeout_still_passed_through(self):
        path = self.resolved_path()
        session = self._fake_session(json_body={"name": "a.png", "subfolder": "", "type": "input"})
        cu.send_upload_request("https://fake-pod.example", path, rri, session=session, timeout=5)
        self.assertEqual(session.post.call_args.kwargs["timeout"], 5)

    def test_unknown_image_type_rejected_before_any_network_call(self):
        # Codexレビュー指摘(Major)の回帰テスト: build_upload_request()と
        # 同じtype検証を、実送信のsend_upload_request()でも行うこと。
        path = self.resolved_path()
        session = mock.MagicMock()
        with self.assertRaises(cu.ComfyUIUploadError):
            cu.send_upload_request(
                "https://fake-pod.example", path, rri, session=session, image_type="arbitrary-bogus"
            )
        self.assertFalse(session.post.called)

    def test_sent_bytes_and_filename_derive_from_same_single_read(self):
        # Codexレビュー指摘(Major)の回帰テスト(TOCTOU対策): 検証・
        # ハッシュ計算・送信がすべて同一の読み取り結果から行われることを、
        # 送信されたバイト列のハッシュがファイル名に埋め込まれたダイジェスト
        # と一致することで確認する。
        import hashlib

        path = self.resolved_path()
        session = self._fake_session(json_body={"name": "a.png", "subfolder": "", "type": "input"})
        cu.send_upload_request("https://fake-pod.example", path, rri, session=session)

        sent_filename, sent_content, sent_content_type = session.post.call_args.kwargs["files"]["image"]
        expected_digest = hashlib.sha256(path.read_bytes()).hexdigest()[:12]
        self.assertIn(expected_digest, sent_filename)
        self.assertEqual(sent_content, path.read_bytes())
        self.assertEqual(sent_content_type, "image/png")

    def test_full_request_kwargs_match_expected_multipart_contract(self):
        # Codexレビュー指摘(Minor)の回帰テスト: mockが緩く、files/data/
        # timeoutの厳密な形を検証していなかった。
        path = self.resolved_path()
        session = self._fake_session(json_body={"name": "a.png", "subfolder": "", "type": "input"})
        cu.send_upload_request("https://fake-pod.example", path, rri, session=session, overwrite=True)

        self.assertEqual(session.post.call_count, 1)
        args, kwargs = session.post.call_args
        self.assertEqual(args, ("https://fake-pod.example/upload/image",))
        self.assertEqual(set(kwargs.keys()), {"files", "data", "timeout", "allow_redirects", "stream"})
        self.assertIn("image", kwargs["files"])
        filename, content, content_type = kwargs["files"]["image"]
        self.assertTrue(filename.endswith(".png"))
        self.assertIsInstance(content, (bytes, bytearray))
        self.assertEqual(content_type, "image/png")
        self.assertEqual(kwargs["data"], {"type": "input", "overwrite": "true"})
        self.assertEqual(kwargs["timeout"], cu.DEFAULT_UPLOAD_TIMEOUT_SECONDS)
        self.assertFalse(kwargs["allow_redirects"])
        self.assertTrue(kwargs["stream"])

    def test_response_with_unsafe_name_rejected_even_on_200(self):
        path = self.resolved_path()
        session = self._fake_session(json_body={"name": "../escape.png", "subfolder": "", "type": "input"})
        with self.assertRaises(cu.ComfyUIUploadError):
            cu.send_upload_request("https://fake-pod.example", path, rri, session=session)

    def test_invalid_source_path_rejected_before_any_network_call(self):
        symlink_target = self.resolved_path()
        link = self.root / "haruto" / "images" / "symlink.png"
        link.symlink_to(symlink_target)
        session = mock.MagicMock()
        with self.assertRaises(cu.ComfyUIUploadError):
            cu.send_upload_request("https://fake-pod.example", link, rri, session=session)
        self.assertFalse(session.post.called)

    def test_redirect_response_rejected(self):
        # 2回目のCodexレビュー指摘、Major対応の回帰テスト: uploadだけ
        # redirectに追従していた問題を修正した(他の3境界と同様に一律拒否)。
        # 3回目のCodexレビュー指摘: 単に例外発生を確認するだけでは、
        # 汎用のHTTPエラー処理(status_code!=200)がたまたま302も拒否して
        # いるだけで「意味のあるテスト」になっていない恐れがあるため、
        # redirect専用の分岐が実際に発火したことをメッセージで確認する。
        path = self.resolved_path()
        session = self._fake_session(status_code=302, headers={"Location": "https://evil.example/steal"})
        with self.assertRaises(cu.ComfyUIUploadError) as ctx:
            cu.send_upload_request("https://fake-pod.example", path, rri, session=session)
        self.assertIn("redirect", str(ctx.exception))

    def test_response_size_limit_exceeded_rejected(self):
        path = self.resolved_path()
        oversized_body = json.dumps({"name": "x" * (cu.MAX_UPLOAD_RESPONSE_BYTES + 1), "subfolder": "", "type": "input"}).encode(
            "utf-8"
        )
        session = self._fake_session(raw_body=oversized_body)
        with self.assertRaises(cu.ComfyUIUploadError) as ctx:
            cu.send_upload_request("https://fake-pod.example", path, rri, session=session)
        self.assertIn("上限", str(ctx.exception))

    def test_response_size_exactly_at_limit_accepted(self):
        # サイズ上限ちょうどは拒否されない(オフバイワンの回帰テスト)。
        path = self.resolved_path()
        padding = cu.MAX_UPLOAD_RESPONSE_BYTES - len(
            json.dumps({"name": "", "subfolder": "", "type": "input"}).encode("utf-8")
        )
        body = json.dumps({"name": "x" * max(padding, 0), "subfolder": "", "type": "input"}).encode("utf-8")
        self.assertLessEqual(len(body), cu.MAX_UPLOAD_RESPONSE_BYTES)
        session = self._fake_session(raw_body=body)
        result = cu.send_upload_request("https://fake-pod.example", path, rri, session=session)
        self.assertEqual(result["name"], "x" * max(padding, 0))

    def test_non_json_content_type_rejected(self):
        path = self.resolved_path()
        session = self._fake_session(headers={"Content-Type": "text/html"}, raw_body=b"<html></html>")
        with self.assertRaises(cu.ComfyUIUploadError) as ctx:
            cu.send_upload_request("https://fake-pod.example", path, rri, session=session)
        self.assertIn("Content-Type", str(ctx.exception))

    def test_stream_read_exception_wrapped_and_response_closed(self):
        # 3回目のCodexレビュー指摘、Major対応の回帰テスト: stream=True化後、
        # 応答本文の読み込み中に送出されるrequests例外(接続先URLを含み得る)
        # がそのまま漏れず、固定メッセージへ変換され、応答が閉じられること。
        import requests

        path = self.resolved_path()
        secret_url = "https://secret-pod.example/upload/image"
        response = mock.MagicMock()
        response.status_code = 200
        response.headers = {"Content-Type": "application/json"}
        response.iter_content = mock.MagicMock(
            side_effect=requests.exceptions.ConnectionError(secret_url)
        )
        session = mock.MagicMock()
        session.post.return_value = response
        with self.assertRaises(cu.ComfyUIUploadError) as ctx:
            cu.send_upload_request("https://fake-pod.example", path, rri, session=session)
        self.assertNotIn(secret_url, str(ctx.exception))
        response.close.assert_called_once()

    def test_timeout_above_upper_bound_rejected(self):
        path = self.resolved_path()
        session = self._fake_session()
        with self.assertRaises(cu.ComfyUIUploadError):
            cu.send_upload_request(
                "https://fake-pod.example", path, rri, session=session, timeout=cu.MAX_UPLOAD_TIMEOUT_SECONDS + 1
            )
        self.assertFalse(session.post.called)


if __name__ == "__main__":
    unittest.main()
