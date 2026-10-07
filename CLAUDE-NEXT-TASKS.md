# Claude Code 向け独立タスク

## 前提

- Codex側は `outputs/liminal.js`、`outputs/audio.js`、閉鎖施設を作業中。両ファイルは編集しない。
- この文書のタスクは浮島の街に限定する。着手前に `git status --short` を確認し、他者の未コミット変更を上書きしない。
- 1タスク1コミット。生成物を含め、変更ファイルをタスク記載範囲内に収める。
- 現在値は浮島全体で約163 draw calls / 682,461 triangles、住宅GLBは約40,247 triangles × 9棟。最初に住宅負荷を下げ、物量追加はその後に行う。

## Task A：住宅LODの制作

**対象ファイル**

- 新規 `work/build_house_lod.py`
- 新規 `outputs/assets/aeolia-house-lod.glb`
- 新規 `outputs/assets/aeolia-house-lod.blend`
- 必要なら新規プレビュー画像1枚

**手順**

1. `work/build_house.py` と既存住宅の輪郭・材質名を再利用する。
2. 屋根、煙突、窓、鎧戸、玄関、バルコニーという識別要素を残し、細かな瓦、石積み、植物を削減する。
3. 材質別に結合してGLBを書き出す。追加依存は入れない。
4. Blenderのヘッドレス実行時に三角形数と材質バッチ数をassertする。

**受け入れ条件**

- 住宅1棟が5,000 triangles以下、4 material batches以下。
- 30m前後の距離で、既存住宅と同じ家系・屋根・窓配置に見える。
- 法線反転、浮いた部品、透明抜けがなく、全体の外接寸法が既存住宅と大きくずれない。

