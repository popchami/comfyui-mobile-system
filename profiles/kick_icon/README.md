# Kick Icon

Kick×Kick用アイコン生成・仕様管理の場所です。

## 元ZIP

```text
kickkick_icon_spec_street_v1.zip
```

## 確認済みファイル

```text
kickkick_icon_spec_bundle/ICON_SPEC_street.md
```

## 判断

今回のZIPは実行環境ではなく、アイコン仕様書です。
仕様書本体は `specs/icons/` に置きます。

この `profiles/kick_icon/` は、将来的にKick Icon専用のComfyUI環境を作る場合の置き場所です。

## 将来置く可能性があるもの

```text
setup_kick_icon.ipynb
backup_kick_icon.ipynb
download_list_kick_icon.txt
kick_icon_workflow.json
comfyui_kick_icon.html
```

## 方針

不足ファイルがある場合は、Flux.1やSDXLなど既存環境を参考にして、Kick Icon専用版として新しく作成します。
単純コピーではなく、モデル名・Workflow名・HTML名・保存先をKick Icon用に調整します。
