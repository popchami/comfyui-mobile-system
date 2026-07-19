# ナツキ正本(参照画像)

異世界ニホン4コマ/5コマ構成マンガ用のキャラクター参照画像。正本はGitHub
Releaseにアセットとして保管し、Gitツリーには含めない。1つのZIP
(`natsuki_complete_set_v2.zip`)から expressions/turnaround/equipment
の3カテゴリを配置する(ハルトのような複数ZIP分割ではない)。

## このディレクトリの構成

Git管理下(常に存在):

- `packages.json` — 正本ZIPの取得元・SHA-256・容量・ZIP内部構成、および
  収録する3カテゴリ(expressions/turnaround/equipment)の定義
- `manifest.json` — 表情(expressions)カテゴリの、表情タグ(31種、ハルトと
  同一のタグ集合)から実ファイル名への対応表
- `turnaround/manifest.json` — 4方向立ち絵カテゴリの、論理タグ
  (`front`/`left-profile`/`back`/`right-profile`)から実ファイル名への
  対応表。4枚とも構図差により画像サイズが異なるため、ファイルごとの
  期待サイズも個別に記録する
- `equipment/manifest.json` — 装備・紋カテゴリの、論理タグから実ファイル名
  への対応表(`crest-hariyumi-himawari`・`mitsugake-right`の2種)
- `README.md` — このファイル

取得後にのみ生成される(Git管理外、`.gitignore`対象):

- `images/` — 表情PNG31枚(1254×1254)
- `turnaround/images/` — 4方向立ち絵PNG4枚(寸法は4枚それぞれ異なる)
- `equipment/images/` — 装備・紋PNG2枚
- `index.html` — ZIP同梱の人間向けプレビューギャラリー

## 取得方法

```bash
python3 scripts/fetch_reference_images.py --character natsuki
```

`packages.json`の`download_url`(GitHub Releaseの固定タグURL、`latest`は
使わない)からZIPを1回だけ取得し、SHA-256・容量を照合したうえで、
expressions/turnaround/equipmentの3カテゴリすべてを検証してから、
まとめて原子的に配置する(1カテゴリでも検証に失敗すれば、いずれの
カテゴリも配置しない)。

## 正本の情報

| 項目 | 値 |
|---|---|
| ファイル名 | `natsuki_complete_set_v2.zip` |
| SHA-256 | `62be11c467c5ec59752a9413ea74268655e391becac7fa4cecb6da760a1c90cb` |
| 容量 | 67,106,972 bytes(約64.0MB) |
| 画像数合計 | 37枚(expressions31 + turnaround4 + equipment2) |
| Release タグ | `natsuki-complete-set-v2` |

固定事項(ZIP同梱README.txt): 女性、黒髪ポニーテール、黄色系ノースリーブ
のフード付きベスト、白い和風インナー、青灰色の袴風パンツ、左手で和式短弓
を持つ、右手に三つ弽を着けて弦を引く、背紋は張弓向日葵紋。単体の弓画像は
未確定のため未収録(弓は4方向立ち絵内に描画済み)。

## 論理IDの例

- `natsuki/neutral.png` → 表情(category省略時は`expressions`扱い、
  ハルトと同じ後方互換形式)
- `natsuki/surprise-medium.png` → 表情
- `natsuki/turnaround/front.png` → 4方向立ち絵(正面)
- `natsuki/turnaround/left-profile.png` → 4方向立ち絵(画面左向きの横顔)
- `natsuki/equipment/crest-hariyumi-himawari.png` → 張弓向日葵紋
- `natsuki/equipment/mitsugake-right.png` → 右手用三つ弽

解決ロジックは`scripts/resolve_reference_image.py`参照。
