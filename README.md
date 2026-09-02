# 全国 地域政治ニュースまとめサイト

RSSフィードから地域・地方政治のニュースを自動収集し、静的なWebページとして
GitHub Pages上に無料で公開するためのプロジェクトです。

## 仕組み
- `build_site.py` が複数のニュースソース（NHK政治、Yahoo!ニュース国内、
  Googleニュース検索など）からRSSを取得し、`index.html` を自動生成します。
- `.github/workflows/update.yml` が GitHub Actions 上で
  **3時間おきに自動実行**され、最新ニュースに更新した `index.html` を
  リポジトリへ自動コミット・プッシュします。
- GitHub Pages がそのリポジトリを公開するので、あなたは一切操作しなくても
  ページが自動で最新化されます。

## セットアップ手順（初回のみ）

1. GitHubアカウントを持っていない場合は https://github.com で無料登録
2. 新しいリポジトリを作成（例: `local-politics-news`、Public設定）
3. このフォルダの中身（`build_site.py`, `requirements.txt`, `README.md`,
   `.github/workflows/update.yml`）をそのリポジトリにアップロード
   - GitHubのWeb画面から「Add file」→「Upload files」でドラッグ&ドロップでもOK
   - または `git` コマンドが使えるなら:
     ```
     git init
     git add .
     git commit -m "initial commit"
     git branch -M main
     git remote add origin https://github.com/【あなたのユーザー名】/local-politics-news.git
     git push -u origin main
     ```
4. リポジトリの **Settings → Actions → General → Workflow permissions** で
   「Read and write permissions」を選択して保存
   （Actionsが自動コミットするために必要です）
5. リポジトリの **Settings → Pages** で
   - Source: 「Deploy from a branch」
   - Branch: `main` / `/(root)` を選択して Save
6. **Actions** タブを開き、「政治ニュース自動更新」ワークフローを
   一度手動実行（Run workflow）して `index.html` を生成させる
7. 数分後、`https://【あなたのユーザー名】.github.io/local-politics-news/`
   でサイトが公開されます

以降は何もしなくても3時間おきに自動更新されます。

## 更新頻度を変えたい場合
`.github/workflows/update.yml` の以下の行を編集してください。

```
cron: "0 */3 * * *"   # 3時間ごと
```

例: 1時間ごとにしたい場合は `"0 * * * *"` に変更します。

## ニュースソースを追加・変更したい場合
`build_site.py` 内の `FEEDS` リストにRSSのURLを追加すれば、
そのソースも自動的に収集対象になります。

## 注意事項
- 表示しているのは各ニュースの見出し・要約のみです。全文はリンク先の
  元記事でご確認ください。
- このプロジェクトはRSS配信の仕様変更などにより、
  ソース側の都合で取得できなくなる場合があります。
