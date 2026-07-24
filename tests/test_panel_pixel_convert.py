#!/usr/bin/env python3
"""scripts/panel_pixel_convert.py(SDXL生成画像1536x640→第1コマinner
1009x345への実ピクセル変換)のテスト。

外部通信は一切発生しない(ローカルファイルのみを扱う)。テスト用の
1536x640画像は、単色ではなく縦方向に識別可能な帯(y座標ごとに異なる色)を
持たせ、crop位置(上38px・下38px)が正しく適用されたことをピクセル値で
検証できるようにする。テストで作成した一時画像はTemporaryDirectory経由で
リポジトリ外に作成し、リポジトリへは残さない。
"""
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import one_panel_pilot as opp  # noqa: E402
import panel_pixel_convert as ppc  # noqa: E402


def _make_striped_image(width=1536, height=640, stripe_height=1):
    """y座標ごとに一意な色を持つ画像を作る(クロップ位置の検証用)。
    stripe_height=1でy座標ごとに完全に一意な色になる。
    """
    img = Image.new("RGB", (width, height))
    pixels = img.load()
    for y in range(height):
        band = y // stripe_height
        color = (band % 256, (band * 5) % 256, (band * 11) % 256)
        for x in range(width):
            pixels[x, y] = color
    return img


class ConvertGenerationToPanelTest(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.tmp = pathlib.Path(self._tmpdir.name)
        self.src = self.tmp / "generation.png"
        self.dst = self.tmp / "panel1.png"
        _make_striped_image().save(self.src, format="PNG")

    def test_output_size_matches_inner_geometry(self):
        result = ppc.convert_generation_to_panel(self.src, self.dst)
        template = opp.load_five_panel_template()
        inner = opp.get_panel_geometry(template, 1)["inner"]
        self.assertEqual(result["final_size"], {"width": inner["width"], "height": inner["height"]})
        with Image.open(self.dst) as saved:
            self.assertEqual(saved.size, (inner["width"], inner["height"]))

    def test_result_matches_pr10_integer_contract(self):
        result = ppc.convert_generation_to_panel(self.src, self.dst)
        self.assertEqual(result["resize_to_px"], {"width": 1009, "height": 421})
        self.assertEqual(result["crop_box_px"], {"left": 0, "upper": 38, "right": 1009, "lower": 383})
        self.assertEqual(result["resampling_method"], "LANCZOS")

    def test_crop_position_uses_documented_band(self):
        # 生成画像はstripe_height=1でy座標ごとに一意な色。
        # リサイズ(1536x640→1009x421)後、上から38pxをクロップして
        # 345px分を採用するはずなので、出力画像の先頭行はリサイズ後の
        # y=38付近の帯に対応するはず(リサイズによる補間で完全一致は
        # しないため、resize_to_pxのheight比率から近似の元y座標を計算し、
        # その近傍の帯色に近い値になっていることだけを確認する)。
        result = ppc.convert_generation_to_panel(self.src, self.dst)
        resize_to = result["resize_to_px"]
        with Image.open(self.dst) as saved:
            saved = saved.convert("RGB")
            top_pixel = saved.getpixel((0, 0))
            bottom_pixel = saved.getpixel((0, saved.height - 1))

        # crop_top_px=38は、リサイズ後(高さ421)の全体に対する相対位置。
        # 出力の先頭行はリサイズ後y=38付近、末尾行はy=382付近に対応するはず。
        approx_top_source_y = int(38 * 640 / resize_to["height"])
        approx_bottom_source_y = int(382 * 640 / resize_to["height"])
        expected_top_band = approx_top_source_y % 256
        expected_bottom_band = approx_bottom_source_y % 256
        # LANCZOSの補間誤差を考慮し、近傍数バンド以内であることを確認する。
        self.assertLessEqual(abs(top_pixel[0] - expected_top_band), 5)
        self.assertLessEqual(abs(bottom_pixel[0] - expected_bottom_band), 5)

    def test_top_and_bottom_stripes_are_not_identical(self):
        # クロップが実際に発生していること(先頭行と末尾行が同じ帯色に
        # なっていない=正しく別位置がクロップされている)ことの素朴な確認。
        ppc.convert_generation_to_panel(self.src, self.dst)
        with Image.open(self.dst) as saved:
            saved = saved.convert("RGB")
            self.assertNotEqual(saved.getpixel((0, 0)), saved.getpixel((0, saved.height - 1)))

    def test_output_is_png(self):
        ppc.convert_generation_to_panel(self.src, self.dst)
        with self.dst.open("rb") as f:
            header = f.read(8)
        self.assertEqual(header, b"\x89PNG\r\n\x1a\n")

    def test_mismatched_input_dimensions_rejected_not_silently_recomputed(self):
        wrong = self.tmp / "wrong.png"
        _make_striped_image(width=800, height=600).save(wrong, format="PNG")
        with self.assertRaises(ppc.PanelPixelConvertError):
            ppc.convert_generation_to_panel(wrong, self.dst)
        self.assertFalse(self.dst.exists())

    def test_does_not_overwrite_existing_dest_by_default(self):
        self.dst.write_bytes(b"pre-existing content")
        with self.assertRaises(ppc.PanelPixelConvertError):
            ppc.convert_generation_to_panel(self.src, self.dst)
        self.assertEqual(self.dst.read_bytes(), b"pre-existing content")

    def test_overwrite_true_allows_replacing_existing_dest(self):
        self.dst.write_bytes(b"pre-existing content")
        ppc.convert_generation_to_panel(self.src, self.dst, overwrite=True)
        with Image.open(self.dst) as saved:
            self.assertEqual(saved.size, (1009, 345))

    def test_rejects_same_source_and_dest_path(self):
        with self.assertRaises(ppc.PanelPixelConvertError):
            ppc.convert_generation_to_panel(self.src, self.src)

    def test_no_temp_file_left_behind_on_success(self):
        ppc.convert_generation_to_panel(self.src, self.dst)
        remaining = sorted(p.name for p in self.tmp.iterdir())
        self.assertEqual(remaining, sorted(["generation.png", "panel1.png"]))

    def test_no_temp_file_left_behind_on_failure(self):
        wrong = self.tmp / "wrong.png"
        _make_striped_image(width=800, height=600).save(wrong, format="PNG")
        with self.assertRaises(ppc.PanelPixelConvertError):
            ppc.convert_generation_to_panel(wrong, self.dst)
        remaining = sorted(p.name for p in self.tmp.iterdir())
        self.assertEqual(remaining, sorted(["generation.png", "wrong.png"]))

    def test_missing_source_file_rejected(self):
        missing = self.tmp / "does-not-exist.png"
        with self.assertRaises(ppc.PanelPixelConvertError):
            ppc.convert_generation_to_panel(missing, self.dst)

    def test_non_image_source_rejected(self):
        not_image = self.tmp / "not-image.png"
        not_image.write_bytes(b"this is not a real png file" * 10)
        with self.assertRaises(ppc.PanelPixelConvertError):
            ppc.convert_generation_to_panel(not_image, self.dst)

    def test_rgba_input_handled(self):
        rgba_src = self.tmp / "rgba.png"
        img = _make_striped_image().convert("RGBA")
        img.save(rgba_src, format="PNG")
        result = ppc.convert_generation_to_panel(rgba_src, self.dst)
        self.assertEqual(result["final_size"], {"width": 1009, "height": 345})

    def test_generation_dimension_check_uses_exif_normalized_size(self):
        # Review B指摘(Minor)の回帰テスト: generation_width×generation_height
        # との一致判定は、EXIF orientation正規化「後」の寸法に対して行われる
        # ことを固定する(正規化前の保存寸法ではない)。保存上は640x1536の
        # portrait画像でも、EXIF orientation=6(90度回転相当)により
        # 正規化後は1536x640のlandscapeになるため受理される。
        exif_src = self.tmp / "exif.png"
        img = Image.new("RGB", (640, 1536), (10, 20, 30))
        exif = img.getexif()
        exif[0x0112] = 6  # Orientation tag: rotate 270 CW
        img.save(exif_src, format="PNG", exif=exif)

        result = ppc.convert_generation_to_panel(
            exif_src, self.dst, generation_width=1536, generation_height=640
        )
        self.assertEqual(result["generation_size"], {"width": 1536, "height": 640})

    def test_extreme_dimension_rejected_by_image_open_guard(self):
        # 片辺だけ極端に大きい画像は、compute_panel_fit()の対象コマ適合判定
        # より前段の、_open_and_normalize_image()自体の辺長上限チェックで
        # 拒否されるべきものである。この画像読み込み専用の防御を直接検証する
        # (full pipelineだと、対象アスペクト比に収まらないという別のエラー
        # 〔one_panel_pilot.PilotError〕が先に発生してしまうため)。
        extreme_src = self.tmp / "extreme.png"
        Image.new("RGB", (ppc.MAX_INPUT_DIMENSION_PX + 1, 100), (0, 0, 0)).save(extreme_src, format="PNG")
        with self.assertRaises(ppc.PanelPixelConvertError):
            ppc._open_and_normalize_image(extreme_src)

    def test_excessive_pixel_count_rejected_by_image_open_guard(self):
        big_area_src = self.tmp / "big-area.png"
        # 辺の長さ上限未満でも、総ピクセル数の上限を超える組み合わせ。
        side = int(ppc.MAX_INPUT_PIXELS ** 0.5) + 1000
        side = min(side, ppc.MAX_INPUT_DIMENSION_PX - 1)
        Image.new("RGB", (side, side), (0, 0, 0)).save(big_area_src, format="PNG")
        with self.assertRaises(ppc.PanelPixelConvertError):
            ppc._open_and_normalize_image(big_area_src)

    def test_decompression_bomb_warning_zone_converted_cleanly(self):
        # 2回目のCodexレビュー指摘(Minor)の回帰テスト: Pillowの閾値の
        # 1〜2倍のピクセル数では、DecompressionBombError(2倍超で送出)
        # ではなくDecompressionBombWarning(別系統のクラス)が送出される。
        # 以前はこちらをcatchしておらず素のまま漏れていた。
        original_max = Image.MAX_IMAGE_PIXELS
        try:
            # 1536x640=983,040pxが、閾値の1〜2倍(warning zone)に入るよう
            # 閾値を設定する(700,000 * 2 = 1,400,000 > 983,040 > 700,000)。
            Image.MAX_IMAGE_PIXELS = 700_000
            with self.assertRaises(ppc.PanelPixelConvertError) as ctx:
                ppc._open_and_normalize_image(self.src)
            self.assertNotIsInstance(ctx.exception, Warning)
        finally:
            Image.MAX_IMAGE_PIXELS = original_max

    def test_custom_generation_resolution_used_when_specified(self):
        custom_src = self.tmp / "custom.png"
        _make_striped_image(width=2000, height=690).save(custom_src, format="PNG")
        result = ppc.convert_generation_to_panel(
            custom_src, self.dst, generation_width=2000, generation_height=690
        )
        self.assertEqual(result["generation_size"], {"width": 2000, "height": 690})
        self.assertEqual(result["final_size"], {"width": 1009, "height": 345})

    def test_overwrite_protection_survives_exists_check_race(self):
        # Codexレビュー指摘(Major)の回帰テスト: 以前はdest_path.exists()を
        # 確認するだけで、確認とos.replace()の間に競合があれば
        # overwrite=Falseの保護を迂回できた。O_CREAT|O_EXCLベースの
        # アトミックな確保に変更したため、Path.exists()自体が(競合により)
        # Falseを返すタイミングであっても、実際にdestが存在すれば拒否
        # されることを確認する。
        self.dst.write_bytes(b"pre-existing content")
        with mock.patch("pathlib.Path.exists", return_value=False):
            with self.assertRaises(ppc.PanelPixelConvertError):
                ppc.convert_generation_to_panel(self.src, self.dst)
        self.assertEqual(self.dst.read_bytes(), b"pre-existing content")

    def test_replace_failure_preserves_existing_output(self):
        # Codexレビュー指摘(Major)の回帰テスト: 以前はos.replace()実行後に
        # 検証していたため、置換自体が失敗した場合でも、それより前の検証済み
        # tmpファイルの内容と既存destの整合性を保証できていなかった。
        # 置換前に検証を済ませているため、置換失敗時は既存の正常な出力を
        # 破壊しないことを確認する。
        ppc.convert_generation_to_panel(self.src, self.dst)
        original_bytes = self.dst.read_bytes()

        with mock.patch("panel_pixel_convert.os.replace", side_effect=OSError("simulated replace failure")):
            with self.assertRaises(Exception):
                ppc.convert_generation_to_panel(self.src, self.dst, overwrite=True)

        self.assertEqual(self.dst.read_bytes(), original_bytes)

    def test_verification_happens_before_replace_not_after(self):
        # 2回目のCodexレビュー指摘(Minor)の回帰テスト: 上記のテストは
        # os.replace()自体を失敗させるだけなので、検証がreplaceより前に
        # 行われる実装でも、replaceより後に行われる(旧)実装でも、
        # どちらでも既存destが変わらず成功してしまい、検証順序の後退を
        # 検出できなかった。ここではtmpファイルの検証自体を失敗させ、
        # os.replace()が一度も呼ばれないことを直接確認する。
        real_open = Image.open

        def fake_open(fp, *args, **kwargs):
            if ".tmp-" in str(fp):
                raise OSError("simulated corrupt temp file during pre-replace verification")
            return real_open(fp, *args, **kwargs)

        with mock.patch("panel_pixel_convert.Image.open", side_effect=fake_open):
            with mock.patch("panel_pixel_convert.os.replace") as fake_replace:
                with self.assertRaises(ppc.PanelPixelConvertError):
                    ppc.convert_generation_to_panel(self.src, self.dst)
                fake_replace.assert_not_called()

    def test_verification_happens_before_link_not_after(self):
        # overwrite=False(os.link()経路)でも同様に、リンク前検証が
        # 機能し、os.link()が一度も呼ばれないことを確認する。
        real_open = Image.open

        def fake_open(fp, *args, **kwargs):
            if ".tmp-" in str(fp):
                raise OSError("simulated corrupt temp file during pre-link verification")
            return real_open(fp, *args, **kwargs)

        with mock.patch("panel_pixel_convert.Image.open", side_effect=fake_open):
            with mock.patch("panel_pixel_convert.os.link") as fake_link:
                with self.assertRaises(ppc.PanelPixelConvertError):
                    ppc.convert_generation_to_panel(self.src, self.dst)
                fake_link.assert_not_called()

    def test_animated_png_rejected(self):
        # Codexレビュー指摘(Minor)の回帰テスト: 以前は複数フレーム画像
        # (アニメーションPNG)の最初のフレームだけを黙って静止画として
        # 変換していた。
        apng_src = self.tmp / "apng.png"
        frame1 = Image.new("RGB", (1536, 640), (255, 0, 0))
        frame2 = Image.new("RGB", (1536, 640), (0, 0, 255))
        frame1.save(apng_src, format="PNG", save_all=True, append_images=[frame2], duration=100, loop=0)
        with self.assertRaises(ppc.PanelPixelConvertError):
            ppc.convert_generation_to_panel(apng_src, self.dst)

    def test_bool_panel_no_rejected(self):
        # Codexレビュー指摘(Minor)の回帰テスト: boolはintのサブクラスの
        # ため明示的に除外する。
        with self.assertRaises(ppc.PanelPixelConvertError):
            ppc.convert_generation_to_panel(self.src, self.dst, panel_no=True)

    def test_bool_overwrite_rejected(self):
        with self.assertRaises(ppc.PanelPixelConvertError):
            ppc.convert_generation_to_panel(self.src, self.dst, overwrite="true")

    def test_huge_generation_height_rejected_cleanly_not_overflowerror(self):
        # Codexレビュー指摘(Minor)の回帰テスト: 以前は極端に大きい
        # generation_heightがcompute_panel_fit()内部で素のOverflowErrorに
        # なっていた。
        with self.assertRaises(ppc.PanelPixelConvertError) as ctx:
            ppc.convert_generation_to_panel(self.src, self.dst, generation_height=10**400)
        self.assertNotIsInstance(ctx.exception, OverflowError)

    def test_negative_generation_width_rejected(self):
        with self.assertRaises(ppc.PanelPixelConvertError):
            ppc.convert_generation_to_panel(self.src, self.dst, generation_width=-1536)

    def test_float_generation_width_rejected(self):
        with self.assertRaises(ppc.PanelPixelConvertError):
            ppc.convert_generation_to_panel(self.src, self.dst, generation_width=1536.0)


if __name__ == "__main__":
    unittest.main()
