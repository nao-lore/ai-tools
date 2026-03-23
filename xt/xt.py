#!/usr/bin/env python3
"""Xの投稿をURL指定で取得するツール（テキスト＋画像自動DL＋記事全文）"""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error

IMG_BASE = "/tmp/xt"


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
        if "x.com/" in line or "twitter.com/" in line:
            urls.append(line)
    return urls


def main():
    parser = argparse.ArgumentParser(
        description="Xの投稿を取得（画像自動DL・記事全文対応）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "使用例:\n"
            "  xt URL                         # 1件取得\n"
            "  xt URL1 URL2 URL3              # 複数同時\n"
            "  xt                             # URLを貼り付けモード\n"
            "  pbpaste | xt                   # クリップボードから\n"
            "  xt URL --no-images             # 画像DLしない\n"
            "  xt URL --json                  # 生JSON出力\n"
        ),
    )
    parser.add_argument("urls", nargs="*", help="ツイートのURLまたはID（省略で貼り付けモード）")
    parser.add_argument("--no-images", action="store_true", help="画像をダウンロードしない")
    parser.add_argument("--save-dir", help=f"画像の保存先（デフォルト: {IMG_BASE}/ツイートID/）")
    parser.add_argument("--json", action="store_true", help="生JSON出力")
    args = parser.parse_args()

    # Get URLs
    urls = args.urls if args.urls else read_urls_from_stdin()

    if not urls:
        print("URLが指定されていません", file=sys.stderr)
        sys.exit(1)

    print(f"[{len(urls)}件取得します]", file=sys.stderr)

    for i, url in enumerate(urls):
        if i > 0:
            print("\n" + "=" * 60 + "\n")

        tweet_id, username = extract_tweet_info(url)
        if not tweet_id:
            print(f"[スキップ] {url}")
            continue

        print(f"  ({i+1}/{len(urls)}) @{username or '?'}", file=sys.stderr)
        tweet = fetch_tweet(tweet_id, username)

        if tweet is None:
            print(f"[スキップ] {url}")
            continue

        if args.json:
            print(json.dumps(tweet, indent=2, ensure_ascii=False))
            continue

        save_dir = None
        if not args.no_images:
            if args.save_dir:
                save_dir = os.path.join(args.save_dir, tweet_id)
            else:
                save_dir = os.path.join(IMG_BASE, tweet_id)
            os.makedirs(save_dir, exist_ok=True)

        print(format_tweet(tweet, save_dir))


if __name__ == "__main__":
    main()
