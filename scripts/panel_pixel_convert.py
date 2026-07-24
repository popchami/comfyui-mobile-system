#!/usr/bin/env python3
"""SDXL生成画像(既定1536×640)を、5コマテンプレート第1コマのinner
(five_panel_template.jsonより1009×345)へ実際にリサイズ・クロップする
ピクセル処理。

scripts/one_panel_pilot.py の`compute_panel_fit()`が確定した整数ピクセル
契約(`resize_to_px`/`crop_box_px`/`resampling_method`)をそのまま用いる
(寸法計算ロジックをこちらへ重複実装しない)。対象コマのinner座標自体も
`load_five_panel_template()`/`get_panel_geometry()`経由でfive_panel_template.json
から読み込み、ハードコードしない。

このモジュールはローカルファイルの画像処理のみを行う。RunPod・ComfyUIへの
実通信は一切行わない。

依存: Pillow(このリポジトリで新規追加)。標準ライブラリのみで完結していた
scripts/one_panel_pilot.py とは異なり、このモジュールは実ピクセル処理の
ためにPillowを必要とする。導入方法は環境により異なる(Debian/Ubuntu系で
aptを使う場合は`python3-pil`、venv/pip環境では`python -m pip install
Pillow`等。`python3-pil`はaptを使わない環境〔Termuxのpipベース環境等〕
では唯一の導入方法ではない、Review B指摘、Minor対応)。
"""
import os
import sys
import tempfile
import warnings
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import one_panel_pilot as opp  # noqa: E402


class PanelPixelConvertError(Exception):
    """画像変換における失敗を表す。"""


_RESAMPLING_FILTERS = {"LANCZOS": Image.LANCZOS}

# 対象の生成解像度(既定1536x640=983,040px)に対して十分な余裕を持たせつつ、
# decompression bomb(意図的に極端なピクセル数を持つ画像)を明確に拒否する
# ための上限。20メガピクセルは既定の生成解像度の約20倍の余裕がある。
MAX_INPUT_PIXELS = 20_000_000
# 極端なアスペクト比(面積は小さくても片辺が極端に大きい)も個別に拒否する。
MAX_INPUT_DIMENSION_PX = 10_000


def _open_and_normalize_image(path):
    """入力画像を安全に開き、EXIF orientationを正規化してRGB/RGBAへ変換する。

    破損・非対応形式・decompression bomb・極端な寸法を明確なエラーで拒否する。
    呼び出し側がcloseできる、`with`ブロックの外に出た独立したImageを返す。
    """
    path = Path(path)
    if not path.is_file():
        raise PanelPixelConvertError(f"入力画像が見つかりません: {path}")

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(path) as img:
                width, height = img.size
                if width <= 0 or height <= 0:
                    raise PanelPixelConvertError(f"入力画像の寸法が不正です: {width}x{height}")
                if width > MAX_INPUT_DIMENSION_PX or height > MAX_INPUT_DIMENSION_PX:
                    raise PanelPixelConvertError(
                        f"入力画像の辺の長さが上限({MAX_INPUT_DIMENSION_PX}px)を"
                        f"超えています(極端な寸法を拒否): {width}x{height}"
                    )
                if width * height > MAX_INPUT_PIXELS:
                    raise PanelPixelConvertError(
                        f"入力画像のピクセル数が上限({MAX_INPUT_PIXELS}px)を超えています"
                        f"(decompression bomb対策): {width}x{height}"
                    )
                # 複数フレーム画像(アニメーションPNG等)を、デコード前に
                # 明確に拒否する(Codexレビュー指摘、Minor対応: 以前は
                # 最初のフレームだけを黙って静止画として変換していた)。
                if getattr(img, "n_frames", 1) != 1:
                    raise PanelPixelConvertError(
                        f"複数フレームの画像(アニメーションPNG等)は対象外です: "
                        f"{path}(frames={img.n_frames})"
                    )
                img.load()  # ここで初めて全体をデコードする(破損検出)

                normalized = ImageOps.exif_transpose(img)
                if normalized is None:
                    normalized = img
                if normalized.mode not in ("RGB", "RGBA"):
                    has_alpha = normalized.mode in ("RGBA", "LA", "PA") or (
                        normalized.mode == "P" and "transparency" in normalized.info
                    )
                    normalized = normalized.convert("RGBA" if has_alpha else "RGB")
                return normalized.copy()
    except PanelPixelConvertError:
        raise
    except (Image.DecompressionBombError, Image.DecompressionBombWarning) as e:
        # DecompressionBombWarningはDecompressionBombErrorとは別系統の
        # クラス(共通の親はException)であり、以前は明示的にcatchしておらず
        # 素のまま漏れていた(2回目のCodexレビュー指摘、Minor対応:
        # 警告をエラー化した場合〔ピクセル数がPillowの閾値の1〜2倍〕は
        # DecompressionBombWarningが、閾値の2倍を超える場合は
        # DecompressionBombErrorが送出される。両方とも同じ
        # PanelPixelConvertErrorへ変換する)。
        raise PanelPixelConvertError(f"入力画像がdecompression bombの疑いがあります: {path}({e})") from e
    except (UnidentifiedImageError, OSError, ValueError) as e:
        raise PanelPixelConvertError(
            f"入力画像を読み込めません(破損または非対応形式の可能性): {path}({e})"
        ) from e


