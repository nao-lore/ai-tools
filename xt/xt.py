#!/usr/bin/env python3
"""X投稿の取得 + YouTube動画の要約を行う統合CLIツール"""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error

IMG_BASE = "/tmp/xt"


# ==============================================================
# URL判定
# ==============================================================

def is_youtube_url(url: str) -> bool:
    """URLがYouTubeかどうか判定"""
    return "youtube.com" in url or "youtu.be" in url


def is_x_url(url: str) -> bool:
    """URLがX/Twitterかどうか判定"""
    return "x.com/" in url or "twitter.com/" in url


# ==============================================================
# YouTube処理
# ==============================================================

def extract_video_id(url_or_id: str) -> str | None:
    """URLまたはIDからvideo IDを抽出"""
    patterns = [
        r'(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$',
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    return None


def get_transcript(video_id: str) -> str:
    """字幕テキストを取得（日本語優先、なければ英語、なければ自動生成）"""
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api.formatters import TextFormatter

    ytt_api = YouTubeTranscriptApi()
    transcript = ytt_api.fetch(video_id, languages=["ja", "en"])
    formatter = TextFormatter()
    return formatter.format_transcript(transcript)


def summarize_transcript(text: str, lang: str = "ja", detail: str = "normal") -> str:
    """Claudeで要約"""
    import anthropic

    client = anthropic.Anthropic()

    if detail == "detailed":
        instruction = (
            "以下はYouTube動画の字幕テキストです。\n"
            "この動画の内容を詳細にまとめてください。\n"
            "- まず動画の概要を2-3文で\n"
            "- 主要なポイントを箇条書きで（各ポイントの説明付き）\n"
            "- 重要な具体例やデータがあれば含める\n"
            "- 結論やアクションアイテムがあればまとめる"
        )
    elif detail == "brief":
        instruction = (
            "以下はYouTube動画の字幕テキストです。\n"
            "3-5文で簡潔に要約してください。"
        )
    else:
        instruction = (
            "以下はYouTube動画の字幕テキストです。\n"
            "この動画の内容をわかりやすくまとめてください。\n"
            "- まず1文で概要\n"
            "- 主要なポイントを箇条書き\n"
            "- 重要な結論があればまとめる"
        )

    if lang == "en":
        instruction = instruction.replace("以下はYouTube動画の字幕テキストです。", "Below is a YouTube video transcript.")
        instruction = instruction.replace("この動画の内容をわかりやすくまとめてください。", "Summarize this video clearly.")
        instruction = instruction.replace("まず1文で概要", "One-sentence overview first")
        instruction = instruction.replace("主要なポイントを箇条書き", "Key points as bullet points")
        instruction = instruction.replace("重要な結論があればまとめる", "Include important conclusions")

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[
            {"role": "user", "content": f"{instruction}\n\n---\n{text}"}
        ],
    )
    return message.content[0].text


def process_youtube(url: str, raw: bool = False, detail: str = "normal", lang: str = "ja") -> None:
    """YouTube URLを処理して結果を出力"""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi  # noqa: F401
    except ImportError:
        print("エラー: YouTube処理に必要なパッケージがありません", file=sys.stderr)
        print("  pip install youtube-transcript-api anthropic", file=sys.stderr)
        return

    video_id = extract_video_id(url)
    if not video_id:
        print(f"[スキップ] 動画IDを認識できません: {url}", file=sys.stderr)
        return

    print(f"動画ID: {video_id}", file=sys.stderr)
    print("字幕を取得中...", file=sys.stderr)

    try:
        transcript = get_transcript(video_id)
    except Exception as e:
        print(f"  字幕取得エラー: {e}", file=sys.stderr)
        return

    if raw:
        print(transcript)
        return

    char_count = len(transcript)
    print(f"字幕取得完了 ({char_count:,}文字)", file=sys.stderr)
    print("要約中...", file=sys.stderr)

    try:
        summary = summarize_transcript(transcript, lang=lang, detail=detail)
    except Exception as e:
        print(f"  要約エラー: {e}", file=sys.stderr)
        return

    print()
    print(summary)


# ==============================================================
# X (Twitter) 処理 — 既存コードそのまま
# ==============================================================

def extract_tweet_info(url_or_id: str) -> tuple[str, str | None]:
    """URLまたはIDからtweet IDとユーザー名を抽出"""
    if re.match(r'^\d+$', url_or_id):
        return url_or_id, None
    match = re.search(r'(?:x\.com|twitter\.com)/([^/]+)/status/(\d+)', url_or_id)
    if match:
        return match.group(2), match.group(1)
    match = re.search(r'/status/(\d+)', url_or_id)
    if match:
        return match.group(1), None
    return None, None


