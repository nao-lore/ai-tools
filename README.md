# AI Tools — X抽出 + YouTube要約 + Chrome拡張

CLIツール2つ + Chrome拡張。AIとの情報収集ワークフローを自動化するためのツールセット。

---

## ツール一覧

| ツール | 概要 |
|--------|------|
| `xt` | X(Twitter)の投稿をURL指定で取得。テキスト・画像・記事全文に対応 |
| `yt-summary` | YouTube動画の字幕を取得してClaudeで要約 |
| Chrome拡張 | X上でツイートをタップ選択してURLをまとめてコピー |

---

## xt — X投稿取得ツール

Xの投稿をURL指定で取得するCLIツール。fxtwitter APIを使って、テキスト・画像DL・引用ツイート・X記事の全文抽出まで対応。

### インストール

```bash
# PATHの通った場所にシンボリックリンクを作成
ln -s /Users/nn/tools/xt/xt /usr/local/bin/xt
ln -s /Users/nn/tools/xt/xt-bulk /usr/local/bin/xt-bulk
```

外部依存なし（Python標準ライブラリのみ）。

### 使い方

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

### xt-bulk

クリップボードのURLリストを一括で `xt` に流すラッパー。Chrome拡張やブックマークレットでコピーした後にそのまま実行できる。

```bash
# Chrome拡張でURLをコピーした後に
xt-bulk
```

---

## yt-summary — YouTube動画要約ツール

YouTube動画の字幕を取得して、Claude APIで要約するCLIツール。日本語・英語の字幕に対応。

### インストール

```bash
# 依存パッケージのインストール
cd /Users/nn/tools/yt-summarizer
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# PATHの通った場所にシンボリックリンクを作成
ln -s /Users/nn/tools/yt-summarizer/yt-summary /usr/local/bin/yt-summary
```

環境変数 `ANTHROPIC_API_KEY` の設定が必要。

### 使い方

```bash
# 通常の要約
yt-summary https://www.youtube.com/watch?v=xxxxx

# 詳細な要約
yt-summary URL --detail detailed

# 簡潔な要約（3-5文）
yt-summary URL --detail brief

# 英語で出力
yt-summary URL --lang en

# 字幕テキストのみ出力（要約なし）
yt-summary URL --raw
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

- **xt**: Python 3.10+（標準ライブラリのみ）
- **yt-summary**: Python 3.10+, `youtube-transcript-api`, `anthropic`
- **Chrome拡張**: Chrome / Chromium系ブラウザ
