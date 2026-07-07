# ZIP実ファイル配置計画

## 目的

アップロード済みZIPの中身を、GitHub上の正しいフォルダへ配置するための指示書です。

このファイルは、Claude CodeやTermuxに作業を任せるときの基準として使います。

---

## 重要ルール

- ファイル名だけで同一判定しない
- 同名でも中身が違う可能性があるため、必要ならSHA-256で確認する
- 既存ファイルを上書きする前に必ず差分確認する
- モデル本体、LoRA本体、生成画像はGitHubに置かない
- APIキー、PAT、パスワードは絶対に置かない

---

## 1. flux1dev_pixelart.zip

配置先:

```text
profiles/flux1_dev/pixelart/24gb/
```

配置:

```text
pixelart_24GB_workflow_v1.json
setup_pixelart.ipynb
backup_pixelart.ipynb
download_list_pixelart.txt
comfyui_pixelart.html
download_ui.ipynb
download_extra.ipynb
```

---

## 2. sdxl_chibi_pixelart.zip

共通ファイル配置先:

```text
profiles/sdxl/
```

配置:

```text
setup_sdxl.ipynb
backup_sdxl.ipynb
download_list_sdxl.txt
download_ui.ipynb
download_extra.ipynb
```

Chibi配置先:

```text
profiles/sdxl/chibi/
```

配置:

```text
sdxl_chibi_24GB_workflow_v1.json
comfyui_sdxl_chibi.html
```

PixelArt配置先:

```text
profiles/sdxl/pixelart/
```

配置:

```text
sdxl_pixelart_24GB_workflow_v1.json
comfyui_sdxl_pixelart.html
```

---

## 3. flux1_dev.zip

配置先:

```text
profiles/flux1_dev/normal/
```

配置:

```text
setup_flux1_dev.ipynb
backup_flux1.ipynb
download_list.txt
download_ui.ipynb
download_extra.ipynb
comfyui_mobile.html
world_setting.txt
flux1_dev_16GB_workflow_v2ollama.json
flux1_dev_24GB_workflow_v2ollama.json
flux1_dev_32GB_workflow_v2ollama.json
flux1_dev_48GB_workflow_v2ollama.json
wildcards/
```

---

## 4. flux_2_klein.zip

配置先:

```text
profiles/flux2_klein/normal/
```

配置:

```text
setup_flux2_klein.ipynb
backup_flux2.ipynb
download_list.txt
download_ui.ipynb
download_extra.ipynb
comfyui_mobile.html
world_setting.txt
flux2_klein_16GB_workflow_v2ollama.json
flux2_klein_24GB_workflow_v2ollama.json
flux2_klein_32GB_workflow_v2ollama.json
flux2_klein_48GB_workflow_v2ollama.json
wildcards/
```

---

## 5. flux_full.zip

配置先:

```text
profiles/flux_full/
```

配置:

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
flux1_dev_16GB_workflow_v2ollama.json
flux1_dev_24GB_workflow_v2ollama.json
flux1_dev_32GB_workflow_v2ollama.json
flux1_dev_48GB_workflow_v2ollama.json
flux2_klein_16GB_workflow_v2ollama.json
flux2_klein_24GB_workflow_v2ollama.json
flux2_klein_32GB_workflow_v2ollama.json
flux2_klein_48GB_workflow_v2ollama.json
wildcards/
```

注意:

`flux_full.zip` の `comfyui_mobile.html` と `download_ui.ipynb` は単体版と中身が違うため、Flux Full専用として扱います。

---

## 6. kickkick_icon_spec_street_v1.zip

配置先:

```text
specs/icons/
```

配置:

```text
ICON_SPEC_street.md
```

元ZIP内では以下の場所にある:

```text
kickkick_icon_spec_bundle/ICON_SPEC_street.md
```

---

## 推奨コマンド例

Termux / Claude Codeで作業する場合は、ZIPを一時フォルダに展開してから、配置先へコピーします。

```bash
mkdir -p tmp_import
unzip flux1dev_pixelart.zip -d tmp_import/flux1dev_pixelart
```

その後、必要ファイルだけを正しい `profiles/` 配下へコピーします。

---

## 完了条件

以下が満たされたら実ファイル配置完了です。

- 各ZIPのファイルが対応する `profiles/` または `specs/` に配置されている
- `docs/ZIP_INVENTORY.md` と実ファイル構成が一致している
- 同名ファイルの上書きが発生していない
- 秘密情報が含まれていない
- モデル本体や生成画像が混ざっていない
