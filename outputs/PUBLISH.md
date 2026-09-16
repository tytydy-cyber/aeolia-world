# 公開手順

## 推奨構成

GitHubリポジトリにゲームを保存し、Cloudflare PagesをGitHubへ接続します。`main`へ更新を送るたびに自動公開され、作業用ブランチには確認用URLが発行されます。

## Cloudflare Pages

Cloudflareの Workers & Pages から「Connect to Git」を選び、GitHubリポジトリを接続します。

- Production branch: `main`
- Framework preset: `None`
- Build command: 空欄
- Build output directory: `outputs`

公開後は `プロジェクト名.pages.dev` で遊べます。独自ドメインは後から追加できます。

## GitHub Pagesだけで公開する場合

この `outputs` フォルダの中身を公開用リポジトリのルートへ置き、Repository settings の Pages で `main` ブランチのルートを選びます。`.nojekyll` はそのまま残します。

## 公開前の確認

- `index.html` と `audio.js`、`effects.js` を削除しない
- `assets/` の階層を変えない
- HTTPSの公開URLで開始、移動、音、建物の読込を確認する
- 更新後はURL末尾の `?v=` を増やすと、友人のブラウザに残った古いキャッシュを避けやすい