def fetch_tweet(tweet_id: str, username: str | None = None) -> dict | None:
    """fxtwitter APIでツイートを取得"""
    if username:
        url = f"https://api.fxtwitter.com/{username}/status/{tweet_id}"
    else:
        url = f"https://api.fxtwitter.com/status/{tweet_id}"
    req = urllib.request.Request(url, headers={"User-Agent": "xt/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"  取得失敗 (HTTP {e.code})", file=sys.stderr)
        return None
    except Exception as e:
        print(f"  エラー: {e}", file=sys.stderr)
        return None

    if data.get("code") != 200:
        return None

    return data["tweet"]


def download_image(url: str, dest: str) -> bool:
    """画像をダウンロード"""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "xt/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            with open(dest, "wb") as f:
                f.write(resp.read())
        return True
    except Exception:
        return False


def save_media(tweet: dict, save_dir: str, prefix: str = "") -> list[str]:
    """ツイートのメディアをダウンロードしてパスのリストを返す"""
    paths = []
    media = tweet.get("media", {})
    if not isinstance(media, dict):
        return paths

    for i, photo in enumerate(media.get("photos", [])):
        img_url = photo.get("url", "")
        if img_url:
            dest = os.path.join(save_dir, f"{prefix}img_{i+1}.jpg")
            if download_image(img_url, dest):
                paths.append(dest)

    for i, video in enumerate(media.get("videos", [])):
        thumb = video.get("thumbnail_url", "")
        if thumb:
            dest = os.path.join(save_dir, f"{prefix}vid_thumb_{i+1}.jpg")
            if download_image(thumb, dest):
                paths.append(dest)

    return paths


def extract_article_text(article: dict) -> str | None:
    """X記事のcontent.blocksから全文を抽出"""
    content = article.get("content", {})
    blocks = content.get("blocks", [])
    if not blocks:
        return None

    lines = []
    for block in blocks:
        text = block.get("text", "")
        btype = block.get("type", "unstyled")
        if btype.startswith("header"):
            lines.append(f"\n## {text}\n")
        elif btype == "unordered-list-item":
            lines.append(f"  - {text}")
        elif btype == "ordered-list-item":
            lines.append(f"  1. {text}")
        elif btype == "blockquote":
            lines.append(f"  > {text}")
        elif btype == "code-block":
            lines.append(f"    {text}")
        else:
            lines.append(text)

    return "\n".join(lines)


def format_tweet(tweet: dict, save_dir: str | None = None) -> str:
    """ツイートを読みやすいテキストに整形"""
    lines = []
    author = tweet.get("author", {})
    handle = author.get("screen_name", "?")
    name = author.get("name", "?")
    created = tweet.get("created_at", "?")
    text = tweet.get("text", "")
    likes = tweet.get("likes", 0)
    retweets = tweet.get("retweets", 0)
    replies = tweet.get("replies", 0)
    views = tweet.get("views", 0)
    tweet_url = tweet.get("url", "")

    lines.append(f"@{handle} ({name}) — {created}")
    lines.append("")
    if text:
        lines.append(text)
        lines.append("")

    # Engagement
    stats = []
    if likes:
        stats.append(f"♥ {likes:,}")
    if retweets:
        stats.append(f"🔁 {retweets:,}")
    if replies:
        stats.append(f"💬 {replies:,}")
    if views:
        stats.append(f"👁 {views:,}")
    if stats:
        lines.append("  ".join(stats))

    # Article (X記事) — 全文抽出
    article = tweet.get("article")
    if article:
        title = article.get("title", "")
        full_text = extract_article_text(article)
        if title:
            lines.append("")
            lines.append(f"━━━ 記事: {title} ━━━")
            if full_text:
                lines.append(full_text)
            else:
                preview = article.get("preview_text", "")
                if preview:
                    lines.append(preview)
            lines.append("━━━━━━━━━━━━━━━━━")

        # Article cover image
        cover = article.get("cover_media", {})
        cover_info = cover.get("media_info", {})
        cover_url = cover_info.get("original_img_url", "")
        if cover_url and save_dir:
            dest = os.path.join(save_dir, "article_cover.jpg")
            if download_image(cover_url, dest):
                lines.append(f"[記事カバー画像] {dest}")

    # Quote tweet
    quote = tweet.get("quote")
    if quote:
        q_author = quote.get("author", {})
        lines.append("")
        lines.append(f"  ┌─ 引用: @{q_author.get('screen_name', '?')} ({q_author.get('name', '?')})")
        for qline in quote.get("text", "").split("\n"):
            lines.append(f"  │ {qline}")
        lines.append(f"  └─ {quote.get('url', '')}")

        if save_dir:
            q_paths = save_media(quote, save_dir, prefix="quote_")
            for p in q_paths:
                lines.append(f"  │ [引用画像] {p}")

    # Media
    media = tweet.get("media", {})
    if isinstance(media, dict):
        photos = media.get("photos", [])
        videos = media.get("videos", [])

        if save_dir:
            img_paths = save_media(tweet, save_dir)
            if img_paths:
                lines.append("")
                for p in img_paths:
                    lines.append(f"[画像] {p}")
        else:
            if photos:
                lines.append("")
                for i, photo in enumerate(photos):
                    lines.append(f"[画像{i+1}] {photo.get('url', '')}")
            if videos:
                lines.append("")
                for i, video in enumerate(videos):
                    duration = video.get("duration", 0)
                    lines.append(f"[動画{i+1}] {duration:.1f}秒 {video.get('url', '')}")

    lines.append("")
    lines.append(tweet_url)

    return "\n".join(lines)


def process_x(url: str, args) -> None:
    """X/Twitter URLを処理して結果を出力"""
    tweet_id, username = extract_tweet_info(url)
    if not tweet_id:
        print(f"[スキップ] {url}")
        return

    tweet = fetch_tweet(tweet_id, username)

    if tweet is None:
        print(f"[スキップ] {url}")
        return

    if args.json:
        print(json.dumps(tweet, indent=2, ensure_ascii=False))
        return

    save_dir = None
    if not args.no_images:
        if args.save_dir:
            save_dir = os.path.join(args.save_dir, tweet_id)
        else:
            save_dir = os.path.join(IMG_BASE, tweet_id)
        os.makedirs(save_dir, exist_ok=True)

    print(format_tweet(tweet, save_dir))


# ==============================================================
# URL読み取り（X + YouTube対応）
# ==============================================================

def read_urls_from_stdin() -> list[str]:
    """標準入力またはクリップボードからURL読み取り"""
    # If stdin is a pipe, read from it
    if not sys.stdin.isatty():
        text = sys.stdin.read()
    else:
        # Interactive: prompt user to paste
        print("URLを貼り付けてください（空行で実行）:", file=sys.stderr)
        input_lines = []
        try:
            while True:
                line = input()
                if line.strip() == "":
                    if input_lines:
                        break
                    continue
                input_lines.append(line.strip())
        except EOFError:
            pass
        text = "\n".join(input_lines)

    urls = []
    for line in text.strip().split("\n"):
        line = line.strip()
        if is_youtube_url(line) or is_x_url(line):
            urls.append(line)
    return urls


# ==============================================================
# メイン
# ==============================================================

def main():
    parser = argparse.ArgumentParser(
        description="X投稿の取得 + YouTube動画の要約",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "使用例:\n"
            "  xt URL                         # X投稿を取得\n"
            "  xt URL1 URL2 URL3              # 複数同時（X・YouTube混在OK）\n"
            "  xt                             # URLを貼り付けモード\n"
            "  pbpaste | xt                   # クリップボードから\n"
            "  xt URL --no-images             # 画像DLしない（X用）\n"
            "  xt URL --json                  # 生JSON出力（X用）\n"
            "  xt YOUTUBE_URL                 # YouTube動画を要約\n"
            "  xt YOUTUBE_URL --raw           # 字幕テキストのみ出力\n"
            "  xt YOUTUBE_URL --detail brief  # 簡潔な要約\n"
        ),
    )
    parser.add_argument("urls", nargs="*", help="X投稿またはYouTube動画のURL（省略で貼り付けモード）")
    # X用オプション
    parser.add_argument("--no-images", action="store_true", help="画像をダウンロードしない（X用）")
    parser.add_argument("--save-dir", help=f"画像の保存先（デフォルト: {IMG_BASE}/ツイートID/）")
    parser.add_argument("--json", action="store_true", help="生JSON出力（X用）")
    # YouTube用オプション
    parser.add_argument("--raw", action="store_true", help="要約せず字幕テキストのみ出力（YouTube用）")
    parser.add_argument("--detail", choices=["brief", "normal", "detailed"], default="normal",
                        help="要約の詳細度（YouTube用、default: normal）")
    parser.add_argument("--lang", choices=["ja", "en"], default="ja",
                        help="要約の出力言語（YouTube用、default: ja）")
    args = parser.parse_args()

    # Get URLs
    urls = args.urls if args.urls else read_urls_from_stdin()

    if not urls:
        print("URLが指定されていません", file=sys.stderr)
        sys.exit(1)

    print(f"[{len(urls)}件処理します]", file=sys.stderr)

    for i, url in enumerate(urls):
        if i > 0:
            print("\n" + "=" * 60 + "\n")

        if is_youtube_url(url):
            print(f"  ({i+1}/{len(urls)}) [YouTube]", file=sys.stderr)
            process_youtube(url, raw=args.raw, detail=args.detail, lang=args.lang)
        else:
            tweet_id, username = extract_tweet_info(url)
            if not tweet_id:
                print(f"[スキップ] {url}")
                continue
            print(f"  ({i+1}/{len(urls)}) @{username or '?'}", file=sys.stderr)
            process_x(url, args)


if __name__ == "__main__":
    main()
