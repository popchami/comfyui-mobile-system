# ZIP確認結果

アップロードされたZIPの中身を確認した記録です。
ファイル名だけでなく、SHA-256ハッシュで中身の違いも確認します。

## 確認済みZIP

| ZIP | 種類 | 配置先 |
|---|---|---|
| `flux1dev_pixelart.zip` | Flux.1 Dev PixelArt 24GB | `profiles/flux1_dev/pixelart/24gb/` |
| `sdxl_chibi_pixelart.zip` | SDXL Chibi / PixelArt | `profiles/sdxl/` |
| `flux_2_klein.zip` | Flux.2 Klein単体 | `profiles/flux2_klein/normal/` |
| `flux1_dev.zip` | Flux.1 Dev単体 | `profiles/flux1_dev/normal/` |
| `flux_full.zip` | Flux.1 + Flux.2統合 | `profiles/flux_full/` |
| `kickkick_icon_spec_street_v1.zip` | Kick×Kickアイコン仕様書 | `specs/icons/` |

---

## 重要な判定

### 同じ内容だったもの

以下は複数ZIPで中身が完全一致していました。

```text
download_extra.ipynb
```

以下はFlux.1 / Flux.2 / SDXL / PixelArtでは同じですが、Flux Fullでは別版でした。

```text
download_ui.ipynb
```

### 同名だが中身が違うもの

```text
comfyui_mobile.html
```

- Flux.1単体版とFlux.2単体版は同じ
- Flux Full版は別物

```text
backup_flux2.ipynb
```

- Flux.2単体版とFlux Full内のものはハッシュが違う

---

## 配置方針

### Flux.1 Dev PixelArt 24GB

```text
profiles/flux1_dev/pixelart/24gb/
├── setup_pixelart.ipynb
├── backup_pixelart.ipynb
├── download_list_pixelart.txt
├── pixelart_24GB_workflow_v1.json
├── comfyui_pixelart.html
├── download_ui.ipynb
└── download_extra.ipynb
```

### SDXL

```text
profiles/sdxl/
├── setup_sdxl.ipynb
├── backup_sdxl.ipynb
├── download_list_sdxl.txt
├── download_ui.ipynb
├── download_extra.ipynb
├── chibi/
│   ├── sdxl_chibi_24GB_workflow_v1.json
│   └── comfyui_sdxl_chibi.html
└── pixelart/
    ├── sdxl_pixelart_24GB_workflow_v1.json
    └── comfyui_sdxl_pixelart.html
```

### Flux.1 Dev単体

```text
profiles/flux1_dev/normal/
├── setup_flux1_dev.ipynb
├── backup_flux1.ipynb
├── download_list.txt
├── download_ui.ipynb
├── download_extra.ipynb
├── comfyui_mobile.html
├── world_setting.txt
├── wildcards/
└── flux1_dev_*GB_workflow_v2ollama.json
```

### Flux.2 Klein単体

```text
profiles/flux2_klein/normal/
├── setup_flux2_klein.ipynb
├── backup_flux2.ipynb
├── download_list.txt
├── download_ui.ipynb
├── download_extra.ipynb
├── comfyui_mobile.html
├── world_setting.txt
├── wildcards/
└── flux2_klein_*GB_workflow_v2ollama.json
```

### Flux Full

```text
profiles/flux_full/
├── setup_flux1_dev.ipynb
├── setup_flux2_klein.ipynb
├── backup_flux1.ipynb
├── backup_flux2.ipynb
├── download_list_flux1.txt
├── download_list_flux2.txt
├── download_ui.ipynb
├── download_extra.ipynb
├── comfyui_mobile.html
├── world_setting.txt
├── wildcards/
├── flux1_dev_*GB_workflow_v2ollama.json
└── flux2_klein_*GB_workflow_v2ollama.json
```

### Kick Icon

```text
specs/icons/ICON_SPEC_street.md
```

---

## 注意

GitHubにモデル本体、LoRA本体、生成画像本体は置きません。
GitHubには環境再現に必要な設定・Workflow・HTML・リスト・仕様書を置きます。
