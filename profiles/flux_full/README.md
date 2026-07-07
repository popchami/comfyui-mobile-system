# Flux Full

Flux.1 Dev と Flux.2 Klein の両方を含む統合環境です。

## 元ZIP

```text
flux_full.zip
```

## 判断

Flux Fullは、Flux.1単体・Flux.2単体とは別に管理します。
同名ファイルでも中身が違うものがあります。

特に注意:

- `comfyui_mobile.html` はFlux1/Flux2単体版と中身が違う
- `download_ui.ipynb` はFlux Full専用版
- `download_list_flux1.txt` と `download_list_flux2.txt` が分かれている

## 置く予定のファイル

```text
setup_flux1_dev.ipynb
setup_flux2_klein.ipynb
backup_flux1.ipynb
backup_flux2.ipynb
download_list_flux1.txt
download_list_flux2.txt
download_ui.ipynb
download_extra.ipynb
comfyui_mobile.html
world_setting.txt
flux1_dev_*GB_workflow_v2ollama.json
flux2_klein_*GB_workflow_v2ollama.json
wildcards/
```

## 注意

Flux Fullは「全部入り」環境として扱います。
単体環境のファイルを安易に上書きしないでください。
