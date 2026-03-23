# AI Tools — X抽出 + YouTube要約 + Chrome拡張

CLIツール + Chrome拡張。AIとの情報収集ワークフローを自動化するためのツールセット。

---

## ツール一覧

| ツール | 概要 |
|--------|------|
| `xt` | X(Twitter)投稿の取得 + YouTube動画の要約。URL自動判定で両方対応 |
| Chrome拡張 | X上でツイートをタップ選択してURLをまとめてコピー |

---

## xt — X投稿取得 + YouTube要約ツール

Xの投稿をURL指定で取得（テキスト・画像DL・引用ツイート・X記事の全文抽出）+ YouTube動画の字幕を取得してClaude APIで要約。URLの種類を自動判定して適切に処理する。X・YouTubeのURL混在もOK。

### インストール

```bash
# PATHの通った場所にシンボリックリンクを作成
ln -s /Users/nn/tools/xt/xt /usr/local/bin/xt
ln -s /Users/nn/tools/xt/xt-bulk /usr/local/bin/xt-bulk

# YouTube機能を使う場合は追加パッケージが必要
pip install youtube-transcript-api anthropic
```

環境変数 `ANTHROPIC_API_KEY` の設定が必要（YouTube要約機能を使う場合）。

### 使い方 — X投稿

```bash
# 1件取得
xt https://x.com/username/status/1234567890

# 複数同時
xt URL1 URL2 URL3

# クリップボードから
pbpaste | xt

# 画像DLしない
xt URL --no-images

# 生JSON出力
xt URL --json

# URLを対話的に貼り付け
xt
```

### 使い方 — YouTube要約

```bash
# 通常の要約
xt https://www.youtube.com/watch?v=xxxxx

# 詳細な要約
xt YOUTUBE_URL --detail detailed

# 簡潔な要約（3-5文）
xt YOUTUBE_URL --detail brief

# 英語で出力
xt YOUTUBE_URL --lang en

# 字幕テキストのみ出力（要約なし）
xt YOUTUBE_URL --raw
```

### 使い方 — X + YouTube混在

```bash
# XとYouTubeのURLを混ぜて処理
xt https://x.com/user/status/123 https://www.youtube.com/watch?v=xxxxx

# クリップボードからも混在OK
pbpaste | xt
```

### xt-bulk

クリップボードのURLリストを一括で `xt` に流すラッパー。Chrome拡張やブックマークレットでコピーした後にそのまま実行できる。

```bash
# Chrome拡張でURLをコピーした後に
xt-bulk
```

---

## Chrome拡張 — X抽出

X(Twitter)上でツイートをタップして選択し、URLをまとめてクリップボードにコピーするChrome拡張。`xt-bulk` と組み合わせて使う。

### インストール

1. Chromeで `chrome://extensions` を開く
2. 「デベロッパーモード」をON
3. 「パッケージ化されていない拡張機能を読み込む」から `xt/chrome-ext/` を選択

### 使い方

1. X(Twitter)のタイムラインやブックマークページを開く
2. ツイートをクリックして選択（青くハイライトされる）
3. フローティングバーの「コピー」でURLをクリップボードにコピー
4. ターミナルで `xt-bulk` を実行

「全選択」で画面上の全ツイートを一括選択もできる。

### ブックマークレット版

Chrome拡張の代わりに、ブックマークレットとしても使える（`xt/bookmarklet.js` 参照）。

---

## 依存関係

- **xt (X機能)**: Python 3.10+（標準ライブラリのみ）
- **xt (YouTube機能)**: Python 3.10+, `youtube-transcript-api`, `anthropic`
- **Chrome拡張**: Chrome / Chromium系ブラウザ
