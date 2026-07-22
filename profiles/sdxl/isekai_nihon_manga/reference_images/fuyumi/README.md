# フユミ正本(参照画像)

異世界ニホン4コマ/5コマ構成マンガ用のキャラクター参照画像。正本はGitHub
Releaseにアセットとして保管し、Gitツリーには含めない。1つのZIP
(`fuyumi_complete_archive_v1.zip`)から expressions/turnaround の2カテゴリ
を配置する(装備・紋カテゴリは今回未収録)。

## このディレクトリの構成

Git管理下(常に存在):

- `packages.json` — 正本ZIPの取得元・SHA-256・容量・ZIP内部構成、および
  収録する2カテゴリ(expressions/turnaround)の定義
- `manifest.json` — 表情(expressions)カテゴリの、表情タグ(31種、ハルト・
  ナツキ・アキラと同一のタグ集合)から実ファイル名への対応表
- `turnaround/manifest.json` — 4方向立ち絵カテゴリの、論理タグ
  (`front`/`left-profile`/`back`/`right-profile`)から実ファイル名への
  対応表。4枚とも887×1774で寸法均一
- `README.md` — このファイル

取得後にのみ生成される(Git管理外、`.gitignore`対象):

- `images/` — 表情PNG31枚(1254×1254)
- `turnaround/images/` — 4方向立ち絵PNG4枚(887×1774)

## 取得方法

```bash
python3 scripts/fetch_reference_images.py --character fuyumi
```

`packages.json`の`download_url`(GitHub Releaseの固定タグURL、`latest`は
使わない)からZIPを1回だけ取得し、SHA-256・容量を照合したうえで、
expressions/turnaroundの2カテゴリすべてを検証してから、まとめて原子的に
配置する(1カテゴリでも検証に失敗すれば、いずれのカテゴリも配置しない)。

## 正本の情報

| 項目 | 値 |
|---|---|
| ファイル名 | `fuyumi_complete_archive_v1.zip` |
| SHA-256 | `7711b6efe5535564a3f6c13c39d957685ea3390fb75d2dd197d2ad1d151c9eca` |
| 容量 | 72,783,398 bytes(約69.4MB) |
| 画像数合計 | 35枚(expressions31 + turnaround4) |
| Release タグ | `fuyumi-complete-archive-v1` |

固定事項(ZIP同梱README.md): 4方向立ち絵の構図は以下の通り。
- 正面: 薬箱本体は身体の後ろに収まり、肩紐のみ見える
- 左側面: 薬箱は背中に垂直密着し、青い薬瓶1本が見える
- 背面: 薬箱に青・透明・オレンジの薬瓶3本を横一列で配置
- 右側面: 薬箱は背中に垂直密着し、オレンジ色の薬瓶1本が見える

表情の基準顔(`00-neutral.png`)は、4方向立ち絵の正面から抽出した同一人物・
同一画角のものを正本とする。

## 今回採用しなかったZIP外・旧候補ファイル

以下は制作途中の候補、または表情のみの旧バージョンであり、正本
(`fuyumi_complete_archive_v1.zip`)に統合済みのため、このcategory定義には
一切登録していない。`fetch_reference_images.py`の取得対象にも含まれない。

- `fuyumi_expression_set_v1.zip`(表情31枚のみの旧版、4方向立ち絵を含まない)
- `fuyumi-right-profile-orange-clear-blue.png`(ZIP外の制作途中候補画像)

## 論理IDの例

- `fuyumi/neutral.png` → 表情(category省略時は`expressions`扱い、
  ハルトと同じ後方互換形式)
- `fuyumi/surprise-medium.png` → 表情
- `fuyumi/turnaround/front.png` → 4方向立ち絵(正面)
- `fuyumi/turnaround/left-profile.png` → 4方向立ち絵(画面左向きの横顔)

解決ロジックは`scripts/resolve_reference_image.py`参照。
