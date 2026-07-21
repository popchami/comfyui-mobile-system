# アキラ正本(参照画像)

異世界ニホン4コマ/5コマ構成マンガ用のキャラクター参照画像。正本はGitHub
Releaseにアセットとして保管し、Gitツリーには含めない。1つのZIP
(`akira_complete_archive_v1.zip`)から expressions/turnaround/equipment
の3カテゴリを配置する(ナツキと同じ、1ZIP・複数カテゴリ方式)。

## このディレクトリの構成

Git管理下(常に存在):

- `packages.json` — 正本ZIPの取得元・SHA-256・容量・ZIP内部構成、および
  収録する3カテゴリ(expressions/turnaround/equipment)の定義
- `manifest.json` — 表情(expressions)カテゴリの、表情タグ(31種、ハルト・
  ナツキと同一のタグ集合)から実ファイル名への対応表
- `turnaround/manifest.json` — 4方向立ち絵カテゴリの、論理タグ
  (`front`/`left-profile`/`back`/`right-profile`)から実ファイル名への
  対応表。4枚とも887×1774で寸法均一
- `equipment/manifest.json` — 装備(符槌・陣札・符釘)カテゴリの、論理タグ
  から実ファイル名への対応表(13種)。ZIP内ではhammer/talisman/nailの
  3サブフォルダに分かれているが、取得時にプレフィックス付きでフラット化
  して配置する(下記「装備のフラット化」参照)
- `README.md` — このファイル

取得後にのみ生成される(Git管理外、`.gitignore`対象):

- `images/` — 表情PNG31枚(1254×1254)
- `turnaround/images/` — 4方向立ち絵PNG4枚(全て887×1774)
- `equipment/images/` — 装備PNG13枚(フラット化済み、寸法は下記参照)
- `index.html` — ZIP同梱の人間向けプレビューギャラリー(存在する場合)

## 取得方法

```bash
python3 scripts/fetch_reference_images.py --character akira
```

`packages.json`の`download_url`(GitHub Releaseの固定タグURL、`latest`は
使わない)からZIPを1回だけ取得し、SHA-256・容量を照合したうえで、
expressions/turnaround/equipmentの3カテゴリすべてを検証してから、
まとめて原子的に配置する(1カテゴリでも検証に失敗すれば、いずれの
カテゴリも配置しない)。

## 装備のフラット化(equipment)

ZIP内の実際の構成は次の通り、3サブフォルダに分かれている。

```
equipment/hammer/00-broad-maple-face.png ...(4枚)
equipment/talisman/00-buff-front.png ...(6枚)
equipment/nail/00-preloaded-side-left-long.png ...(3枚)
```

論理上は1つの`equipment`カテゴリとして扱い、配置後は`hammer-`/
`talisman-`/`nail-`のプレフィックスを付けて`equipment/images/`直下へ
フラット化する(例: `hammer/00-broad-maple-face.png` →
`equipment/images/hammer-00-broad-maple-face.png`)。この変換は
`equipment/manifest.json`の`source_file`(ZIP内の実パス)と`file`
(配置後のファイル名)の対応、および`scripts/fetch_reference_images.py`の
`flatten`機能で行う。

寸法は13枚中12枚が887×1774、`nail-ranged-flight-long`(遠打ち状態)のみ
1024×1536で異なる(元画像の寸法は変更していない)。

## ZIP内に含まれるが正本資産として登録していないもの

以下はZIP内に含まれるが、`packages.json`・categoryのmanifestには一切
登録しておらず、`scripts/fetch_reference_images.py`による取得・配置の
対象外(保存用資料としてZIP内にのみ残る)。

- `character/reference/00-approved-fullbody.png` — 承認済み全身基準画像
  (turnaroundとは別の単体資料)
- `crest/crest-ofuda-momiji.jpg` — 家紋(封印札と紅葉)。PNGではなくJPG
  形式のため、既存の論理ID解決(`.png`拡張子前提)にも未対応。追加は
  今回の作業範囲外
- `previews/` — 確認用一覧画像4枚(ZIP同梱README.md記載により、正本
  ではなく人間による確認用の資料)
- ZIP同梱の`README.md`・`manifest.json`(ZIP独自形式)・`SHA256SUMS.txt`

## 正本の情報

| 項目 | 値 |
|---|---|
| ファイル名 | `akira_complete_archive_v1.zip` |
| SHA-256 | `1c34b24d830902ff3f63aa748956deed9da0d687e5177ef4ebda209200d8ffd7` |
| 容量 | 119,070,569 bytes(約113.5MB) |
| 画像数合計(登録分) | 48枚(expressions31 + turnaround4 + equipment13) |
| Release タグ(案・未作成) | `akira-complete-archive-v1` |

固定事項(ZIP同梱README.md): 若い日本人男性、短い濃茶髪、琥珀色の目、
細い長方形の銀縁眼鏡。抑えた深紅の半袖アウター(黒と金の縁取り)、黄色の
インナーの下に白襟を一枚重ねる(襟の順序: 肌→白襟→黄色インナー→黒・赤
アウター)。黒い膨らみのある袴風パンツ、脚絆、茶色のブーツ。胸の飾りは
トンボ。体の真横の工具入れに符釘・陣札・符槌を収納。刀は使用しない。
背中の家紋は円の中に封印札と紅葉。役割は味方へのバフ・敵へのデバフを行う
支援役。背面では黒い立ち襟が内襟を覆うため白襟は見えない。

## 論理IDの例

- `akira/neutral.png` → 表情(category省略時は`expressions`扱い、
  ハルト・ナツキと同じ後方互換形式)
- `akira/surprise-medium.png` → 表情
- `akira/turnaround/front.png` → 4方向立ち絵(正面)
- `akira/turnaround/left-profile.png` → 4方向立ち絵(画面左向きの横顔)
- `akira/equipment/hammer-broad-maple-face.png` → 符槌(紅葉面)
- `akira/equipment/talisman-buff-front.png` → 加護札(正面)
- `akira/equipment/nail-ranged-flight-long.png` → 符釘(遠打ち状態)

解決ロジックは`scripts/resolve_reference_image.py`参照(この論理ID解決
自体は`file`のみを見るため、フラット化・source_fileの仕組みを意識する
必要はない)。
