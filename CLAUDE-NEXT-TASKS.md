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