def convert_generation_to_panel(
    source_path,
    dest_path,
    panel_no=1,
    generation_width=1536,
    generation_height=640,
    overwrite=False,
):
    """SDXL生成画像(source_path)を、five_panel_template.jsonのpanel_no
    コマのinnerへ実際にリサイズ・クロップし、PNGとしてdest_pathへ保存する。

    - 入力寸法がgeneration_width×generation_heightと異なる場合は明確に
      エラーにする(黙って別の縮小率で計算し直さない)。
    - 変換手順はscripts/one_panel_pilot.pyのcompute_panel_fit()が返す
      整数ピクセル契約(resize_to_px/crop_box_px/resampling_method)を
      そのまま使う。対象コマのinner座標はfive_panel_template.jsonから
      読み込む(ハードコードしない)。
    - 出力は一時ファイルへ書き込んでから`os.replace()`で確定させる
      (書き込み途中のファイルが最終パスへ現れない)。
    - dest_pathが既に存在する場合、overwrite=Falseなら拒否する。
    - source_pathとdest_pathが同一の場合は拒否する(元画像を上書きしない)。
    - 保存後、改めて画像を開いて寸法を再確認する。

    戻り値には、実際に適用したresize_to_px/crop_box_px/resampling_method・
    最終寸法・保存先パスを含める。
    """
    # 公開APIの入口でbool・型・範囲を検証し、依存先(compute_panel_fit()等)や
    # Pillowの内部例外(OverflowError等)がそのまま漏れないようにする
    # (Codexレビュー指摘、Minor対応: 以前はpanel_no=True等のbool境界を
    # 検証しておらず、極端に大きいgeneration_width/heightがcompute_panel_fit()
    # 内部で素のOverflowErrorになっていた)。
    for name, value in (
        ("panel_no", panel_no),
        ("generation_width", generation_width),
        ("generation_height", generation_height),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise PanelPixelConvertError(f"{name}は正の整数である必要があります(bool不可): {value!r}")
    if generation_width > MAX_INPUT_DIMENSION_PX or generation_height > MAX_INPUT_DIMENSION_PX:
        raise PanelPixelConvertError(
            f"generation_width/generation_heightが上限({MAX_INPUT_DIMENSION_PX}px)を"
            f"超えています: {generation_width}x{generation_height}"
        )
    if not isinstance(overwrite, bool):
        raise PanelPixelConvertError(f"overwriteはbool型である必要があります: {overwrite!r}")

    source_path = Path(source_path)
    dest_path = Path(dest_path)

    if source_path.resolve() == dest_path.resolve():
        raise PanelPixelConvertError(f"入力画像と出力先が同一です(元画像を上書きしません): {source_path}")

    try:
        template = opp.load_five_panel_template()
        geometry = opp.get_panel_geometry(template, panel_no)
        inner = geometry["inner"]
        fit = opp.compute_panel_fit(generation_width, generation_height, inner["width"], inner["height"])
    except opp.PilotError as e:
        # panel_pixel_convert.pyの公開APIはPanelPixelConvertError単一種で
        # 失敗を表す契約とする(Codexレビュー指摘、Minor対応: 以前は
        # PanelPixelConvertErrorとopp.PilotErrorの2種類が呼び出し側から
        # 見え、単一のexcept節で安全に扱えなかった)。
        raise PanelPixelConvertError(f"寸法計算に失敗しました: {e}") from None

    resize_to_px = fit["resize_to_px"]
    crop_box_px = fit["crop_box_px"]
    resampling_name = fit["resampling_method"]
    if resampling_name not in _RESAMPLING_FILTERS:
        raise PanelPixelConvertError(f"未対応のリサンプリング方式です: {resampling_name!r}")

    # img.sizeはEXIF orientation正規化「後」の寸法である
    # (_open_and_normalize_image()が返す時点で既に適用済み)。
    # generation_width×generation_heightとの一致判定もこの正規化後の
    # 寸法に対して行う(Review B指摘、Minor対応: 保存上の寸法〔正規化前〕
    # なのか正規化後の寸法なのか、文書上どちらとも読める表現になっていた
    # ため明記する。decompression bomb対策の面積・辺長上限は正規化前
    # 〔保存寸法〕に対して適用される、_open_and_normalize_image()参照)。
    img = _open_and_normalize_image(source_path)
    try:
        if img.size != (generation_width, generation_height):
            raise PanelPixelConvertError(
                f"入力画像の寸法が期待値と異なります: 実際={img.size[0]}x{img.size[1]}、"
                f"期待={generation_width}x{generation_height}"
                "(黙って別の縮小率では計算しません。正しい生成解像度の画像を渡してください)"
            )

        resized = img.resize(
            (resize_to_px["width"], resize_to_px["height"]),
            _RESAMPLING_FILTERS[resampling_name],
        )
        try:
            box = (
                crop_box_px["left"],
                crop_box_px["upper"],
                crop_box_px["right"],
                crop_box_px["lower"],
            )
            cropped = resized.crop(box)
            try:
                if cropped.size != (inner["width"], inner["height"]):
                    raise PanelPixelConvertError(
                        f"クロップ後の寸法がinnerと一致しません: {cropped.size} != "
                        f"({inner['width']}, {inner['height']})"
                    )

                dest_path.parent.mkdir(parents=True, exist_ok=True)

                fd, tmp_path_str = tempfile.mkstemp(
                    dir=str(dest_path.parent), prefix=f".{dest_path.name}.tmp-", suffix=".png"
                )
                tmp_path = Path(tmp_path_str)
                try:
                    with os.fdopen(fd, "wb") as f:
                        cropped.save(f, format="PNG")

                    # os.replace()/os.link()する前に一時ファイル自体を検証する
                    # (Codexレビュー指摘、Major対応: 以前はos.replace()で
                    # destを確定させた後に検証していたため、検証失敗時に
                    # overwrite=True時の既存の正常な出力ファイルを回復できず、
                    # 破損した一時ファイルの内容がdestに残ってしまっていた)。
                    # Pillow由来の例外もPanelPixelConvertErrorへ統一する
                    # (公開APIの例外型契約を維持する)。
                    try:
                        with Image.open(tmp_path) as verify_img:
                            verify_img.load()
                            if verify_img.format != "PNG":
                                raise PanelPixelConvertError(
                                    f"一時ファイルの形式がPNGではありません: {verify_img.format!r}"
                                )
                            if verify_img.size != (inner["width"], inner["height"]):
                                raise PanelPixelConvertError(
                                    f"一時ファイルの寸法が一致しません: {verify_img.size} != "
                                    f"({inner['width']}, {inner['height']})"
                                )
                    except PanelPixelConvertError:
                        raise
                    except (UnidentifiedImageError, OSError, ValueError) as e:
                        raise PanelPixelConvertError(f"一時ファイルの検証に失敗しました: {e}") from None

                    if overwrite:
                        os.replace(tmp_path, dest_path)
                        tmp_path = None  # os.replace()がtmp_pathを消費した(改名済み)
                    else:
                        # overwrite=False時は、`os.link()`の
                        # FileExistsError自体を「存在しなければ作成」の
                        # アトミック判定として使う(2回目のCodexレビュー
                        # 指摘、Major対応: 以前はO_CREAT|O_EXCLで空の
                        # プレースホルダーを確保してから最終的に
                        # os.replace()する2段階方式だったため、検証失敗時に
                        # プレースホルダーを掃除するコードが、その間に
                        # 別プロセスが正当に書き込んだ内容まで誤って
                        # 削除しうるバグを持っていた。os.link()なら
                        # dest_pathを一切unlinkしないため、そのバグの
                        # 発生条件自体がなくなる)。
                        try:
                            os.link(tmp_path, dest_path)
                        except FileExistsError:
                            raise PanelPixelConvertError(
                                f"出力先が既に存在します(overwrite未指定): {dest_path}"
                            ) from None
                finally:
                    if tmp_path is not None:
                        tmp_path.unlink(missing_ok=True)
            finally:
                cropped.close()
        finally:
            resized.close()
    finally:
        img.close()

    # 保存後、改めて開いて寸法・形式を再確認する(書き込み内容そのものを
    # 信用しない。上記の置換前検証と合わせた二重確認)。Pillow由来の例外も
    # PanelPixelConvertErrorへ統一する。
    try:
        with Image.open(dest_path) as saved:
            saved.load()
            if saved.format != "PNG":
                raise PanelPixelConvertError(f"保存後の画像形式がPNGではありません: {saved.format!r}")
            if saved.size != (inner["width"], inner["height"]):
                raise PanelPixelConvertError(
                    f"保存後の画像寸法が一致しません: {saved.size} != "
                    f"({inner['width']}, {inner['height']})"
                )
    except PanelPixelConvertError:
        raise
    except (UnidentifiedImageError, OSError, ValueError) as e:
        raise PanelPixelConvertError(f"保存後の画像検証に失敗しました: {e}") from None

    return {
        "source_path": str(source_path),
        "dest_path": str(dest_path),
        "panel_no": panel_no,
        "generation_size": {"width": generation_width, "height": generation_height},
        "resize_to_px": resize_to_px,
        "crop_box_px": crop_box_px,
        "resampling_method": resampling_name,
        "final_size": {"width": inner["width"], "height": inner["height"]},
        # safe_area内へ人物が収まっている保証はプロンプト側の努力目標であり、
        # このピクセル変換自体は検証できない(ONE_PANEL_PILOT.md参照)。
        # 実際に人物が意図通りの位置にいるかは、次工程の画像内容検査が必要。
        "safe_area_containment_verified": False,
    }