**実行テスト**

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --python work/build_house_lod.py
node work/test-controls.mjs
```

## Task B：住宅LODのゲーム統合

Task A完了後に着手する。

**対象ファイル**

- `outputs/aeolia.html`
- `work/asset-loader.mjs`
- `work/test-controls.mjs`

**手順**

1. 既存の材質別 `InstancedMesh` 読み込み処理を小さく拡張し、デスクトップは開始地点に近い2棟だけ既存住宅、残り7棟をLODにする。
2. スマートフォン判定時は9棟すべてLODにする。
3. 既存のfallbackとコリジョンproxyは維持する。LOD切替用ライブラリや新しい抽象化は追加しない。
4. テクスチャ種別の判定は既存の材質名と `textureMaterial` を再利用する。

**受け入れ条件**

- デスクトップで住宅由来の描画 triangles が約115k以下、スマートフォンで45k以下。
- 住宅バッチはデスクトップ8以下、スマートフォン4以下。
- 読み込み失敗時は既存fallbackが表示され、移動・衝突・発見・キャラクター選択に回帰がない。
- 浮島全体を実ブラウザで180k triangles以下へ近づける。未達なら数値と最大要因を記録して止め、景観を削って帳尻を合わせない。

**実行テスト**

```sh
node work/test-controls.mjs
node work/test-effects.mjs
node work/audit-game.mjs
```

加えて `outputs/aeolia.html?debug=1` をデスクトップ幅とスマートフォン幅で開き、開始地点・飛行中・住宅密集部のFPS / p95 / calls / trianglesを記録する。

## Task C：浮島用テクスチャ素材の制作

Task Aと並行可能。Task Bのファイルは触らない。

**対象ファイル**

- `work/make_textures.py`
- 新規 `outputs/assets/textures/island-life-atlas.png`
- 新規 `outputs/assets/textures/island-distance-atlas.png`
- 新規 `outputs/assets/textures/island-mark-mask.png`
- `outputs/assets/textures/GENERATED-ASSETS.md`

**手順**

1. 既存の画像生成方法に合わせ、Pythonで決定的に再生成できるようにする。
2. life atlasは布、花、箱、工具、時計盤、時刻表をまとめる。distance atlasは遠景住宅・塔の色面と汚れをまとめる。mark maskは濡れ、修理跡、土埃、足跡をまとめる。
3. 固有名詞や雰囲気だけの日本語を画像へ書き込まない。時刻表は判読不能な短線と数字程度に留める。

**受け入れ条件**

- life / distanceは各1024×1024、mark maskは512×512。
- 3枚合計3MB以下、継ぎ目・余白の色にじみ・意図しない透明縁がない。
- 既存の石、木、漆喰と並べても彩度やコントラストが浮かない。

**実行テスト**

```sh
python3 work/make_textures.py
python3 -c "from PIL import Image; from pathlib import Path; specs={'island-life-atlas.png':(1024,1024),'island-distance-atlas.png':(1024,1024),'island-mark-mask.png':(512,512)}; root=Path('outputs/assets/textures'); assert all(Image.open(root/n).size==s for n,s in specs.items()); assert sum((root/n).stat().st_size for n in specs)<3_000_000"
```

## Task D：浮島単独QAレポート

Task B完了後に着手する。修正実装はせず、問題を再現可能な形で報告する。

**対象ファイル**

- 新規 `FLOATING-ISLAND-QA.md`

**手順**

1. `DREAMCORE-ISLANDS-PLAN.md` の性能・コリジョン・視差・操作条件に沿って確認する。
2. PC幅とスマートフォン幅で、中央島、三つの外島、橋・階段、島裏、雲下復帰を巡る。
3. 各問題へURL、画面幅、座標、操作、期待結果、実結果、重要度を記録する。
4. 背景を目的地と誤認する箇所、8秒以上見どころがない移動区間、LOD切替の目立ち方を別項目で記録する。

**受け入れ条件**

- 30/60/120Hzの自動テスト結果を記載する。
- PC / スマートフォンのFPS、p95、draw calls、trianglesを開始地点と飛行中で記載する。
- 意図しない衝突、めり込み、カメラ抜け、透明面崩れは「なし」でも巡回地点を明記する。
- 修正候補は重要度順に最大10件。推測と再現確認済みを分ける。

**実行テスト**

```sh
node work/test-controls.mjs
node work/test-effects.mjs
node work/test-audio.mjs
node work/audit-game.mjs
git diff --check
```

## 競合回避

- 編集禁止：`outputs/liminal.js`、`outputs/audio.js`、`BACKROOMS-FACILITY-PLAN.md`、`IMPLEMENTATION-PROGRESS.md`。
- `outputs/aeolia.html`、`work/test-controls.mjs`、`work/asset-loader.mjs` はTask Bだけが編集する。Task A/C/Dは触らない。
- `work/make_textures.py` はTask Cだけが編集する。
- 既存GLB・BLENDを上書きせず、LODは別名で追加する。
- 公開、push、進捗ポイント更新はCodex側が行う。Claude Code側は担当コミットのハッシュと実測値を共有する。

---

# 追加で切り出せるタスク

Task A〜D完了後の作業。優先順位はE、F、G。各タスクを別コミットにし、開始前に `git pull --ff-only` と `git status --short` を実行する。

## Task E：浮島5地区の軽量モジュール制作

Codexと並行可能。ゲーム本体は編集しない。

**対象ファイル**

- 新規 `work/build_island_modules.py`
- 新規 `outputs/assets/aeolia-island-modules.glb`
- 新規 `outputs/assets/aeolia-island-modules.blend`
- 必要なら新規プレビュー画像1枚

**内容**

- 市場：屋台、花台、収穫箱
- 鐘楼：時計盤、鐘、ロープ、点検足場
- 風車：工具台、干し布の支持部、補修材
- 離宮：水盤縁、腰掛け、排水口
- 雲下停留所：ホーム、屋根、ベンチ、灯

各地区の主役は3種類以内にし、既存 `island-life-atlas.png` のUVを使う。ゲーム内配置、コリジョン、読み込み処理は実装しない。

**受け入れ条件**

- 合計45k triangles以下、12 material batches以下。
- モジュールごとに原点と外接寸法をBlenderスクリプト内で検査する。
- 反転面、重複面、浮いた部品がなく、10〜30mから用途を判別できる。
- Blenderヘッドレス再生成とNodeでのGLB解析が成功する。

## Task F：浮島の残存コリジョン修正

Task Eとは並行可能だが、Codexが `outputs/aeolia.html` を編集していない期間だけ着手する。着手時にCodexへ宣言する。

**対象ファイル**

- `outputs/aeolia.html`
- `work/test-controls.mjs`
- `FLOATING-ISLAND-QA.md` の追補だけ

**内容**

1. 離宮の列柱へ見た目と一致する円形コリジョンを追加。
2. 風車の羽根へ回転面を近似する薄いコリジョンを追加。回転中に閉じ込めないこと。
3. 遠景3D島12個を「着地できない遠景」として明示し、半径220mより外側から接近時に薄く霞ませる。地面判定は追加しない。
4. 中央島の崖際でカメラが岩へ入る再現経路を検査し、既存 `cameraBlockers` の形状だけで直せる場合のみ修正。

**受け入れ条件**

- 通常速度と最大速度、30/60/120Hzで列柱・風車をすり抜けない。
- 羽根に接触してもプレイヤーが内部へ固定されない。
- 遠景島が到達可能な外島と区別でき、追加draw callsは2以下。
- 既存の島裏、世界境界、雲下復帰テストを維持する。

## Task G：3ステージ横断QA

Task E/F完了後。修正実装はせず、検査と報告だけ行う。

**対象ファイル**

- 新規 `THREE-WORLD-QA.md`
- 必要なら新規 `work/test-world-entry.mjs` 1ファイル

**確認範囲**

- 世界選択から3ステージへの遷移、戻る操作、キャラクター選択の保持。
- PC・スマートフォンの移動、ドラッグ視点、消音、上昇・下降。
- 30/60/120Hz、開始地点と飛行中のFPS・p95・calls・triangles。
- 各ステージ5分巡回時の衝突、透明面、背景誤認、8秒以上の空白区間。
- 既存発見記録を保持したまま別ステージへ移動できること。

**受け入れ条件**

- 再現確認済みと推測を分け、問題は重要度順に最大12件。
- 修正候補ごとにURL、画面幅、座標、操作、期待結果、実結果を記載。
- コードを変更せず、全既存テストと `git diff --check` の結果を記録する。

## Task H：ユーザーテスト用紙の作成

他タスクと並行可能。実際の評価を代行したことにはしない。

**対象ファイル**

- 新規 `PLAYTEST-GUIDE.md`

8分間の説明なしプレイを3ステージそれぞれ実施できるよう、観察項目、質問、時刻記録欄、PC/スマホ別の記録欄を1ページ相当にまとめる。誘導質問、世界観の正解説明、開発者向け専門用語は入れない。

---

# Claude作業結果（2026-10-02）

A〜Hは全て完了した（A `1371147`、B `efb561a`、C `5cf5c28`、D `b20b207`、E `8271ad8`、F `e3312ac`、G `8a874a2`、H `d63b3df`）。Codex停止中に、`THREE-WORLD-QA.md` の候補1・2・3・5・7・8・11・12と、地区モジュールの質感を修正した。各指摘の対応状況は `THREE-WORLD-QA.md` の追補に、引き継ぎ事項と未対応の項目は `PLAYTEST-REVIEW.md` の「2026-10-02 Claude作業記録と引き継ぎ」に記録した。いずれもpush前。

---

# Claude Code 次タスク（2026-10-04）

## 現在地

- 最新HEADは `7554fad`。開始前に `git status --short` と `git log -3 --oneline` で確認する。
- 遊戯室の追加素材は `71097c9`、7区画へのゲーム統合は `7554fad` でコミット済み。
- Codex内部サブエージェントが作った素材を、Claude Codeが独立レビューして改善する工程とする。
- Codexは `outputs/playroom.js`、`outputs/playroom.html`、`work/test-playroom.mjs` を担当するため編集しない。

## Task I：遊戯室GLBの質感・輪郭レビューと改善

**対象ファイル**

- `source/scripts/build_playroom_zone_assets.py`
- `source/blender/playroom-zone-assets.blend`
- `outputs/assets/playroom/playroom-*-pack.glb`
- `source/previews/playroom-zone-assets-preview.png`
- `work/test-playroom-zone-assets.mjs`
- 必要なら `outputs/assets/playroom/textures/` 内の新規アトラス2枚まで
- 完了記録として本ファイル末尾と `PLAYTEST-REVIEW.md` へ短く追記

**実施内容**

1. 4素材群を10〜30mのゲーム視点で確認し、単純な直方体や円筒の組み合わせに見える箇所を重要度順に特定する。
2. 特に子どもの街の3店舗、昼寝室の寝具、誕生日席、雲の回廊について、面取り、輪郭差、布・樹脂・塗装面の差を強める。
3. 既存のカーペット、擦れた樹脂、青空壁紙を再利用できる場合は再利用する。新規画像は最大1024px、合計2枚までとし、生成スクリプトから再生成可能にする。
4. 同一平面を重ねない。透明板の多用、細かな実ジオメトリ、描画負荷を増やすだけの小物追加は避ける。
5. 2×2プレビューを更新し、4素材群を同程度の画面占有率で比較できる状態にする。

**受け入れ条件**

- 各GLB 3MB未満、150k triangles未満。現在値からdraw batchを増やす場合は理由を記録する。
- 実GLB parseでbounds、縮退面0、完全重複三角形0。
- 3店舗を色だけでなく屋根線・開口・庇の輪郭で区別できる。
- 寝具が板、雲の回廊が単なる四角い壁に見えない。
- `node work/test-playroom-zone-assets.mjs` と全 `work/test-*.mjs` が通る。
- 対象ファイルだけを1コミットにまとめ、SHA、容量、triangles、materials、変更前後の判断を報告する。

## 連携方法

- Claude Codeへの自動通知はない。ユーザーがClaude Code側で「`CLAUDE-NEXT-TASKS.md` のTask Iを実行」と依頼した時点で着手する。
- 作業中は上記対象外のファイルを編集しない。Codex側の未コミット変更があれば上書きしない。
- 完了後、Codexはコミットと記録を読み、ゲーム内配置、コリジョン、描画回数、実ブラウザ表示を検査する。

## Claude作業結果：Task I（2026-10-04）

遊戯室の4素材群を作り直した。SHAはコミット後に `git log -1 -- source/scripts/build_playroom_zone_assets.py` で確認できる。詳細と配置・コリジョンへの影響は `PLAYTEST-REVIEW.md` の「2026-10-04 遊戯室GLBの質感・輪郭（Claude）」に記録した。

| GLB | 変更前 | 変更後 |
|---|---|---|
| playground | 2,384 tri / 5 mat / 142KB | 2,384 tri / 5 mat / 103KB（形は変更なし） |
| child-town | 4,580 tri / 9 mat / 311KB | 6,460 tri / 9 mat / 243KB |
| quiet-rooms | 6,036 tri / 9 mat / 413KB | 14,572 tri / 10 mat / 482KB |
| cloud-corridor | 1,040 tri / 5 mat / 70KB | 5,136 tri / 5 mat / 161KB |

---

## Task J：遊戯室の建築モジュール制作（完了、結果は末尾）

Codexは同時に `outputs/playroom.js`、`outputs/playroom.html`、`work/test-playroom.mjs` を編集する。これらには触れず、新規素材だけを制作する。

**対象ファイル**

- 新規 `source/scripts/build_playroom_architecture.py`
- 新規 `source/blender/playroom-architecture.blend`
- 新規 `outputs/assets/playroom/playroom-architecture.glb`
- 新規 `source/previews/playroom-architecture-preview.png`
- 新規 `work/test-playroom-architecture.mjs`
- 完了記録として本ファイル末尾と `PLAYTEST-REVIEW.md` へ追記

**制作物**

1. 厚みのある丸角アーチ通路。開口幅8m、高さ6m程度。
2. 雲の輪郭を持つ壁龕。平面板ではなく、奥行きと内側の陰影が読めるもの。
3. 波形の天井下がりと間接照明溝。直線の箱だけに見えない輪郭にする。
4. 柔らかい保護材で覆われた非対称な柱。完全な円柱・直方体を避ける。

**受け入れ条件**

- 4モジュールを1つのGLBへ収録し、ノード名で個別取得できる。
- 合計30k triangles以下、材質6以下、GLB 2MB以下。
- 布／軟質材、塗装面、樹脂、金属を見分けられる材質名とroughnessを持つ。
- 同一平面の重なり、縮退面、完全重複三角形が0。
- 10〜25mのゲーム視点で、単純な箱の組み合わせに見えない。
- Blenderヘッドレス再生成と `node work/test-playroom-architecture.mjs` が成功する。
- 対象ファイルだけを1コミットにまとめ、SHAと実測値を記録する。

**連携状態**

- この依頼はファイルへ記載しただけで、Claude Codeへの自動通知・実行はない。
- Claude Code側で「`CLAUDE-NEXT-TASKS.md` のTask Jを実行」と伝えられた時点で着手する。

## Claude作業結果：Task J（2026-10-04）

`outputs/assets/playroom/playroom-architecture.glb` に4モジュールを収録した（合計9,988 triangles、6材質、289KB）。SHAは `git log -1 -- source/scripts/build_playroom_architecture.py` で確認できる。

| ノード名 | triangles | 寸法（three.js 幅×高さ×奥行き） | 材質 |
|---|---:|---|---|
| `ArchPassage` | 2,676 | 11.20×7.40×2.02 | 塗装、樹脂、布 |
| `CloudNiche` | 1,912 | 7.20×5.00×1.15 | 塗装、壁奥の影色、樹脂、布 |
| `WaveSoffit` | 2,672 | 12.00×1.60×2.85 | 塗装、金属、発光 |
| `PaddedColumn` | 2,728 | 1.99×6.00×1.47 | 布、樹脂、金属 |

---

## Task K：遊戯室の床・虹接続モジュール（完了、結果は末尾）

Codexは `outputs/playroom.js`、`outputs/playroom.html`、`work/test-playroom.mjs` を編集する。これらへ触れず、新規素材だけを制作する。

**対象ファイル**

- 新規 `source/scripts/build_playroom_floor_modules.py`
- 新規 `source/blender/playroom-floor-modules.blend`
- 新規 `outputs/assets/playroom/playroom-floor-modules.glb`
- 新規 `source/previews/playroom-floor-modules-preview.png`
- 新規 `work/test-playroom-floor-modules.mjs`
- 完了記録として本ファイル末尾と `PLAYTEST-REVIEW.md` へ追記

**制作物**

1. `RainbowWallJoin`：既存虹の外縁へ沿う左右の軟質壁接続。虹を置物ではなく壁から生えた構造に見せる。中央開口は塞がない。
2. `CloudCarpet`：厚さ8〜16cm、左右非対称な雲形カーペット。完全な平面にせず縁を丸める。
3. `SoftMeadowBerm`：高さ25〜65cmの低い草原色の起伏。飛行・歩行の視界を塞がず、中央の空床を分割する。
4. `PaddedFenceIsland`：曲線状の低い保護柵と座面。直線の柵を増やさない。

**受け入れ条件**

- 4モジュールを名前付きルートノードとして1 GLBへ収録。
- 合計24k triangles以下、材質6以下、GLB 2MB以下。
- 壁画3種と同じ退色した青、草色、クリーム、褪せた珊瑚色を使う。
- 同一平面重なり、縮退面、完全重複三角形0。
- 床へ置く面は最下部を1cm沈められる形とし、ちらつきを避ける。
- Blenderヘッドレス再生成、専用Nodeテスト、既存全テストを通す。
- 対象ファイルだけを1コミットにまとめ、SHAと実測値を記録する。

**連携状態**

- この記載だけではClaude Codeへ自動通知・実行されない。
- Claude Code側で「`CLAUDE-NEXT-TASKS.md` のTask Kを実行」と伝えた時点で着手する。

配置条件とゲーム側の分類は `PLAYTEST-REVIEW.md` の「2026-10-04 遊戯室の建築モジュール（Claude）」に記録した。

## Claude作業結果：Task K（2026-10-05）

`outputs/assets/playroom/playroom-floor-modules.glb` に4モジュールを収録した（合計10,940 triangles、5材質、265KB）。SHAは `git log -1 -- source/scripts/build_playroom_floor_modules.py` で確認できる。

| ノード名 | triangles | 寸法（three.js 幅×高さ×奥行き） | 材質 |
|---|---:|---|---|
| `RainbowWallJoin` | 2,128 | 22.00×5.28×2.58（虹の単位） | 褪せた青、クリーム |
| `CloudCarpet` | 1,022 | 7.43×0.16×5.09 | クリーム |
| `SoftMeadowBerm` | 1,466 | 12.07×0.54×4.46 | 草色 |
| `PaddedFenceIsland` | 6,324 | 6.91×1.02×6.93 | 褪せた青、褪せた珊瑚色、クリーム樹脂 |

配置条件は `PLAYTEST-REVIEW.md` の「2026-10-05 遊戯室の床・虹接続モジュール（Claude）」に記録した。

---

## Task L：虹を壁へ統合する入口シェル（完了、結果は末尾）

Codexはゲーム本体を編集する。競合を避けるため、Claude Codeは次の新規ファイルだけを制作する。

- `source/scripts/build_playroom_entry_shell.py`
- `source/blender/playroom-entry-shell.blend`
- `outputs/assets/playroom/playroom-entry-shell.glb`
- `source/previews/playroom-entry-shell-preview.png`
- `work/test-playroom-entry-shell.mjs`
- 完了記録として本ファイル末尾と `PLAYTEST-REVIEW.md` へ追記

**制作物**

1. `RainbowPortalWall`：幅34〜40m、高さ12〜14m、奥行き1.2〜1.8m。既存虹を置物ではなく壁の開口として見せる、厚みのある非対称な入口シェル。
2. `CloudReliefA`、`CloudReliefB`、`CloudReliefC`：輪郭の異なる壁付け雲。厚み0.25〜0.55m、閉じた裏面を持ち、平面板にしない。

**寸法・品質条件**

- 虹素材の内半径4.8、外半径7.48を基準とし、中央開口を狭めない。
- ゲーム倍率1.48と1.38の両方で、幅6mの通過帯と高さ3.6mのプレイヤー／飛行経路を確保する。
- 虹と同一平面を作らず、内側見込み面をクリーム色、壁面を退色した空色にする。
- 単純な長方形の正面板を避け、上端と側端に緩い非対称曲線を持たせる。
- 合計28k triangles以下、材質6以下、GLB 2MB以下。
- 表裏とも表示でき、縮退面・完全重複三角形・正の面積を持つ同一平面重なりが0。
- 専用テストでノード名、寸法、開口、法線、重複面を検査する。
- 対象ファイルだけを1コミットにまとめ、SHAと実測値を記録する。

**編集禁止**

- `outputs/playroom.js`
- `outputs/playroom.html`
- `work/test-playroom.mjs`
- Task K以前の既存素材と生成スクリプト

**連携状態**

- この記載だけではClaude Codeへ自動通知・実行されない。
- Claude Code側で「`CLAUDE-NEXT-TASKS.md` のTask Lを実行」と伝えた時点で着手する。

---

## Task M：滑り台・ボールプールの軟質遊具化（完了、結果は末尾）

Codexは画像素材、ゲーム本体、配置を担当する。Claude Codeは既存素材を編集せず、次の新規ファイルだけを制作する。

- `source/scripts/build_playroom_soft_play_upgrade.py`
- `source/blender/playroom-soft-play-upgrade.blend`
- `outputs/assets/playroom/playroom-soft-play-upgrade.glb`
- `source/previews/playroom-soft-play-upgrade-preview.png`
- `work/test-playroom-soft-play-upgrade.mjs`

**制作物**

1. `SoftSlideTower`：現状と同じ大きさの通過可能な塔だが、柱・屋根・滑走面を丸め、接合部へ厚い保護パッドを持たせる。滑走面は連続した曲率と厚みを持つ。
2. `RoundedBallPit`：内寸14×9m程度。角を丸めた厚い軟質壁、沈み込みのある上縁、疎密差のある滑らかな球を持つ。球は少数メッシュの見た目でもよいが、四角い槽に見せない。

**受け入れ条件**

- 2ノード合計35k triangles以下、材質6以下、GLB 2MB以下。
- 現在のコリジョン寸法内へ収まり、滑り台の幅2m以上の進入路と、ボールプール周囲1.2m以上の通路を確保する。
- 褪せた珊瑚色、クリーム、鈍い青、草色を使用し、原色を避ける。
- 表裏の法線、縮退面、完全重複面、正の面積を持つ同一平面重なりを検査する。
- 既存 `playroom-slide.glb`、`playroom-ball-pit.glb`、ゲームJS／HTMLへ触れない。
- 対象ファイルだけを1コミットにまとめ、SHA・三角形数・材質数・寸法を記録する。

**連携状態**

- Task Lと同様、この記載だけではClaude Codeへ自動通知・実行されない。
- Claude Code側で「Task Lを完了後、Task Mを実行」と明示して着手する。

## Claude作業結果：Task L（2026-10-07）

`outputs/assets/playroom/playroom-entry-shell.glb` に4ノードを収録した（合計5,586 triangles、3材質、128KB）。SHAは `git log -1 -- source/scripts/build_playroom_entry_shell.py` で確認できる。

| ノード名 | triangles | 寸法（three.js 幅×高さ×奥行き） |
|---|---:|---|
| `RainbowPortalWall` | 2,136 | 37.96×13.38×1.50（虹の単位） |
| `CloudReliefA` | 1,150 | 6.82×3.03×0.45（m） |
| `CloudReliefB` | 1,150 | 5.22×2.32×0.30（m） |
| `CloudReliefC` | 1,150 | 9.56×3.27×0.54（m） |

配置条件は `PLAYTEST-REVIEW.md` の「2026-10-07 遊戯室の入口シェル（Claude）」に記録した。

## Claude作業結果：Task M（2026-10-07）

`outputs/assets/playroom/playroom-soft-play-upgrade.glb` に2ノードを収録した（合計19,380 triangles、6材質、613KB）。SHAは `git log -1 -- source/scripts/build_playroom_soft_play_upgrade.py` で確認できる。

| ノード名 | triangles | 寸法（three.js 幅×高さ×奥行き） | 置き換え対象 |
|---|---:|---|---|
| `SoftSlideTower` | 6,760 | 8.16×6.13×3.62 | `playroom-slide.glb`（同じ原点・単位・向き） |
| `RoundedBallPit` | 12,620 | 7.56×0.97×5.50 | `playroom-ball-pit.glb`（同じ原点・単位・向き） |

配置条件は `PLAYTEST-REVIEW.md` の「2026-10-07 遊戯室の軟質遊具（Claude）」に記録した。

---

## Task N：奥区画の天井・壁際シルエット（完了、結果は末尾）

Codexはゲーム本体、照明、既存素材の再配置を担当する。Claude Codeは競合を避け、次の新規ファイルだけを制作する。

- `source/scripts/build_playroom_deep_room_kit.py`
- `source/blender/playroom-deep-room-kit.blend`
- `outputs/assets/playroom/playroom-deep-room-kit.glb`
- `source/previews/playroom-deep-room-kit-preview.png`
- `work/test-playroom-deep-room-kit.mjs`

**制作物**

1. `CloudCeilingCove`：雲形の天井縁と間接照明溝。直線の梁に見えず、天井へ5cm埋めて配置できる。
2. `SoftWallAlcove`：奥行き1.2〜1.8mの非対称な壁龕。人が通れる開口ではなく、寝具・椅子・小物の背景になる。
3. `HangingCloudCluster`：高さ違いの立体雲3〜5個を一群にした吊り装飾。薄い板を禁止し、全方向から厚みが見える。

**受け入れ条件**

- 合計24k triangles以下、材質5以下、GLB 1.5MB以下。
- 退色した空色、クリーム、鈍い青、褪せた珊瑚色のみを使う。
- 同一平面重なり、縮退面、完全重複面0。床から高さ3.6mまでの通行域へ出さない。
- 既存GLB、`outputs/playroom.js`、HTML、既存テストへ触れない。
- 対象ファイルだけを1コミットにし、SHA、寸法、三角形数、材質数を記録する。

**連携状態**

- この記載だけではClaude Codeへ自動通知・実行されない。
- Claude Code側で「`CLAUDE-NEXT-TASKS.md` のTask Nを実行」と伝えた時点で着手する。

## Claude作業結果：Task N（2026-10-08）

`outputs/assets/playroom/playroom-deep-room-kit.glb` に3ノードを収録した（合計14,802 triangles、5材質、390KB）。SHAは `git log -1 -- source/scripts/build_playroom_deep_room_kit.py` で確認できる。

| ノード名 | triangles | 寸法（three.js 幅×高さ×奥行き、m） |
|---|---:|---|
| `CloudCeilingCove` | 4,822 | 16.00×1.26×2.01 |
| `SoftWallAlcove` | 1,916 | 7.50×5.22×1.74 |
| `HangingCloudCluster` | 8,064 | 6.59×5.97×3.55 |

配置条件は `PLAYTEST-REVIEW.md` の「2026-10-08 遊戯室の奥区画キット（Claude）」に記録した。

---

## Task O：雲の回廊を立体空間へ作り直す（未着手）

現在の固定視点 `playroom.html?debug=1&view=cloud` は、白い平面床、直線フレーム、壁紙が画面を占め、参照画像の「雲に包まれた遊戯空間」になっていない。既存 `playroom-cloud-corridor-pack.glb` の修正ではなく、置換用の新規キットを制作する。

**Claude Codeの担当ファイル**

- `source/scripts/build_playroom_cloud_corridor_v2.py`
- `source/blender/playroom-cloud-corridor-v2.blend`
- `outputs/assets/playroom/playroom-cloud-corridor-v2.glb`
- `source/previews/playroom-cloud-corridor-v2-preview.png`
- `work/test-playroom-cloud-corridor-v2.mjs`

**制作物**

1. `CloudCorridorShell`：幅24m以上、高さ13m以上、奥行き22m以上。左右と天井が連続した丸い室内殻で、正面板や直線の箱に見えない。中央に幅8m×高さ6m以上の飛行経路を残す。
2. `CloudFloorBanks`：床の左右へ厚い雲堤を非対称に配置し、中央通路を幅7m以上残す。床全面を白く覆わない。
3. `DistantCloudGate`：終端の遠景となる二重以上の雲形開口。薄い看板は禁止し、裏側と見込み面を持つ。
4. `FloatingCloudIslands`：高さと奥行きが異なる3群以上。飛行経路の外へ置き、全方向から厚みが見える。

**受け入れ条件**

- `PLAYROOM-REFERENCE-SPEC.md` の雲回廊視点で、前景・中景・遠景の3層が素材単体プレビューでも判別できる。
- 単純な長方形の大面積面、薄い平面、同じ形の等間隔反復を避ける。
- 退色した空色、クリーム、薄い灰青、少量の褪せた珊瑚色。原色と純白の大面積使用は禁止。
- 合計32k triangles以下、材質6以下、GLB 2MB以下。
- 床から高さ3.6m、中央幅7mの通行域を侵さない。
- 動かす群を識別できるノード名を付ける。ゲーム側で各群へ位相の異なる低速ドリフトを適用するため、原点を各群の中心に置く。移動余白は水平1.5m、上下0.5mを見込む。
- 表裏の法線、縮退面、完全重複面、正の面積を持つ同一平面重なりが0。
- 専用テストでノード名、寸法、開口、予算、法線、重複面を検査する。
- 対象ファイルだけを1コミットにまとめ、SHAと実測値を末尾へ記録する。

**編集禁止**

- `outputs/playroom.js`
- `outputs/playroom.html`
- `work/test-playroom.mjs`
- 既存GLBと既存生成スクリプト

**連携状態**

- この記載だけではClaude Codeへ自動通知・実行されない。
- Claude Code側で「`CLAUDE-NEXT-TASKS.md` のTask Oを実行」と伝えた時点で着手する。

---

## Task P：昼寝室と誕生日会場を分離する（Task Oと並行可）

現在の `playroom-quiet-rooms-pack.glb` は昼寝用と誕生日用の家具を一体で収録し、ゲーム側で同じ全セットを2室へ重複配置している。既存素材を壊さず、意味ごとに分離した置換素材を作る。

**Claude Codeの担当ファイル**

- `source/scripts/build_playroom_quiet_split.py`
- `source/blender/playroom-quiet-split.blend`
- `outputs/assets/playroom/playroom-quiet-split.glb`
- `source/previews/playroom-quiet-split-preview.png`
- `work/test-playroom-quiet-split.mjs`

**制作物**

1. `NapRoomSet`：寝具、マット、低い間仕切り。最後の寝床だけを少し離し、発見対象として読める構図にする。
2. `BirthdayRoomSet`：机、ケーキ、椅子、アーチ。椅子はケーキへ向け、人物サイズに対して自然な寸法を保つ。

**受け入れ条件**

- 既存素材を流用してよいが、2ノードを個別配置できること。
- 2ノード合計14,600 triangles以下、材質6以下、GLB 1.5MB以下。
- 各ノードの原点を床中央へ置き、幅22m×奥行き8m以内。
- 単純な等間隔配置を避け、中央に幅3m以上の移動経路を残す。
- 同一平面重なり、縮退面、完全重複面0。専用テストで検査する。
- 対象ファイルだけを1コミットにまとめ、SHA、各ノード寸法、三角形数、材質数を末尾へ記録する。

**編集禁止**

- `outputs/playroom.js`、HTML、既存テスト、既存GLB、既存生成スクリプト

**連携状態**

- Task Oと別コミットで独立して実行できる。
- この記載だけではClaude Codeへ自動通知・実行されない。

---

## Task Q：子どもの街の前景キット（Task O・Pと並行可）

現在の店舗3棟は形状を読めるが、広い通路に一列だけ置かれ、正面展示に見える。店舗本体を作り直さず、前景・中景を作る少数素材を追加する。

**Claude Codeの担当ファイル**

- `source/scripts/build_playroom_town_foreground.py`
- `source/blender/playroom-town-foreground.blend`
- `outputs/assets/playroom/playroom-town-foreground.glb`
- `source/previews/playroom-town-foreground-preview.png`
- `work/test-playroom-town-foreground.mjs`

**制作物**

1. `TownBenchCluster`：丸みのあるベンチ1、低い植栽または布製遊具2〜3。薄い板は禁止。
2. `TownSignCluster`：非対称な案内標識と低い街灯。文字は使わず、退色した図形で構成する。
3. `TownVehicleSilhouette`：子ども用の小さな乗り物1台。人物より小さすぎず、全方向から厚みが見える。

**受け入れ条件**

- 合計8,000 triangles以下、材質5以下、GLB 1MB以下。
- 店舗入口を塞がず、各群の周囲へ幅1.5m以上の経路を残せる寸法。
- 退色した珊瑚色、草色、クリーム、鈍い青。原色と直方体だけの構成は禁止。
- 同一平面重なり、縮退面、完全重複面0。専用テストで検査する。
- 対象ファイルだけを1コミットにまとめ、SHA、各ノード寸法、三角形数、材質数を末尾へ記録する。

**編集禁止**

- `outputs/playroom.js`、HTML、既存テスト、既存GLB、既存生成スクリプト

**連携状態**

- Task O・Pと別コミットで独立して実行できる。
- この記載だけではClaude Codeへ自動通知・実行されない。
