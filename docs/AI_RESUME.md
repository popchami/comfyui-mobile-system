# AI_RESUME

## Current
- profiles/flux1_dev/icon/ は OllamaGemini 不使用方針に合わせて修正中。
- custom_nodes_memo_icon.txt は修正済み。
  - ComfyUI-OllamaGemini / BRIA_RMBG / ConvertRasterToVector / SaveSVG 前提を撤回。
  - 現在の安全な動作対象は PNGアイコン生成まで。
- download_list_flux1.txt はicon用に整理済み。
  - NSFW系LoRA/checkpoint記述を削除。
  - Flux.1 Dev / text encoder / VAE / upscaler / Ollama のみに整理。

## Next
- profiles/flux1_dev/icon/setup_flux1_dev.ipynb を実行可能なnotebook形式として再確認する。
- profiles/flux1_dev/icon/comfyui_icon_mobile.html の生成APIは、現状PNG保存までの構成として扱う。
- profiles/flux1_dev/icon/flux1_dev_icon_16GB_workflow_v2ollama.json に残っているOllamaGemini由来ノードを、PNG保存のみのworkflowへ整理する。
- RunPod上で setup_flux1_dev.ipynb → download_ui.ipynb → comfyui_icon_mobile.html の順に実機検証する。

## Blocked / 未確定
- SVG化・背景透過は未確定。
- OllamaGeminiは使わないため、BRIA_RMBG / ConvertRasterToVector / SaveSVG は採用しない。
- SVG化を再開する場合は、採用する別ノードを決めてから /object_info でAPI形式を確認する。
