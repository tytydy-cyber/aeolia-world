# AEOLIA — 雲海紀行

浮島の街を歩き、空を飛んで巡るブラウザ向け散策ゲームです。

## ローカル起動

```sh
python3 -m http.server 8765 --bind 127.0.0.1 --directory outputs
```

`http://localhost:8765/` を開いてください。公開設定は `outputs/PUBLISH.md` にあります。

## 操作

- 十字キー／WASD：移動
- ドラッグ：視点操作
- F：歩行／飛行
- Space／Shift：上昇／下降
- C：進行方向へ視点を戻す
