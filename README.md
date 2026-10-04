# AEOLIA — 雲海紀行

3つの世界を飛んで巡るブラウザ向け散策ゲームです。戦闘や会話はなく、発見地点を訪ねて旅の記録を集めます。

## 世界

- 浮島の街（`aeolia.html`）：雲海に浮かぶ中央島と三つの外島、雲の下の点検路
- 閉鎖施設（`liminal.html?stage=parallax`）：使われなくなった施設が街区規模でつながる空間
- 郊外（`liminal.html?stage=somnia`）：水路、空中庭園、発電設備が育ったソーラーパンクの郊外
- 遊戯室（`playroom.html`）：虹、遊具、ボールプールが反復する巨大な屋内遊戯施設

世界選択（`index.html`）から各世界へ移動します。発見した場所は、端末内の発見記録に全世界分まとめて保存されます。

## ローカル起動

```sh
python3 -m http.server 8765 --bind 127.0.0.1 --directory outputs
```

`http://localhost:8765/` を開いてください。

## 操作

- 十字キー／WASD：移動（常に飛行）
- ドラッグ：視点操作。Q・Eでも旋回
- Space／Shift：上昇／下降。下降しながら前進すると加速
- Ctrl：加速
- C：進行方向へ視点を戻す

スマートフォンでは画面左の十字パッドで移動し、右側のボタンで上昇・下降します。3D画面のスワイプで視点を動かせます。

## フォルダ

- `outputs/`：公開されるゲーム本体。mainへのpushでGitHub Pagesへ自動公開（`docs/PUBLISH.md`）
- `work/`：自動テスト（`node work/test-*.mjs`、`node work/audit-game.mjs`）と素材の生成スクリプト
- `source/`：Blenderの原本、確認用の画像、未使用の素材（公開しない）
- `docs/`：公開手順と過去の記録
- 計画と作業記録：`WORLD-DIRECTION.md`、各ステージの計画書、`PLAYTEST-REVIEW.md`、QAレポート
