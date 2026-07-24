#!/usr/bin/env python3
"""「画像アップロード準備」と「実ピクセル変換」を、外部通信なしで
end-to-endに再現するローカル統合試験。

1. ハルト正本画像を既存resolverで解決
2. upload用multipartリクエストの内容をmockで確認
3. 正常なComfyUI upload応答fixtureを検証
4. 返された画像名をWorkflowのLoadImageへ反映
5. 1536x640のテスト画像をローカル生成
6. 実ピクセル変換を実行
7. 1009x345のPNGを確認
8. RunPodへ通信していないことを確認
9. 秘密情報が出力に含まれないことを確認

reference_image解決の隔離は既存tests/test_one_panel_pilot.pyの
IsolatedReferenceImagesTestCaseをそのまま再利用する。
"""
import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

import one_panel_pilot as opp  # noqa: E402
import resolve_reference_image as rri  # noqa: E402
import comfyui_upload as cu  # noqa: E402
import panel_pixel_convert as ppc  # noqa: E402
from test_one_panel_pilot import IsolatedReferenceImagesTestCase, load_fixture_packet, CONFIG_PATH  # noqa: E402


class OnePanelRuntimePrepIntegrationTest(IsolatedReferenceImagesTestCase):
    def setUp(self):
        super().setUp()
        real_png_bytes = cu.PNG_SIGNATURE + b"\x00" * 64
        for name in ("00-neutral.png", "04-surprise-weak.png"):
            (self.root / "haruto" / "images" / name).write_bytes(real_png_bytes)

        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.work_dir = pathlib.Path(self._tmpdir.name)

    def test_full_upload_and_pixel_conversion_pipeline_without_network(self):
        # 1. ハルト正本画像を既存resolverで解決
        packet = load_fixture_packet()
        panel = opp.get_panel(packet, 1)
        performer = panel["performers"][0]
        reference_image_path = opp.resolve_performer_reference_image(performer, rri)
        self.assertTrue(reference_image_path.is_file())

        # 2. upload用multipartリクエストの内容をmockで確認
        upload_request = cu.build_upload_request(reference_image_path, rri)
        self.assertEqual(upload_request["endpoint_path"], "/upload/image")
        self.assertEqual(upload_request["form_fields"]["overwrite"], "false")

        secret_endpoint = "https://secret-pod-abc123.proxy.runpod.net"
        secret_api_key = "sk-super-secret-runpod-key-99999"
        fake_response = mock.MagicMock()
        fake_response.status_code = 200
        fake_response.headers = {"Content-Type": "application/json"}
        fake_response.iter_content = mock.MagicMock(
            return_value=iter(
                [
                    json.dumps(
                        {
                            "name": upload_request["upload_filename"],
                            "subfolder": "",
                            "type": "input",
                        }
                    ).encode("utf-8")
                ]
            )
        )
        fake_session = mock.MagicMock()
        fake_session.post.return_value = fake_response

        with mock.patch.dict(
            "os.environ",
            {"RUNPOD_API_KEY": secret_api_key, "RUNPOD_ENDPOINT_URL": secret_endpoint},
        ):
            # 8. RunPodへ通信していないことを確認(実requestsモジュールが
            #    一切呼ばれていないことを検証しながら送信関数を実行する)。
            with mock.patch("comfyui_upload.requests.post") as real_post:
                upload_result = cu.send_upload_request(
                    secret_endpoint, reference_image_path, rri, session=fake_session
                )
                self.assertFalse(real_post.called)

        # 3. 正常なComfyUI upload応答fixtureを検証(send_upload_request内部で
        #    既にvalidate_upload_response()を通過している)
        self.assertEqual(upload_result["name"], upload_request["upload_filename"])

        # 4. 返された画像名をWorkflowのLoadImageへ反映
        config = opp.load_config(CONFIG_PATH)
        workflow, _, _ = opp.build_comfyui_workflow(
            panel, performer, reference_image_path, config, seed=12345
        )
        updated_workflow = cu.apply_uploaded_image_to_workflow(workflow, upload_result)
        self.assertEqual(updated_workflow["36"]["inputs"]["image"], upload_result["name"])
        # 元workflowは変更されない
        self.assertEqual(workflow["36"]["inputs"]["image"], reference_image_path.name)

        # 5. 1536x640のテスト画像をローカル生成(識別可能な帯付き)
        generation_src = self.work_dir / "generated.png"
        img = Image.new("RGB", (1536, 640))
        pixels = img.load()
        for y in range(640):
            color = (y % 256, (y * 5) % 256, (y * 11) % 256)
            for x in range(1536):
                pixels[x, y] = color
        img.save(generation_src, format="PNG")

        # 6. 実ピクセル変換を実行
        panel_dest = self.work_dir / "panel1.png"
        conversion_result = ppc.convert_generation_to_panel(generation_src, panel_dest)

        # 7. 1009x345のPNGを確認
        self.assertEqual(conversion_result["final_size"], {"width": 1009, "height": 345})
        with Image.open(panel_dest) as saved:
            self.assertEqual(saved.size, (1009, 345))
            with panel_dest.open("rb") as f:
                self.assertEqual(f.read(8), b"\x89PNG\r\n\x1a\n")

        # 第1コマinner座標(five_panel_template.json)と一致することを確認
        template = opp.load_five_panel_template()
        inner = opp.get_panel_geometry(template, 1)["inner"]
        self.assertEqual(conversion_result["final_size"], {"width": inner["width"], "height": inner["height"]})

        # 9. 秘密情報が出力に含まれないことを確認
        serialized = json.dumps(
            {
                "upload_request": upload_request,
                "upload_result": upload_result,
                "updated_workflow": updated_workflow,
                "conversion_result": conversion_result,
            },
            ensure_ascii=False,
        )
        self.assertNotIn(secret_api_key, serialized)
        self.assertNotIn(secret_endpoint, serialized)
        self.assertNotIn("secret-pod-abc123", serialized)


if __name__ == "__main__":
    unittest.main()
