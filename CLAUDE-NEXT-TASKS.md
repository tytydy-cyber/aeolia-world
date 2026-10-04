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

## Task J：遊戯室の建築モジュール制作（未着手）

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
