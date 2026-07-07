# profiles

RunPod / ComfyUIで実際に使う環境一式を置く場所です。

## 基本ルール

1つの生成環境は、できるだけ1つのフォルダにまとめます。

例:

```text
profiles/flux1_dev/pixelart/24gb/
```

この中に、setup、workflow、download_list、HTML UI、backupなどを置きます。

## 置くもの

- setup用Notebook
- backup用Notebook
- workflow JSON
- HTML UI
- download_list
- wildcards
- README

## 置かないもの

- モデル本体
- LoRA本体
- 生成画像
- APIキー
- PAT
- パスワード
