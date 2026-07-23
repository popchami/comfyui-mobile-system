# 書記官正本(参照画像)

異世界ニホン4コマ/5コマ構成マンガ用のキャラクター参照画像。正本はGitHub
Releaseにアセットとして保管し、Gitツリーには含めない。1つのZIP
(`scribe_complete_archive_v1.zip`)から expressions/turnaround/equipment
の3カテゴリを配置する。

## このディレクトリの構成

Git管理下(常に存在):

- `packages.json` — 正本ZIPの取得元・SHA-256・容量・ZIP内部構成、および
  収録する3カテゴリ(expressions/turnaround/equipment)の定義
- `manifest.json` — 表情(expressions)カテゴリの、表情タグ(31種、ハルト・
  ナツキ・アキラ・フユミと同一のタグ集合)から実ファイル名への対応表
- `turnaround/manifest.json` — 4方向立ち絵カテゴリの、論理タグ
  (`front`/`left-profile`/`back`/`right-profile`)から実ファイル名への
  対応表。4枚とも887×1774で寸法均一
- `equipment/manifest.json` — 書記局章(emblem)を、既存のequipmentカテゴリの
  論理タグ`official-scribe-bureau-emblem`として登録する対応表。新規emblem
  categoryは追加せず、既存の3category構成をそのまま流用
- `README.md` — このファイル

取得後にのみ生成される(Git管理外、`.gitignore`対象):

- `images/` — 表情PNG31枚(1254×1254)
- `turnaround/images/` — 4方向立ち絵PNG4枚(887×1774)
- `equipment/images/` — 書記局章PNG1枚(1254×1254)

## 取得方法

```bash
python3 scripts/fetch_reference_images.py --character scribe
```

`packages.json`の`download_url`(GitHub Releaseの固定タグURL、`latest`は
使わない)からZIPを1回だけ取得し、SHA-256・容量を照合したうえで、
expressions/turnaround/equipmentの3カテゴリすべてを検証してから、
まとめて原子的に配置する(1カテゴリでも検証に失敗すれば、いずれの
カテゴリも配置しない)。

## 正本の情報

| 項目 | 値 |
|---|---|
| ファイル名(Release公開時) | `scribe_complete_archive_v1.zip` |
| SHA-256 | `e1674d69d81f6a72edf2156e7cf6e6d8854ac2ada19b5d4420564df9433ec476` |
| 容量 | 70,937,890 bytes(約67.7MB) |
| 画像数合計 | 36枚(expressions31 + turnaround4 + equipment1) |
| Release タグ | `scribe-complete-archive-v1` |

固定仕様:
- 濃い中間紫のロングアウター(金縁・地紋)
- 赤いボブと編み込み、丸眼鏡、鳩のかんざし
- 左手にタブレット、右手にペン
- 書記局章は円+中央の筆+左右対称の巻物で構成
- 腕章・タブレット・背面上部に同一の書記局章を使用

表情の基準顔(`00-neutral.png`)は、4方向立ち絵の正面から抽出した同一人物・
同一画角のものを正本とする。

## 不採用ファイル

以下は転送時に破損していた旧ファイルであり、正本には一切使用していない。

- `scribe_complete_archive_v1.zip`(初回転送分、EOCD欠落で不正なZIP)
- `scribe_complete_archive_v1-1.zip`(再転送分、初回分と同一SHA-256で同様に不正)

正本は`scribe_complete_archive_v1_rebuilt.zip`(新ファイル名で再構築されたもの)
のバイト列のみであり、Release公開時はこのバイト列に`scribe_complete_archive_v1.zip`
という名前を付けてアセットとしてアップロードする。

## 論理IDの例

- `scribe/neutral.png` → 表情(category省略時は`expressions`扱い、
  ハルトと同じ後方互換形式)
- `scribe/surprise-medium.png` → 表情
- `scribe/turnaround/front.png` → 4方向立ち絵(正面)
- `scribe/turnaround/left-profile.png` → 4方向立ち絵(画面左向きの横顔)
- `scribe/equipment/official-scribe-bureau-emblem.png` → 書記局章

解決ロジックは`scripts/resolve_reference_image.py`参照。
